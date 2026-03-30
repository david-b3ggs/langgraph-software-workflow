import logging
from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)


async def fetch_docs_node(state: IngestionState) -> dict:
    """Conditionally fetch external docs for unrecognised dependencies."""
    logger.info("fetch_docs: needs_fetch=%s", state["repo_structure"].get("needs_doc_fetch"))
    # STUB — Phase 3 implements httpx fetching
    return {"fetched_docs": {}}
