import operator
from typing import Annotated
from typing_extensions import TypedDict


class IngestionState(TypedDict):
    repo_path: str

    # Parallel Track A output — reducer merges concurrent updates
    existing_md: Annotated[dict[str, str], operator.or_]

    # Parallel Track B output — reducer merges concurrent updates
    repo_structure: Annotated[dict, operator.or_]

    # Conditional fetch
    fetched_docs: Annotated[dict[str, str], operator.or_]

    # Generated MD files
    planner_md: str
    backend_md: str
    frontend_md: str
    docs_agent_md: str

    ingestion_complete: bool


DEFAULT_INGESTION_STATE: dict = {
    "existing_md": {},
    "repo_structure": {},
    "fetched_docs": {},
    "planner_md": "",
    "backend_md": "",
    "frontend_md": "",
    "docs_agent_md": "",
    "ingestion_complete": False,
}
