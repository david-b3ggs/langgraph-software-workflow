"""File I/O tools for reading, hashing, and writing the 4 MD context files."""
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MD_FILES = {
    "PROJECT.md":     "project",
    "CODE_STYLES.md": "code_styles",
    "BRAND_STYLES.md":"brand_styles",
    "TESTING.md":     "testing",
}


def load_md_files(repo_path: str) -> dict[str, str]:
    """Load all 4 context MD files from the repo root.

    Returns a dict keyed by filename. Missing files return an empty string
    (not an error — the ingestion pipeline may not have run yet).
    """
    root = Path(repo_path)
    result: dict[str, str] = {}
    for filename in MD_FILES:
        p = root / filename
        if p.exists():
            result[filename] = p.read_text(encoding="utf-8")
            logger.debug("load_md_files: loaded %s (%d chars)", filename, len(result[filename]))
        else:
            result[filename] = ""
            logger.debug("load_md_files: %s not found, using empty string", filename)
    return result


def hash_content(content: str) -> str:
    """Return a SHA-256 hex digest of the given string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_md_files(md_map: dict[str, str]) -> dict[str, str]:
    """Return a dict of filename → SHA-256 hash for version pinning."""
    return {filename: hash_content(content) for filename, content in md_map.items()}


def write_md_files(repo_path: str, files: dict[str, str]) -> None:
    """Write a dict of filename → content to the repo root.

    Creates the file if it doesn't exist. Only writes keys that are present
    in the input dict — does not touch other files.
    """
    root = Path(repo_path)
    for filename, content in files.items():
        if not content:
            continue
        dest = root / filename
        dest.write_text(content, encoding="utf-8")
        logger.info("write_md_files: wrote %s (%d chars)", filename, len(content))


def md_files_are_current(repo_path: str, pinned_versions: dict[str, str]) -> bool:
    """Check if the on-disk MD files match the pinned version hashes.

    Used by the ingestion pipeline to decide whether to skip a re-run.
    Returns True only if all 4 files exist and all hashes match.
    """
    current = load_md_files(repo_path)
    current_hashes = hash_md_files(current)
    for filename, pinned_hash in pinned_versions.items():
        if current_hashes.get(filename) != pinned_hash:
            return False
    return True
