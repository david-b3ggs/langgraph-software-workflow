import logging
from src.state.dev_loop_state import DevLoopState, WorkerOutput

logger = logging.getLogger(__name__)


async def worker_frontend_node(state: DevLoopState) -> dict:
    """Frontend worker: generates React/UI code for its assigned subtask.
    Receives current_task via Send payload."""
    task = state.get("current_task") or {}
    logger.info("worker_frontend: task_id=%s", task.get("id"))
    # STUB — Phase 4 implements LLM call with BRAND_STYLES + CODE_STYLES context
    output: WorkerOutput = {
        "agent": "frontend",
        "diff": "--- a/App.tsx\n+++ b/App.tsx\n@@ stub frontend diff @@",
        "modified_files": ["App.tsx"],
        "rationale": "Stub frontend implementation.",
        "passed_review": False,
    }
    return {"worker_outputs": {"frontend": output}}
