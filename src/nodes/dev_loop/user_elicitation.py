import logging
from src.state.dev_loop_state import DevLoopState

logger = logging.getLogger(__name__)


async def user_elicitation_node(state: DevLoopState) -> dict:
    """Surface a structured escalation artifact when retry caps are hit.
    This is a first-class output — not an error state."""
    review_capped = state.get("review_retry_count", 0) >= 2
    test_capped   = state.get("test_retry_count", 0) >= 3
    trigger = "review_cap" if review_capped else "test_cap"

    escalation = {
        "trigger":        trigger,
        "review_retries": state.get("review_retry_count", 0),
        "test_retries":   state.get("test_retry_count", 0),
        "worker_outputs": state.get("worker_outputs", {}),
        "review_result":  state.get("review_result"),
        "test_result":    state.get("test_result"),
        "options": [
            "edit_task_spec",
            "resume_from_checkpoint",
            "abort",
        ],
    }

    logger.warning("user_elicitation: escalating — trigger=%s", trigger)
    # STUB — Phase 5 implements webhook/Slack notification
    print("\n[ESCALATION] Human intervention required.")
    print(f"  Trigger:        {trigger}")
    print(f"  Review retries: {escalation['review_retries']}")
    print(f"  Test retries:   {escalation['test_retries']}")
    print(f"  Options:        {escalation['options']}")

    return {"escalated": True, "escalation_context": escalation}
