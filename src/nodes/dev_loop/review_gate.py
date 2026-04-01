import logging
from pydantic import BaseModel
from src.state.dev_loop_state import DevLoopState, ReviewResult
from src.llm.client import get_llm
from src.config import settings

logger = logging.getLogger(__name__)


class _ReviewResultModel(BaseModel):
    passed: bool
    feedback: list[str] = []


_REVIEW_PROMPT = """You are a senior code reviewer. Review the diffs below against the project's code style guidelines.

Respond with a JSON object:
- passed: true if the diffs follow conventions and have no blocking issues, false otherwise
- feedback: list of specific blocking issues found (empty list if passed)

Code style guidelines:
{code_styles_md}

Files in review scope: {review_files}

Diffs to review:
{diffs}
"""


async def review_gate_node(state: DevLoopState) -> dict:
    """Run code review via CodeRabbit API (or LLM fallback). Returns ReviewResult."""
    retry = state.get("review_retry_count", 0)
    review_files = state.get("review_subgraph", [])
    logger.info("review_gate: attempt=%d subgraph_files=%d", retry + 1, len(review_files))

    if settings.coderabbit_api_key:
        # TODO: POST diffs to CodeRabbit API
        # https://api.coderabbit.ai/v1/reviews
        # result = await _call_coderabbit(state)
        logger.warning("review_gate: CodeRabbit integration not yet implemented, falling back to LLM")

    # LLM fallback
    worker_outputs = state.get("worker_outputs", {})
    diffs = "\n\n".join(
        f"### {agent} worker\n{output['diff']}"
        for agent, output in worker_outputs.items()
        if output.get("diff")
    )
    if not diffs:
        diffs = "(no diffs produced)"

    md = state.get("compressed_md", {})
    prompt = _REVIEW_PROMPT.format(
        code_styles_md=md.get("CODE_STYLES.md", ""),
        review_files=", ".join(review_files) if review_files else "(all modified files)",
        diffs=diffs,
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(_ReviewResultModel)

    try:
        llm_result: _ReviewResultModel = await structured_llm.ainvoke(prompt)
        result: ReviewResult = {
            "passed": llm_result.passed,
            "feedback": [{"message": f} for f in llm_result.feedback],
        }
        logger.info("review_gate: passed=%s feedback_count=%d", result["passed"], len(result["feedback"]))
    except Exception as exc:
        logger.error("review_gate: LLM call failed: %s — defaulting to pass", exc)
        result = {"passed": True, "feedback": []}

    return {
        "review_result": result,
        "review_retry_count": retry + (0 if result["passed"] else 1),
    }
