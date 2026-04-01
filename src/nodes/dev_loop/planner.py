import logging
from pydantic import BaseModel, ValidationError
from src.state.dev_loop_state import DevLoopState
from src.llm.client import get_llm

logger = logging.getLogger(__name__)


class _SubTaskModel(BaseModel):
    id: str
    type: str  # "backend" | "frontend" | "docs"
    depends_on: list[str] = []
    context_hint: str
    migration_scope: str | None = None


class _PlanModel(BaseModel):
    subtasks: list[_SubTaskModel]


_PLANNER_PROMPT = """You are a senior software architect. Given the project context and task below, produce a structured plan as a list of subtasks.

Rules:
- Only produce subtasks matching the requested scope: {scope}
- Each subtask must have a unique id (e.g. "be-1", "fe-1", "docs-1")
- type must be one of: backend, frontend, docs
- context_hint must be a concrete one-liner describing exactly what this subtask should implement
- Set migration_scope to a short description only if a DB schema change is needed; otherwise leave it null
- depends_on lists ids of subtasks that must complete before this one (can be empty)

Project context:
{project_md}

Task:
  title: {title}
  type: {task_type}
  scope: {scope}
"""


async def planner_node(state: DevLoopState) -> dict:
    """Generate a structured dependency graph of subtasks. LLM with structured output.
    Retries up to 2x on ValidationError before returning plan=None (halts graph)."""
    task = state["task"]
    logger.info("planner: task=%s", task.get("title"))

    project_md = state.get("compressed_md", {}).get("PROJECT.md", "(no PROJECT.md found)")
    prompt = _PLANNER_PROMPT.format(
        scope=task.get("scope", "both"),
        project_md=project_md,
        title=task.get("title", ""),
        task_type=task.get("type", "feature"),
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(_PlanModel)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            result: _PlanModel = await structured_llm.ainvoke(prompt)
            plan = [t.model_dump() for t in result.subtasks]
            logger.info("planner: produced %d subtasks on attempt %d", len(plan), attempt + 1)
            return {"plan": plan}
        except (ValidationError, Exception) as exc:
            last_error = exc
            logger.warning("planner: attempt %d failed: %s", attempt + 1, exc)

    logger.error("planner: exhausted retries, last error: %s", last_error)
    return {"plan": None}
