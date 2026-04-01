import asyncio
import json
import logging
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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

_SERVER_PARAMS = StdioServerParameters(
    command="npx",
    args=["-y", "@upstash/context7-mcp@latest"],
)


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


async def fetch_docs_for_packages(packages: list[str]) -> dict[str, str]:
    """Fetch Context7 docs for a list of package names via stdio MCP.

    Spawns `npx @upstash/context7-mcp` as a subprocess — no running server needed.
    Returns {pkg_name: doc_content}. Returns {} on any connection failure.
    """
    filtered = [p for p in packages if p in PACKAGE_TO_LIBRARY_NAME]
    if not filtered:
        logger.info("fetch_docs: no known packages to fetch docs for")
        return {}

    try:
        async with stdio_client(_SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                tool_names = {t.name for t in tools_result.tools}
                for required in (_RESOLVE_TOOL, _DOCS_TOOL):
                    if required not in tool_names:
                        raise RuntimeError(f"Context7 MCP missing tool: {required!r}")

                async def _fetch_one(pkg: str) -> tuple[str, str]:
                    library_name = PACKAGE_TO_LIBRARY_NAME[pkg]

                    resolve_result = await session.call_tool(
                        _RESOLVE_TOOL,
                        {"libraryName": library_name, "query": "API reference and usage guide"},
                    )
                    resolve_text = resolve_result.content[0].text if resolve_result.content else ""
                    library_id = _parse_library_id(resolve_text)
                    if not library_id:
                        logger.warning("fetch_docs: could not resolve library ID for %r", library_name)
                        return pkg, ""

                    docs_result = await session.call_tool(
                        _DOCS_TOOL,
                        {"libraryId": library_id, "query": "API reference, configuration, and usage guide"},
                    )
                    doc_text = docs_result.content[0].text if docs_result.content else ""
                    return pkg, doc_text

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
        logger.warning("fetch_docs: Context7 unavailable (%s) — skipping doc fetch", exc)
        return {}
