import logging
from src.state.dev_loop_state import DevLoopState, WorkerOutput

logger = logging.getLogger(__name__)


async def worker_docs_node(state: DevLoopState) -> dict:
    """Docs worker: updates READMEs and TESTING.md for its assigned subtask.
    Receives current_task via Send payload."""
    task = state.get("current_task") or {}
    logger.info("worker_docs: task_id=%s", task.get("id"))
    # STUB — Phase 4 implements LLM call with TESTING.md context
    output: WorkerOutput = {
        "agent": "docs",
        "diff": "--- a/README.md\n+++ b/README.md\n@@ stub docs diff @@",
        "modified_files": ["README.md"],
        "rationale": "Stub docs update.",
        "passed_review": False,
    }
    return {"worker_outputs": {"docs": output}}
