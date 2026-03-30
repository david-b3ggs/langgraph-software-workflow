import logging
from langgraph.types import interrupt
from src.state.dev_loop_state import DevLoopState

logger = logging.getLogger(__name__)


def human_gate_node(state: DevLoopState) -> dict:
    """Pause execution and surface the plan to the engineer for approval.

    Uses interrupt() — the production HITL mechanism. Graph resumes when the
    caller invokes graph.invoke(Command(resume=True/False), config=...).
    """
    logger.info("human_gate: surfacing plan with %d subtasks", len(state["plan"] or []))

    approved = interrupt({
        "plan": state["plan"],
        "task": state["task"],
        "message": "Review the plan above. Approve to begin parallel execution.",
    })

    logger.info("human_gate: approved=%s", approved)
    return {"human_approved": bool(approved)}
