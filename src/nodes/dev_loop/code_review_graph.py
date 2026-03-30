"""Build a call/import dependency subgraph from worker diffs.

No LLM — pure graph traversal. Extracts changed files from worker diffs,
expands to their 1-hop import neighbourhood, and stores the result as
review_subgraph. The review gate uses this list instead of the full codebase
to keep the review prompt token-efficient.
"""
import logging

from src.state.dev_loop_state import DevLoopState
from src.tools.git_tools import get_changed_files_from_diffs
from src.tools.graph_tools import build_repo_call_graph, get_impacted_subgraph
from src.config import settings

logger = logging.getLogger(__name__)


async def build_review_subgraph_node(state: DevLoopState) -> dict:
    """Extract changed files from diffs and expand to the impacted subgraph.

    Steps:
      1. Collect all diffs from worker_outputs.
      2. Parse changed file paths from the diffs.
      3. Build the repo's import/call graph via graph_tools.
      4. Expand changed files to their 1-hop neighbourhood.
      5. Store result in review_subgraph.
    """
    outputs = state.get("worker_outputs") or {}
    logger.info("code_review_graph: processing %d worker outputs", len(outputs))

    # 1. Collect diffs
    diffs = [o["diff"] for o in outputs.values() if o.get("diff")]

    # 2. Parse changed files
    changed_files = get_changed_files_from_diffs(diffs)
    logger.info("code_review_graph: %d changed files from diffs", len(changed_files))

    if not changed_files:
        logger.warning("code_review_graph: no changed files found in diffs")
        return {"review_subgraph": []}

    # 3. Build import graph for the target repo
    repo_path = state.get("task", {}).get("repo_path", settings.repo_path)
    try:
        repo_graph = build_repo_call_graph(repo_path)
    except Exception as exc:
        logger.warning("code_review_graph: graph build failed (%s) — using changed files only", exc)
        return {"review_subgraph": changed_files}

    # 4. Expand to 1-hop neighbourhood
    impacted = get_impacted_subgraph(repo_graph, changed_files, depth=1)

    logger.info(
        "code_review_graph: %d changed → %d impacted files (graph had %d nodes)",
        len(changed_files), len(impacted), repo_graph.number_of_nodes(),
    )
    return {"review_subgraph": impacted}
