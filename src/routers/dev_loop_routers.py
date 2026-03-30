"""Routing functions for the dev loop graph.

These are pure functions — they inspect state and return either a destination
string or a list of Send objects for fan-out. No side effects.
"""
from langgraph.types import Send
from src.state.dev_loop_state import DevLoopState, SubTask


def _get_ready_tasks(plan: list[SubTask], completed: dict) -> list[SubTask]:
    """Return subtasks whose dependencies have all been completed."""
    done_ids = set(completed.keys())
    return [t for t in plan if all(dep in done_ids for dep in t["depends_on"])]


def route_planner(state: DevLoopState) -> str:
    """Halt if planner returned None (validation failures exhausted retries)."""
    return "halt" if state.get("plan") is None else "proceed"


def dispatch_workers(state: DevLoopState) -> list[Send]:
    """Fan-out to worker nodes for all currently ready subtasks.

    Called as a routing function from add_conditional_edges — used on both the
    initial dispatch (from human_gate) and retry dispatches (from review/test routing).
    """
    plan = state.get("plan") or []
    completed = state.get("worker_outputs") or {}
    ready = _get_ready_tasks(plan, completed)
    if not ready:
        # Fallback: re-run all tasks (e.g. on retry when outputs were reset)
        ready = plan
    return [Send(f"worker_{t['type']}", {**state, "current_task": t}) for t in ready]


def route_review(state: DevLoopState):
    """Pass → test_loop. Cap hit → user_elicitation. Retry → re-dispatch workers."""
    r = state.get("review_result")
    if r and r["passed"]:
        return "test_loop"
    if state.get("review_retry_count", 0) >= 2:
        return "user_elicitation"
    # Retry: inject review feedback into state (already present) and re-dispatch
    return dispatch_workers(state)


def route_test(state: DevLoopState):
    """Pass → artifact_update. Cap hit → user_elicitation. Retry → re-dispatch workers."""
    t = state.get("test_result")
    if t and t["passed"]:
        return "artifact_update"
    if state.get("test_retry_count", 0) >= 3:
        return "user_elicitation"
    return dispatch_workers(state)
