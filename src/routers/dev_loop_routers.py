"""Routing functions for the dev loop graph.

These are pure functions — they inspect state and return either a destination
string or a list of Send objects for fan-out. No side effects.
"""
from langgraph.types import Send
from src.state.dev_loop_state import DevLoopState


def route_planner(state: DevLoopState) -> str:
    """Halt if planner returned None (validation failures exhausted retries)."""
    return "halt" if state.get("plan") is None else "proceed"


def dispatch_workers(state: DevLoopState) -> list[Send]:
    """Fan-out to all subtasks in parallel.

    Sends every task in the plan in one wave. The planner's context_hint
    encodes ordering guidance for each worker. On retry all tasks are
    re-dispatched (existing worker_outputs from the prior pass remain in state
    and are overwritten by the new run).
    """
    plan = state.get("plan") or []
    return [Send(f"worker_{t['type']}", {**state, "current_task": t}) for t in plan]


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
