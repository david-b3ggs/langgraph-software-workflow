import logging
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)


async def generate_frontend_md_node(state: IngestionState) -> dict:
    """Generate BRAND_STYLES.md from planner MD + structure analysis."""
    logger.info("generate_frontend_md")
    # STUB — Phase 3 implements LLM call
    frontend_md = "# BRAND_STYLES.md (stub)\n\nUI styling guidelines will be generated here.\n"
    return {"frontend_md": frontend_md}
