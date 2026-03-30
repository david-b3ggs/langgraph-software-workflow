import logging
from src.state.dev_loop_state import DevLoopState, ReviewResult

logger = logging.getLogger(__name__)


async def review_gate_node(state: DevLoopState) -> dict:
    """Run code review via CodeRabbit API (or LLM fallback). Returns ReviewResult.
    Increments review_retry_count on failure."""
    retry = state.get("review_retry_count", 0)
    logger.info("review_gate: attempt=%d subgraph_files=%d", retry + 1, len(state.get("review_subgraph", [])))
    # STUB — Phase 4 implements CodeRabbit API call + LLM fallback
    result: ReviewResult = {"passed": True, "feedback": []}
    return {
        "review_result": result,
        "review_retry_count": retry + (0 if result["passed"] else 1),
    }
