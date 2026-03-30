import logging
from src.state.dev_loop_state import DevLoopState, SubTask

logger = logging.getLogger(__name__)


async def planner_node(state: DevLoopState) -> dict:
    """Generate a structured dependency graph of subtasks. LLM with structured output.
    Retries up to 2x on ValidationError before returning plan=None (halts graph)."""
    logger.info("planner: task=%s", state["task"].get("title"))
    # STUB — Phase 4 implements LLM call with .with_structured_output(list[SubTask])
    scope = state["task"].get("scope", "both")
    plan: list[SubTask] = []

    if scope in ("backend", "both", "infra"):
        plan.append({
            "id": "be-1",
            "type": "backend",
            "depends_on": [],
            "context_hint": "Implement backend changes for the task.",
            "migration_scope": None,
        })
    if scope in ("frontend", "both"):
        plan.append({
            "id": "fe-1",
            "type": "frontend",
            "depends_on": ["be-1"] if scope == "both" else [],
            "context_hint": "Implement frontend changes for the task.",
            "migration_scope": None,
        })
    plan.append({
        "id": "docs-1",
        "type": "docs",
        "depends_on": [t["id"] for t in plan],
        "context_hint": "Update documentation and TESTING.md.",
        "migration_scope": None,
    })

    return {"plan": plan}
