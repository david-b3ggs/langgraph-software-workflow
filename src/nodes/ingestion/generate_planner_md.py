import json
import logging
from langchain_core.messages import HumanMessage
from src.llm.client import get_llm
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a technical writer generating PROJECT.md for a software project.
This file is read by an AI planning agent before it breaks down development tasks.

## Repo structure analysis
{structure}

## Existing markdown files found in the repo
{existing_md}

Write a clear, factual PROJECT.md covering:
1. **Purpose** — what this project does in 2-3 sentences
2. **Architecture** — high-level component breakdown (dirs, layers, data flow)
3. **Languages & Frameworks** — detected stack with roles
4. **Key Conventions** — anything evident from the existing docs or structure (naming, module layout, async patterns, etc.)
5. **Entry Points** — how the system is started/invoked

Be concise and factual. Do not invent details not supported by the evidence.
Output only the markdown content — no preamble.
"""


async def generate_planner_md_node(state: IngestionState) -> dict:
    """Generate PROJECT.md — the planner agent's primary context."""
    logger.info("generate_planner_md")

    structure = json.dumps(state.get("repo_structure", {}), indent=2)
    existing_md_parts = []
    for filename, content in (state.get("existing_md") or {}).items():
        snippet = content[:2000]
        existing_md_parts.append(f"### {filename}\n{snippet}")
    existing_md = "\n\n".join(existing_md_parts) or "(none found)"

    prompt = _PROMPT.format(structure=structure, existing_md=existing_md)
    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    planner_md = response.content.strip()

    logger.info("generate_planner_md: generated %d chars", len(planner_md))
    return {"planner_md": planner_md}
