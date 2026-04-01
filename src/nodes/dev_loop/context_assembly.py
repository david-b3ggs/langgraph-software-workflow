import logging
from src.state.dev_loop_state import DevLoopState
from src.tools import file_tools
from src.config import settings

logger = logging.getLogger(__name__)


async def context_assembly_node(state: DevLoopState) -> dict:
    """Load and compress MD files per task scope. Pin md_versions for this run."""
    scope = state["task"].get("scope", "both")
    logger.info("context_assembly: scope=%s", scope)

    repo_path = state["task"].get("repo_path") or settings.repo_path
    content = file_tools.load_md_files(repo_path)
    versions = file_tools.hash_md_files(content)

    # Backend tasks don't need brand/UI context
    filtered = dict(content)
    if scope == "backend":
        filtered.pop("BRAND_STYLES.md", None)

    return {"compressed_md": filtered, "md_versions": versions}
