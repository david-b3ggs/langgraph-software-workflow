"""Track B: detect repo structure, languages, frameworks, and test patterns."""
import logging
import re
from pathlib import Path

from src.state.ingestion_state import IngestionState

logger = logging.getLogger(__name__)

_SKIP_DIRS = {"node_modules", "vendor", "__pycache__", ".venv", "venv", ".git"}

# Framework / language detection rules: (filename_or_glob, language, framework)
_DETECTION_RULES: list[tuple[str, str, str]] = [
    ("go.mod",            "go",         "go-modules"),
    ("go.sum",            "go",         "go-modules"),
    ("package.json",      "typescript", "node"),
    ("tsconfig.json",     "typescript", "typescript"),
    ("next.config.*",     "typescript", "next.js"),
    ("vite.config.*",     "typescript", "vite"),
    ("requirements.txt",  "python",     "pip"),
    ("pyproject.toml",    "python",     "pyproject"),
    ("setup.py",          "python",     "setuptools"),
    ("Cargo.toml",        "rust",       "cargo"),
    ("pom.xml",           "java",       "maven"),
    ("build.gradle",      "java",       "gradle"),
    ("Gemfile",           "ruby",       "bundler"),
    ("mix.exs",           "elixir",     "mix"),
]

# Test directory / file patterns
_TEST_PATTERNS = [
    "**/*_test.go",
    "**/test_*.py",
    "**/*.test.ts",
    "**/*.test.js",
    "**/*.spec.ts",
    "**/*.spec.js",
    "**/tests/**",
    "**/test/**",
    "**/__tests__/**",
]

# DB/schema file patterns
_SCHEMA_PATTERNS = [
    "**/migrations/**",
    "**/schema.sql",
    "**/schema.go",
    "**/*.prisma",
    "**/models.py",
]


async def analyze_codebase_structure_node(state: IngestionState) -> dict:
    """Detect languages, frameworks, DB schema files, and test structure.

    Returns:
        repo_structure: dict with keys:
            languages       list[str]  detected programming languages
            frameworks      list[str]  detected frameworks/toolchains
            has_tests       bool       whether test files were found
            test_files      list[str]  sample test file paths (up to 10)
            schema_files    list[str]  DB/ORM schema file paths
            dir_layout      list[str]  top-level directory names
            needs_doc_fetch bool       True if version-specific deps were found
    """
    root = Path(state["repo_path"]).resolve()
    logger.info("analyze_structure: scanning %s", root)

    languages: set[str] = set()
    frameworks: set[str] = set()

    # --- Framework / language detection ---
    for rule_file, lang, framework in _DETECTION_RULES:
        if "*" in rule_file:
            matches = list(root.glob(rule_file))
        else:
            matches = [root / rule_file]

        for match in matches:
            if match.exists() and _not_in_skip_dir(match, root):
                languages.add(lang)
                frameworks.add(framework)
                logger.debug("analyze_structure: detected %s / %s via %s", lang, framework, match.name)

    # --- Infer languages from file extensions if not already detected ---
    ext_lang_map = {
        ".go": "go", ".py": "python", ".ts": "typescript",
        ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
        ".rs": "rust", ".java": "java", ".rb": "ruby",
    }
    for file_path in _walk_source_files(root):
        lang = ext_lang_map.get(file_path.suffix)
        if lang:
            languages.add(lang)

    # --- Test files ---
    test_files: list[str] = []
    for pattern in _TEST_PATTERNS:
        for p in root.glob(pattern):
            if p.is_file() and _not_in_skip_dir(p, root):
                test_files.append(str(p.relative_to(root)))
                if len(test_files) >= 10:
                    break
        if len(test_files) >= 10:
            break

    # --- Schema / migration files ---
    schema_files: list[str] = []
    for pattern in _SCHEMA_PATTERNS:
        for p in root.glob(pattern):
            if p.is_file() and _not_in_skip_dir(p, root):
                schema_files.append(str(p.relative_to(root)))

    # --- Top-level directory layout ---
    dir_layout = sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in _SKIP_DIRS
    )

    # --- needs_doc_fetch heuristic ---
    # Flag if we found version-pinned deps in package.json or go.mod
    needs_doc_fetch = _check_needs_doc_fetch(root, frameworks)

    structure = {
        "languages":      sorted(languages),
        "frameworks":     sorted(frameworks),
        "has_tests":      bool(test_files),
        "test_files":     test_files,
        "schema_files":   schema_files,
        "dir_layout":     dir_layout,
        "needs_doc_fetch": needs_doc_fetch,
    }
    logger.info(
        "analyze_structure: languages=%s frameworks=%s has_tests=%s",
        structure["languages"], structure["frameworks"], structure["has_tests"],
    )
    return {"repo_structure": structure}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _not_in_skip_dir(file_path: Path, root: Path) -> bool:
    parts = file_path.relative_to(root).parts
    return not any(p.startswith(".") or p in _SKIP_DIRS for p in parts)


def _walk_source_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and _not_in_skip_dir(p, root):
            yield p


def _check_needs_doc_fetch(root: Path, frameworks: set[str]) -> bool:
    """Heuristic: flag True if the project uses version-specific dependencies
    that might need external doc fetching (e.g. a specific ORM or router version).
    Currently checks package.json for known framework deps.
    """
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            import json
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            # Flag if using specific versions of known doc-heavy frameworks
            flagged = {"next", "react", "vue", "svelte", "prisma", "drizzle-orm"}
            if any(k in deps for k in flagged):
                return True
        except Exception:
            pass
    return False
