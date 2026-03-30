import logging
from src.state.dev_loop_state import DevLoopState, TestResult

logger = logging.getLogger(__name__)


async def test_loop_node(state: DevLoopState) -> dict:
    """Write/update unit tests then run the integration suite from TESTING.md.
    Increments test_retry_count on failure."""
    retry = state.get("test_retry_count", 0)
    logger.info("test_loop: attempt=%d", retry + 1)
    # STUB — Phase 4 implements LLM test generation + subprocess test runner
    result: TestResult = {"passed": True, "failures": [], "retry_count": retry}
    return {
        "test_result": result,
        "test_retry_count": retry + (0 if result["passed"] else 1),
    }
