# PROJECT.md

## Purpose

This project implements a multi-agent software development orchestration loop using LangGraph. It provides an automated pipeline that analyzes existing codebases to generate contextual markdown files (PROJECT.md, CODE_STYLES.md, etc.), then runs a continuous development loop where specialized AI agents collaborate to plan, implement, and validate software changes. The system includes an ingestion/bootstrap phase (Phase 0) for cold-start repo analysis and a persistent dev loop for ongoing task execution.

## Architecture

### High-Level Components

```
src/
  └── nodes/
        └── dev_loop/       — Core development loop graph nodes and logic
scripts/                     — Utility/runner scripts
tests/                       — Test suite
```

### Data Flow

1. **Ingestion Pipeline (Phase 0)** — Runs once per repo. Performs parallel analysis of repo structure (directory layout, DB schemas, frameworks, tests) and existing markdown/README files. Optionally fetches external docs for detected dependencies. Generates context markdown files (PROJECT.md, CODE_STYLES.md, BRAND_STYLES.md, TESTING.md).

2. **Dev Loop** — A LangGraph-based stateful graph that orchestrates agent interactions. Nodes in the graph represent agent responsibilities (planning, implementation, validation). State is checkpointed (via `langgraph-checkpoint-sqlite` / `aiosqlite`) to enable retry/resume on failure.

3. **State flows through the LangGraph graph** with checkpointing at each node transition, enabling persistence and recovery.

### Key Layers

- **Graph Definition** — LangGraph graph(s) defining node transitions and conditional edges
- **Nodes/Agents** — Individual agent logic housed under `src/nodes/`
- **State Schema** — Pydantic models defining the shared state passed between nodes
- **Checkpointing** — SQLite-backed persistence for graph state

## Languages & Frameworks

| Technology | Role |
|---|---|
| **Python** | Primary language |
| **LangGraph** (≥0.2.0) | Graph-based agent orchestration framework |
| **LangChain** (≥0.2.0) | LLM interaction abstractions and tooling |
| **langchain-anthropic** (≥0.1.0) | Anthropic (Claude) model integration |
| **langgraph-checkpoint-sqlite** (≥0.1.0) | SQLite-based state checkpointing for graph persistence |
| **Pydantic** (≥2.0.0) | State schema validation and settings management |
| **pydantic-settings** (≥2.0.0) | Environment/configuration management |
| **unidiff** (≥0.7.5) | Parsing and handling of unified diff / patch files |
| **networkx** (≥3.0) | Graph analysis (likely for dependency or structure analysis) |
| **httpx** (≥0.27.0) | Async HTTP client (for doc fetching and API calls) |
| **aiosqlite** (≥0.19.0) | Async SQLite access for checkpointing |
| **python-dotenv** (≥1.0.0) | Environment variable loading from `.env` files |
| **pytest** (≥8.0.0) / **pytest-asyncio** (≥0.23.0) | Testing framework with async support |

## Key Conventions

- **Async patterns** — The project uses async I/O throughout (httpx, aiosqlite, pytest-asyncio), indicating graph nodes and agents are implemented as async functions.
- **Pydantic for state** — State schemas and configuration use Pydantic v2 models (`pydantic-settings` for env-based config).
- **Environment configuration** — Uses `.env` files via `python-dotenv` for API keys and settings.
- **Markdown-driven context** — The system generates and consumes structured markdown files (PROJECT.md, CODE_STYLES.md, BRAND_STYLES.md, TESTING.md) as shared context between agents and phases.
- **Module layout** — Source code lives under `src/` with node implementations organized by function under `src/nodes/`. Tests colocate with source (`test_loop.py` alongside dev_loop code) and also exist in a top-level `tests/` directory.
- **Diff-based changes** — The `unidiff` dependency indicates agents produce or consume unified diffs/patches for code modifications rather than full file rewrites.

## Entry Points

- **Dev Loop** — Primary execution is through the LangGraph graph defined in `src/nodes/dev_loop/`. The exact runner script is likely in `scripts/` or invoked programmatically.
- **Tests** — Run via `pytest` from the project root. Test files include `src/nodes/dev_loop/test_loop.py` and the `tests/` directory.
- **Configuration** — Requires a `.env` file with API keys (minimally an Anthropic API key for `langchain-anthropic`).