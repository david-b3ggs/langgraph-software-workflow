try:
    from langgraph.graph import StateGraph, START, END
except ModuleNotFoundError:
    # Helpful error message if langgraph isn't installed or import path is wrong
    raise ModuleNotFoundError("No module named 'langgraph'. Make sure 'langgraph' is installed in your Python environment (pip install langgraph) or the package is available on PYTHONPATH.")

from src.state.ingestion_state import IngestionState

from src.nodes.ingestion.analyze_markdown      import analyze_existing_markdown_node
from src.nodes.ingestion.analyze_structure     import analyze_codebase_structure_node
from src.nodes.ingestion.fetch_docs            import fetch_docs_node
from src.nodes.ingestion.generate_planner_md   import generate_planner_md_node
from src.nodes.ingestion.generate_backend_md   import generate_backend_md_node
from src.nodes.ingestion.generate_frontend_md  import generate_frontend_md_node
from src.nodes.ingestion.generate_docs_agent_md import generate_docs_agent_md_node
from src.nodes.ingestion.write_md_files        import write_md_files_to_repo_node

from src.routers.ingestion_routers import (
    dispatch_analysis_tracks,
    route_fetch_docs,
    dispatch_ingestion_generators,
)

_ANALYSIS_NODES   = ["analyze_markdown", "analyze_structure"]
_GENERATOR_NODES  = ["generate_backend", "generate_frontend", "generate_docs"]


def build_ingestion_graph() -> StateGraph:
    graph = StateGraph(IngestionState)

    # --- Nodes ---
    graph.add_node("analyze_markdown",  analyze_existing_markdown_node)
    graph.add_node("analyze_structure", analyze_codebase_structure_node)
    graph.add_node("fetch_docs",        fetch_docs_node)
    graph.add_node("generate_planner",  generate_planner_md_node)
    graph.add_node("generate_backend",  generate_backend_md_node)
    graph.add_node("generate_frontend", generate_frontend_md_node)
    graph.add_node("generate_docs",     generate_docs_agent_md_node)
    graph.add_node("write_md_files",    write_md_files_to_repo_node)

    # Parallel analysis tracks fan-out from START
    graph.add_conditional_edges(START, dispatch_analysis_tracks, _ANALYSIS_NODES)

    # Both tracks fan-in to fetch_docs
    graph.add_edge("analyze_markdown",  "fetch_docs")
    graph.add_edge("analyze_structure", "fetch_docs")

    # Conditional: skip or run external doc fetch
    graph.add_conditional_edges("fetch_docs", route_fetch_docs, {
        "needed": "generate_planner",
        "skip":   "generate_planner",
    })

    # Planner MD → parallel generator fan-out
    graph.add_conditional_edges("generate_planner", dispatch_ingestion_generators, _GENERATOR_NODES)

    # All generators fan-in to write
    graph.add_edge("generate_backend",  "write_md_files")
    graph.add_edge("generate_frontend", "write_md_files")
    graph.add_edge("generate_docs",     "write_md_files")
    graph.add_edge("write_md_files",    END)

    return graph


def compile_ingestion() -> object:
    graph = build_ingestion_graph()
    return graph.compile()


# Module-level instance for `langgraph dev` / LangGraph Studio
ingestion_graph = compile_ingestion()
