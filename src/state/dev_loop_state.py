import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict


class SubTask(TypedDict):
    id: str
    type: Literal["backend", "frontend", "docs"]
    depends_on: list[str]
    context_hint: str
    migration_scope: str | None


class WorkerOutput(TypedDict):
    agent: str
    diff: str
    modified_files: list[str]
    rationale: str
    passed_review: bool


class ReviewResult(TypedDict):
    passed: bool
    feedback: list[dict]  # LineAnnotation list


class TestResult(TypedDict):
    passed: bool
    failures: list[dict]
    retry_count: int


class DevLoopState(TypedDict):
    # Task
    task: dict                          # TaskSpec: {title, type, scope}
    plan: list[SubTask] | None

    # HITL
    human_approved: bool

    # Per-worker Send payload — populated by dispatch_workers
    current_task: SubTask | None

    # Execution — reducer merges per-worker results without overwriting
    worker_outputs: Annotated[dict[str, WorkerOutput], operator.or_]
    review_subgraph: list[str]          # impacted file list from code_review_graph

    # Gate results
    review_result: ReviewResult | None
    test_result: TestResult | None

    # Retry counters
    review_retry_count: int
    test_retry_count: int

    # Escalation
    escalated: bool
    escalation_context: dict | None

    # MD versions pinned per run and compressed content per agent
    md_versions: dict[str, str]
    compressed_md: dict[str, str]


# Default state values used when initialising a new run
DEFAULT_STATE: dict = {
    "plan": None,
    "human_approved": False,
    "current_task": None,
    "worker_outputs": {},
    "review_subgraph": [],
    "review_result": None,
    "test_result": None,
    "review_retry_count": 0,
    "test_retry_count": 0,
    "escalated": False,
    "escalation_context": None,
    "md_versions": {},
    "compressed_md": {},
}
