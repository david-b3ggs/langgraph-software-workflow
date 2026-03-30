import logging
from src.state.dev_loop_state import DevLoopState, WorkerOutput

logger = logging.getLogger(__name__)


async def worker_backend_node(state: DevLoopState) -> dict:
    """Backend worker: generates Go/API code for its assigned subtask.
    Receives current_task via Send payload."""
    task = state.get("current_task") or {}
    logger.info("worker_backend: task_id=%s", task.get("id"))
    # STUB — Phase 4 implements LLM call with CODE_STYLES context
    output: WorkerOutput = {
        "agent": "backend",
        "diff": "--- a/main.go\n+++ b/main.go\n@@ stub backend diff @@",
        "modified_files": ["main.go"],
        "rationale": "Stub backend implementation.",
        "passed_review": False,
    }
    return {"worker_outputs": {"backend": output}}
