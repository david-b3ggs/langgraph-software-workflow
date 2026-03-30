"""Track A: scan the repo for existing README and markdown files."""
import logging
from pathlib import Path

from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_MD_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
_SKIP_DIRS = {"node_modules", "vendor", "__pycache__", ".venv", "venv", ".git"}

# Known context file names we should capture explicitly
_CONTEXT_FILES = {"PROJECT.md", "CODE_STYLES.md", "BRAND_STYLES.md", "TESTING.md"}


async def analyze_existing_markdown_node(state: IngestionState) -> dict:
    """Walk the repo and collect all markdown/text files.

    Returns:
        existing_md: dict[filename → content] for all found MD files.
    """
    root = Path(state["repo_path"]).resolve()
    logger.info("analyze_markdown: scanning %s", root)

    found: dict[str, str] = {}

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in _MD_EXTENSIONS:
            continue

        # Skip hidden dirs and irrelevant directories
        parts = file_path.relative_to(root).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts):
            continue

        rel = str(file_path.relative_to(root))
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            found[rel] = content
            logger.debug("analyze_markdown: found %s (%d chars)", rel, len(content))
        except OSError as exc:
            logger.warning("analyze_markdown: could not read %s — %s", rel, exc)

    logger.info("analyze_markdown: found %d markdown files", len(found))
    return {"existing_md": found}
