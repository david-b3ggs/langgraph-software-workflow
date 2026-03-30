"""Routing functions for the ingestion pipeline graph."""
from langgraph.types import Send
from src.state.ingestion_state import IngestionState


def dispatch_analysis_tracks(state: IngestionState) -> list[Send]:
    """Fan-out to both parallel analysis tracks simultaneously."""
    return [
        Send("analyze_markdown",  state),
        Send("analyze_structure", state),
    ]


def route_fetch_docs(state: IngestionState) -> str:
    """Conditionally fetch external docs if unrecognised dependencies were found."""
    needs = state.get("repo_structure", {}).get("needs_doc_fetch", False)
    return "needed" if needs else "skip"


def dispatch_ingestion_generators(state: IngestionState) -> list[Send]:
    """Fan-out to backend/frontend/docs MD generators simultaneously."""
    return [
        Send("generate_backend",  state),
        Send("generate_frontend", state),
        Send("generate_docs",     state),
    ]
