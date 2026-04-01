import logging
from pydantic import BaseModel
from src.state.dev_loop_state import DevLoopState, WorkerOutput
from src.llm.client import get_llm

logger = logging.getLogger(__name__)


class _WorkerOutputModel(BaseModel):
    diff: str
    modified_files: list[str]
    rationale: str


_DOCS_PROMPT = """You are a technical writer. Update the project documentation for the task below as a unified diff.
Typically targets .md files (README, TESTING.md, etc.).

Output ONLY a JSON object with these fields:
- diff: the full unified diff (--- a/file / +++ b/file / @@ ... @@ format)
- modified_files: list of file paths that are modified (from the +++ b/ lines)
- rationale: one or two sentences explaining what documentation was updated and why

Testing guidelines (for reference):
{testing_md}

Project context:
{project_md}

Task: {title}
Subtask context: {context_hint}
"""


async def worker_docs_node(state: DevLoopState) -> dict:
    """Docs worker: generates documentation diffs for its assigned subtask."""
    task = state.get("current_task") or {}
    logger.info("worker_docs: task_id=%s", task.get("id"))

    md = state.get("compressed_md", {})
    prompt = _DOCS_PROMPT.format(
        testing_md=md.get("TESTING.md", ""),
        project_md=md.get("PROJECT.md", ""),
        title=state["task"].get("title", ""),
        context_hint=task.get("context_hint", ""),
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(_WorkerOutputModel)

    try:
        result: _WorkerOutputModel = await structured_llm.ainvoke(prompt)
        output: WorkerOutput = {
            "agent": "docs",
            "diff": result.diff,
            "modified_files": result.modified_files,
            "rationale": result.rationale,
            "passed_review": False,
        }
    except Exception as exc:
        logger.error("worker_docs: LLM call failed: %s", exc)
        output = {
            "agent": "docs",
            "diff": "",
            "modified_files": [],
            "rationale": f"worker failed: {exc}",
            "passed_review": False,
        }

    return {"worker_outputs": {"docs": output}}
