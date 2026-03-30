import logging
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)


async def generate_planner_md_node(state: IngestionState) -> dict:
    """Generate PROJECT.md — the planner agent's primary context."""
    logger.info("generate_planner_md")
    # STUB — Phase 3 implements LLM call
    planner_md = (
        "# PROJECT.md (stub)\n\n"
        "Project purpose, architecture, and frameworks will be generated here.\n"
    )
    return {"planner_md": planner_md}
