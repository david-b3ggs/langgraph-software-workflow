import json
import logging
from langchain_core.messages import HumanMessage
from src.llm.client import get_llm
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a technical writer generating TESTING.md for a software project.
This file is read by an AI test agent before it writes, runs, or evaluates tests.

## Project summary (PROJECT.md)
{planner_md}

## Repo structure analysis
{structure}

## Existing markdown files found in the repo
{existing_md}

## Fetched library documentation
{fetched_docs}

Write TESTING.md covering:
1. **Test Runner** — exact command(s) to run the full test suite (e.g. `pytest`, `go test ./...`, `npm test`)
2. **Test Layout** — where tests live relative to source (co-located, `tests/`, etc.)
3. **Test Types** — unit, integration, e2e — which exist and how they are distinguished
4. **Coverage** — how to generate a coverage report if applicable
5. **Fixtures & Helpers** — any shared test utilities or fixtures worth knowing about
6. **CI Integration** — how tests are run in CI if evident from repo structure

Be precise with commands — the test agent will run them verbatim.
Output only the markdown content — no preamble.
"""


async def generate_docs_agent_md_node(state: IngestionState) -> dict:
    """Generate TESTING.md from planner MD + structure analysis."""
    logger.info("generate_docs_agent_md")

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
    docs_agent_md = response.content.strip()

    logger.info("generate_docs_agent_md: generated %d chars", len(docs_agent_md))
    return {"docs_agent_md": docs_agent_md}
