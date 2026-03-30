import logging
from typing import Literal
from src.state.dev_loop_state import DevLoopState

logger = logging.getLogger(__name__)

TaskType = Literal["feature", "bug", "refactor"]
TaskScope = Literal["frontend", "backend", "both", "infra"]


async def task_ingestion_node(state: DevLoopState) -> dict:
    """Normalise raw task input into a typed TaskSpec. No LLM — pure deterministic."""
    raw = state["task"]
    logger.info("task_ingestion: title=%s", raw.get("title"))

    task = {
        "title": raw.get("title", "Untitled task"),
        "type":  raw.get("type", "feature"),
        "scope": raw.get("scope", "both"),
        "description": raw.get("description", ""),
    }
    return {"task": task}
