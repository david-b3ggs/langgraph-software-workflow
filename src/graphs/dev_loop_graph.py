from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.config import settings
from src.state.dev_loop_state import DevLoopState

from src.nodes.dev_loop.task_ingestion   import task_ingestion_node
from src.nodes.dev_loop.context_assembly import context_assembly_node
from src.nodes.dev_loop.planner          import planner_node
from src.nodes.dev_loop.human_gate       import human_gate_node
from src.nodes.dev_loop.worker_backend   import worker_backend_node
from src.nodes.dev_loop.worker_frontend  import worker_frontend_node
from src.nodes.dev_loop.worker_docs      import worker_docs_node
from src.nodes.dev_loop.code_review_graph import build_review_subgraph_node
from src.nodes.dev_loop.review_gate      import review_gate_node
from src.nodes.dev_loop.test_loop        import test_loop_node
from src.nodes.dev_loop.artifact_update  import artifact_update_node
from src.nodes.dev_loop.user_elicitation import user_elicitation_node

from src.routers.dev_loop_routers import (
    route_planner,
    dispatch_workers,
    route_review,
    route_test,
)

_WORKER_NODES = ["worker_backend", "worker_frontend", "worker_docs"]


def build_dev_loop_graph() -> StateGraph:
    graph = StateGraph(DevLoopState)

    # --- Nodes ---
    graph.add_node("task_ingestion",    task_ingestion_node)
    graph.add_node("context_assembly",  context_assembly_node)
    graph.add_node("planner",           planner_node)
    graph.add_node("human_gate",        human_gate_node)
    graph.add_node("worker_backend",    worker_backend_node)
    graph.add_node("worker_frontend",   worker_frontend_node)
    graph.add_node("worker_docs",       worker_docs_node)
    graph.add_node("code_review_graph", build_review_subgraph_node)
    graph.add_node("review_gate",       review_gate_node)
    graph.add_node("test_loop",         test_loop_node)
    graph.add_node("artifact_update",   artifact_update_node)
    graph.add_node("user_elicitation",  user_elicitation_node)

    # --- Linear spine ---
    graph.add_edge(START,             "task_ingestion")
    graph.add_edge("task_ingestion",  "context_assembly")
    graph.add_edge("context_assembly","planner")

    # Planner: validated plan → human_gate, or halt on malformed output
    graph.add_conditional_edges("planner", route_planner, {
        "proceed": "human_gate",
        "halt":    END,
    })

    # HITL → fan-out via Send (dispatch_workers returns [Send(...), ...])
    graph.add_conditional_edges("human_gate", dispatch_workers, _WORKER_NODES)

    # Workers fan-in to code_review_graph (LangGraph waits for all Send branches)
    graph.add_edge("worker_backend",  "code_review_graph")
    graph.add_edge("worker_frontend", "code_review_graph")
    graph.add_edge("worker_docs",     "code_review_graph")
    graph.add_edge("code_review_graph", "review_gate")

    # Review gate: pass → test_loop, retry → re-dispatch workers, cap → escalate
    graph.add_conditional_edges(
        "review_gate", route_review,
        ["test_loop", "user_elicitation"] + _WORKER_NODES,
    )

    # Test loop: pass → artifact_update, retry → re-dispatch workers, cap → escalate
    graph.add_conditional_edges(
        "test_loop", route_test,
        ["artifact_update", "user_elicitation"] + _WORKER_NODES,
    )

    graph.add_edge("artifact_update",  END)
    graph.add_edge("user_elicitation", END)

    return graph


def compile_dev_loop(checkpointer=None) -> object:
    """Compile the dev loop graph.

    Pass an AsyncSqliteSaver (or any BaseCheckpointSaver) instance.
    Use build_checkpointer() in an async context to create one.
    """
    graph = build_dev_loop_graph()
    return graph.compile(checkpointer=checkpointer)


async def build_checkpointer(db_path: str | None = None):
    """Open an async SQLite connection and return an AsyncSqliteSaver.
    Must be used as: async with build_checkpointer() as cp: ..."""
    import aiosqlite
    path = db_path or settings.checkpoints_db
    conn = await aiosqlite.connect(path)
    return AsyncSqliteSaver(conn)
