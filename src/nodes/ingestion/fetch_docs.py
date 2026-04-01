import json
import logging
import re
from pathlib import Path

from src.state.ingestion_state import IngestionState
from src.tools.documentation_tools import fetch_docs_for_packages

logger = logging.getLogger(__name__)


async def fetch_docs_node(state: IngestionState) -> dict:
    """Fetch Context7 library docs for detected dependencies when needed."""
    if not state["repo_structure"].get("needs_doc_fetch"):
        logger.info("fetch_docs: skipping (needs_doc_fetch=False)")
        return {"fetched_docs": {}}

    repo_root = Path(state["repo_path"])
    packages: list[str] = []

    # JS: package.json
    pkg_json = repo_root / "package.json"
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text())
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        packages.extend(deps.keys())

    # Python: requirements.txt (strip version specifiers)
    req_txt = repo_root / "requirements.txt"
    if req_txt.exists():
        for line in req_txt.read_text().splitlines():
            name = re.split(r"[>=<!;\s]", line.strip())[0].lower()
            if name and not name.startswith("#"):
                packages.append(name)

    # Go: go.mod (extract module paths, use last path segment as key)
    go_mod = repo_root / "go.mod"
    if go_mod.exists():
        for line in go_mod.read_text().splitlines():
            m = re.match(r"\s+?([\w./\-]+)\s+v", line)
            if m:
                packages.append(m.group(1).split("/")[-1])

    fetched = await fetch_docs_for_packages(packages)
    logger.info("fetch_docs: fetched docs for %d libraries", len(fetched))
    return {"fetched_docs": fetched}
