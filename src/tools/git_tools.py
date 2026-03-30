"""Git operation tools: diff parsing, changed file extraction, commit."""
import logging
import subprocess
from pathlib import Path

from unidiff import PatchSet

logger = logging.getLogger(__name__)


def get_git_diff(repo_path: str, base: str = "HEAD") -> str:
    """Return the unified diff between the working tree and base ref.

    Uses `git diff <base>` so it includes staged + unstaged changes relative
    to the given base. Pass base="" for `git diff` (unstaged only).
    """
    cmd = ["git", "diff", base] if base else ["git", "diff"]
    result = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("git_diff: non-zero exit: %s", result.stderr.strip())
    return result.stdout


def extract_changed_files(diff_text: str) -> list[str]:
    """Parse a unified diff and return the list of modified file paths.

    Uses the unidiff library to parse headers reliably. Falls back to an
    empty list if the diff is empty or malformed.
    """
    if not diff_text.strip():
        return []
    try:
        patch = PatchSet(diff_text)
        files = []
        for patched_file in patch:
            # Use the target path (b/...) — that's the file after the change
            path = patched_file.path
            if path and path != "/dev/null":
                files.append(path)
        return files
    except Exception as exc:
        logger.warning("extract_changed_files: parse error — %s", exc)
        return []


def get_changed_files_from_diffs(diffs: list[str]) -> list[str]:
    """Aggregate changed files from multiple worker diffs. Deduplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for diff in diffs:
        for path in extract_changed_files(diff):
            if path not in seen:
                seen.add(path)
                result.append(path)
    return result


def commit_changes(repo_path: str, message: str, add_all: bool = False) -> bool:
    """Stage and commit changes in the repo.

    Args:
        repo_path: Absolute path to the git repository.
        message:   Commit message.
        add_all:   If True, run `git add -A` before committing.

    Returns True on success, False on failure.
    """
    cwd = repo_path
    if add_all:
        subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("commit_changes: git commit failed — %s", result.stderr.strip())
        return False
    logger.info("commit_changes: committed — %s", message)
    return True


def is_git_repo(path: str) -> bool:
    """Return True if path is inside a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_repo_root(path: str) -> str | None:
    """Return the absolute path to the git repo root, or None if not a repo."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()
