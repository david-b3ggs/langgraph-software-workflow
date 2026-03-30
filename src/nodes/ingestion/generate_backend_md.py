import json
import logging
from langchain_core.messages import HumanMessage
from src.llm.client import get_llm
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a technical writer generating CODE_STYLES.md for a software project.
This file is read by an AI backend/code agent before it writes or edits code.

## Project summary (PROJECT.md)
{planner_md}

## Repo structure analysis
{structure}

## Existing markdown files found in the repo
{existing_md}

Write CODE_STYLES.md covering:
1. **File & Module Layout** — how files are organised, where new modules belong
2. **Naming Conventions** — variables, functions, classes, files (infer from structure and existing docs)
3. **Async Patterns** — sync vs async usage, event loop assumptions
4. **Error Handling** — approach to exceptions, logging, and propagation
5. **Imports & Dependencies** — how imports are structured, where to add new deps
6. **Testing Approach** — where tests live, how they are run (infer from test files and structure)

Be concise and factual. Do not invent details not supported by the evidence.
Output only the markdown content — no preamble.
"""


async def generate_backend_md_node(state: IngestionState) -> dict:
    """Generate CODE_STYLES.md from planner MD + structure analysis."""
    logger.info("generate_backend_md")

    structure = json.dumps(state.get("repo_structure", {}), indent=2)
    existing_md_parts = []
    for filename, content in (state.get("existing_md") or {}).items():
        snippet = content[:1500]
        existing_md_parts.append(f"### {filename}\n{snippet}")
    existing_md = "\n\n".join(existing_md_parts) or "(none found)"

    prompt = _PROMPT.format(
        planner_md=state.get("planner_md", "(not yet generated)"),
        structure=structure,
        existing_md=existing_md,
    )
    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    backend_md = response.content.strip()

    logger.info("generate_backend_md: generated %d chars", len(backend_md))
    return {"backend_md": backend_md}
