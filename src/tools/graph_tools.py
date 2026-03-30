"""Repo call/import graph builder for token-efficient code review.

Builds a directed graph of file → imported_file edges by parsing import
statements. Language detection is by file extension. Degrades gracefully
for unsupported languages — only the directly changed files are returned.

Supported languages:
  .py  — AST-based import parsing
  .go  — regex on `import` blocks and single-line imports
  .ts / .tsx / .js / .jsx — regex on ES6 import / require
"""
import ast
import logging
import re
from pathlib import Path

import networkx as nx

logger = logging.getLogger(__name__)

# File extensions to include when walking the repo
_SUPPORTED_EXTENSIONS = {".py", ".go", ".ts", ".tsx", ".js", ".jsx"}

# Max files to walk (safety limit for very large repos)
_MAX_FILES = 5_000


# ---------------------------------------------------------------------------
# Language-specific import extractors
# ---------------------------------------------------------------------------

def _imports_python(source: str, file_path: Path) -> list[str]:
    """Extract imported module paths from a Python source file using the AST."""
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.replace(".", "/") + ".py")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.replace(".", "/") + ".py")
    return imports


_GO_IMPORT_RE = re.compile(r'"([^"]+)"')

def _imports_go(source: str, file_path: Path) -> list[str]:
    """Extract imported package paths from a Go source file using regex."""
    # Match both `import "pkg"` and `import ( "pkg1" \n "pkg2" )`
    in_block = False
    imports: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped == "import (":
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        if in_block or stripped.startswith("import "):
            for m in _GO_IMPORT_RE.finditer(line):
                pkg = m.group(1)
                # Skip stdlib and third-party (no slash prefix heuristic)
                if "/" in pkg:
                    imports.append(pkg)
    return imports


_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)

def _imports_js(source: str, file_path: Path) -> list[str]:
    """Extract imported module specifiers from JS/TS using regex."""
    imports: list[str] = []
    for m in _JS_IMPORT_RE.finditer(source):
        specifier = m.group(1) or m.group(2)
        # Only include relative imports (starts with . or ..)
        if specifier and specifier.startswith("."):
            imports.append(specifier)
    return imports


_EXTRACTORS = {
    ".py":  _imports_python,
    ".go":  _imports_go,
    ".ts":  _imports_js,
    ".tsx": _imports_js,
    ".js":  _imports_js,
    ".jsx": _imports_js,
}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_repo_call_graph(repo_path: str) -> nx.DiGraph:
    """Walk the repo and build a directed import graph (file → imported_file).

    Nodes are relative file paths from the repo root.
    Edges point from importer to importee.
    Files that can't be parsed are skipped silently.
    """
    root = Path(repo_path).resolve()
    graph = nx.DiGraph()
    count = 0

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in _SUPPORTED_EXTENSIONS:
            continue
        # Skip hidden dirs and common non-source dirs
        parts = file_path.relative_to(root).parts
        if any(p.startswith(".") or p in {"node_modules", "vendor", "__pycache__", ".venv", "venv"} for p in parts):
            continue
        if count >= _MAX_FILES:
            logger.warning("build_repo_call_graph: hit _MAX_FILES limit (%d)", _MAX_FILES)
            break

        rel = str(file_path.relative_to(root))
        graph.add_node(rel)
        count += 1

        extractor = _EXTRACTORS.get(file_path.suffix)
        if extractor is None:
            continue

        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for imported in extractor(source, file_path):
            # Add edge even if importee isn't in the graph yet
            graph.add_edge(rel, imported)

    logger.info("build_repo_call_graph: %d nodes, %d edges", graph.number_of_nodes(), graph.number_of_edges())
    return graph


def get_impacted_subgraph(
    graph: nx.DiGraph,
    changed_files: list[str],
    depth: int = 1,
) -> list[str]:
    """Return the set of files impacted by changes — changed files + their
    direct callers and callees up to `depth` hops.

    Falls back to returning only the changed files if the graph is empty
    or none of the changed files are in the graph.
    """
    if not graph or not changed_files:
        return changed_files

    impacted: set[str] = set(changed_files)

    for changed in changed_files:
        if changed not in graph:
            continue
        # Successors (files this one imports) and predecessors (files that import this one)
        try:
            ego = nx.ego_graph(graph, changed, radius=depth, undirected=True)
            impacted.update(ego.nodes())
        except Exception as exc:
            logger.debug("get_impacted_subgraph: ego_graph failed for %s — %s", changed, exc)

    result = sorted(impacted)
    logger.info(
        "get_impacted_subgraph: %d changed → %d impacted files",
        len(changed_files), len(result),
    )
    return result
