import json
import logging
from langchain_core.messages import HumanMessage
from src.llm.client import get_llm
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a technical writer generating BRAND_STYLES.md for a software project.
This file is read by an AI frontend/docs agent before it writes UI or documentation.

## Project summary (PROJECT.md)
{planner_md}

## Repo structure analysis
{structure}

## Existing markdown files found in the repo
{existing_md}

## Fetched library documentation
{fetched_docs}

Write BRAND_STYLES.md covering:
1. **UI Framework & Component Library** — what is in use (infer from package.json, imports, or existing docs)
2. **Styling Approach** — CSS methodology, design tokens, theming (Tailwind, CSS Modules, styled-components, etc.)
3. **Tone & Voice** — how the product communicates with users (infer from existing docs/copy)
4. **Typography & Colour** — any conventions visible in existing docs or config
5. **Component Conventions** — file structure, naming, props patterns
6. **Accessibility** — any a11y standards or practices mentioned

If the project has no frontend (pure backend/CLI), state that clearly and focus on documentation style instead.
Be concise and factual. Output only the markdown content — no preamble.
"""


async def generate_frontend_md_node(state: IngestionState) -> dict:
    """Generate BRAND_STYLES.md from planner MD + structure analysis."""
    logger.info("generate_frontend_md")

    structure = json.dumps(state.get("repo_structure", {}), indent=2)
    existing_md_parts = []
    for filename, content in (state.get("existing_md") or {}).items():
        snippet = content[:1500]
        existing_md_parts.append(f"### {filename}\n{snippet}")
    existing_md = "\n\n".join(existing_md_parts) or "(none found)"

    fetched_docs_parts = []
    for pkg_name, doc_content in (state.get("fetched_docs") or {}).items():
        fetched_docs_parts.append(f"### {pkg_name}\n{doc_content[:3000]}")
    fetched_docs_section = "\n\n".join(fetched_docs_parts) or "(none fetched)"

    prompt = _PROMPT.format(
        planner_md=state.get("planner_md", "(not yet generated)"),
        structure=structure,
        existing_md=existing_md,
        fetched_docs=fetched_docs_section,
    )
    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    frontend_md = response.content.strip()

    logger.info("generate_frontend_md: generated %d chars", len(frontend_md))
    return {"frontend_md": frontend_md}
