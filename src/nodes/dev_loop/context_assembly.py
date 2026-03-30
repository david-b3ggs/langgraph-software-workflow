import logging
from src.state.dev_loop_state import DevLoopState

logger = logging.getLogger(__name__)


async def context_assembly_node(state: DevLoopState) -> dict:
    """Load and compress MD files per task scope. Pin md_versions for this run."""
    logger.info("context_assembly: scope=%s", state["task"].get("scope"))
    # STUB — Phase 4 implements file loading, hashing, and compression
    compressed_md = {
        "PROJECT.md":     "(stub PROJECT.md content)",
        "CODE_STYLES.md": "(stub CODE_STYLES.md content)",
        "BRAND_STYLES.md":"(stub BRAND_STYLES.md content)",
        "TESTING.md":     "(stub TESTING.md content)",
    }
    md_versions = {k: "stub-hash" for k in compressed_md}
    return {"compressed_md": compressed_md, "md_versions": md_versions}
