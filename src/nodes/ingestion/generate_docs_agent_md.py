import logging
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)


async def generate_docs_agent_md_node(state: IngestionState) -> dict:
    """Generate TESTING.md from planner MD + structure analysis."""
    logger.info("generate_docs_agent_md")
    # STUB — Phase 3 implements LLM call
    docs_agent_md = "# TESTING.md (stub)\n\nTest runner commands will be generated here.\n"
    return {"docs_agent_md": docs_agent_md}
