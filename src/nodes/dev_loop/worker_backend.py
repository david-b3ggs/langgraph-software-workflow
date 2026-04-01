import logging
from pydantic import BaseModel
from src.state.dev_loop_state import DevLoopState, WorkerOutput
from src.llm.client import get_llm

logger = logging.getLogger(__name__)


class _WorkerOutputModel(BaseModel):
    diff: str
    modified_files: list[str]
    rationale: str


_BACKEND_PROMPT = """You are a backend engineer. Implement the subtask below as a unified diff.

Output ONLY a JSON object with these fields:
- diff: the full unified diff (--- a/file / +++ b/file / @@ ... @@ format)
- modified_files: list of file paths that are modified (from the +++ b/ lines)
- rationale: one or two sentences explaining what was changed and why

Project context:
{project_md}

Code style guidelines:
{code_styles_md}

Task: {title}
Subtask context: {context_hint}
"""


async def worker_backend_node(state: DevLoopState) -> dict:
    """Backend worker: generates code diffs for its assigned subtask."""
    task = state.get("current_task") or {}
    logger.info("worker_backend: task_id=%s", task.get("id"))

    md = state.get("compressed_md", {})
    prompt = _BACKEND_PROMPT.format(
        project_md=md.get("PROJECT.md", ""),
        code_styles_md=md.get("CODE_STYLES.md", ""),
        title=state["task"].get("title", ""),
        context_hint=task.get("context_hint", ""),
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(_WorkerOutputModel)

    try:
        result: _WorkerOutputModel = await structured_llm.ainvoke(prompt)
        output: WorkerOutput = {
            "agent": "backend",
            "diff": result.diff,
            "modified_files": result.modified_files,
            "rationale": result.rationale,
            "passed_review": False,
        }
    except Exception as exc:
        logger.error("worker_backend: LLM call failed: %s", exc)
        output = {
            "agent": "backend",
            "diff": "",
            "modified_files": [],
            "rationale": f"worker failed: {exc}",
            "passed_review": False,
        }

    return {"worker_outputs": {"backend": output}}
