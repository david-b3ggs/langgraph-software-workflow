import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)

PACKAGE_TO_LIBRARY_NAME: dict[str, str] = {
    # JavaScript / TypeScript — frontend
    "next":           "Next.js",
    "react":          "React",
    "vue":            "Vue.js",
    "svelte":         "Svelte",
    # JavaScript / TypeScript — backend
    "express":        "Express.js",
    "fastify":        "Fastify",
    "hono":           "Hono",
    "nestjs":         "NestJS",
    "@nestjs/core":   "NestJS",
    "trpc":           "tRPC",
    "@trpc/server":   "tRPC",
    "elysia":         "Elysia",
    # ORM / DB (JS)
    "prisma":         "Prisma",
    "drizzle-orm":    "Drizzle ORM",
    "typeorm":        "TypeORM",
    "sequelize":      "Sequelize",
    # Python — web frameworks
    "fastapi":        "FastAPI",
    "flask":          "Flask",
    "django":         "Django",
    "starlette":      "Starlette",
    "litestar":       "Litestar",
    # Python — AI / ML
    "langgraph":      "LangGraph",
    "langchain":      "LangChain Python",
    "langchain-core": "LangChain Python",
    "openai":         "OpenAI Python SDK",
    "anthropic":      "Anthropic Python SDK",
    "pydantic":       "Pydantic",
    # Python — DB / ORM
    "sqlalchemy":     "SQLAlchemy",
    "alembic":        "Alembic",
    "tortoise-orm":   "Tortoise ORM",
    # Go — web frameworks
    "gin":            "Gin",
    "echo":           "Echo",
    "fiber":          "Fiber",
    "chi":            "Chi",
}

_RESOLVE_TOOL = "resolve-library-id"
_DOCS_TOOL    = "query-docs"


def _parse_library_id(text: str) -> str | None:
    """Extract a Context7 library ID from a resolve-library-id response."""
    try:
        data = json.loads(text)
        results = data if isinstance(data, list) else data.get("result", [])
        if results:
            first = results[0]
            return first.get("id") or first.get("context7CompatibleLibraryID")
    except (json.JSONDecodeError, TypeError, KeyError, IndexError):
        pass
    m = re.search(r"(/[\w/.\-]+)", text)
    if m:
        return m.group(1)
    return None


async def _resolve_library_id(tool, library_name: str) -> str | None:
    result = await tool.ainvoke({"libraryName": library_name, "query": "API reference and usage guide"})
    text = result if isinstance(result, str) else getattr(result, "content", str(result))
    library_id = _parse_library_id(text)
    if not library_id:
        logger.warning("fetch_docs: could not resolve library ID for %r", library_name)
    return library_id


async def _query_docs(tool, library_id: str, query: str) -> str:
    result = await tool.ainvoke({"libraryId": library_id, "query": query})
    return result if isinstance(result, str) else getattr(result, "content", str(result))


async def fetch_docs_for_packages(
    packages: list[str],
    mcp_url: str,
    transport: str = "sse",
) -> dict[str, str]:
    """Fetch Context7 docs for a list of package names. Returns {pkg_name: doc_content}."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    filtered = [p for p in packages if p in PACKAGE_TO_LIBRARY_NAME]
    if not filtered:
        logger.info("fetch_docs: no known packages to fetch docs for")
        return {}

    try:
        async with MultiServerMCPClient({"context7": {"url": mcp_url, "transport": transport}}) as client:
            tools = {t.name: t for t in client.get_tools()}
            for required in (_RESOLVE_TOOL, _DOCS_TOOL):
                if required not in tools:
                    raise RuntimeError(f"Context7 MCP missing tool: {required!r}")

            resolve_tool = tools[_RESOLVE_TOOL]
            docs_tool = tools[_DOCS_TOOL]

            async def _fetch_one(pkg: str) -> tuple[str, str]:
                library_name = PACKAGE_TO_LIBRARY_NAME[pkg]
                library_id = await _resolve_library_id(resolve_tool, library_name)
                if not library_id:
                    return pkg, ""
                content = await _query_docs(docs_tool, library_id, "API reference, configuration, and usage guide")
                return pkg, content

            results = await asyncio.gather(*[_fetch_one(pkg) for pkg in filtered], return_exceptions=True)

        output: dict[str, str] = {}
        for item in results:
            if isinstance(item, Exception):
                logger.warning("fetch_docs: error fetching a library: %s", item)
            else:
                pkg, content = item
                if content:
                    output[pkg] = content
        return output

    except Exception as exc:
        logger.warning("fetch_docs: MCP server unreachable or failed (%s) — skipping doc fetch", exc)
        return {}
