import logging
from pathlib import Path
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_FILE_MAP = {
    "PROJECT.md":      "planner_md",
    "CODE_STYLES.md":  "backend_md",
    "BRAND_STYLES.md": "frontend_md",
    "TESTING.md":      "docs_agent_md",
}


async def write_md_files_to_repo_node(state: IngestionState) -> dict:
    """Write all four generated MD files into the repo."""
    repo = Path(state["repo_path"])
    for filename, state_key in _FILE_MAP.items():
        content = state.get(state_key, "")
        if content:
            (repo / filename).write_text(content, encoding="utf-8")
            logger.info("write_md_files: wrote %s", filename)
    return {"ingestion_complete": True}
