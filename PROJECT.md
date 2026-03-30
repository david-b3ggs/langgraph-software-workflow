# PROJECT.md

## Purpose

This project implements a multi-agent software development orchestration loop using LangGraph. It provides an automated pipeline that analyzes existing codebases to generate contextual markdown files (PROJECT.md, CODE_STYLES.md, BRAND_STYLES.md, TESTING.md), then runs a continuous development loop where specialized AI agents collaborate to plan, implement, review, and test software changes. The system includes an ingestion/bootstrap phase (Phase 0) for cold-start repo analysis and a persistent dev loop (Phase 1) for ongoing task execution, with a human approval checkpoint before any code is written.

## Architecture

### High-Level Components

```
src/
  └── nodes/
        └── dev_loop/       — Core development loop graph nodes, agent logic, and co-located tests
scripts/                     — Utility and runner scripts
tests/                       — Top-level test suite (additional test root)
```

### Data Flow

1. **Ingestion Pipeline (Phase 0)** — Runs once per repo. Performs parallel analysis of repo structure (directory layout, DB schemas, frameworks, tests) and existing markdown/README files. Optionally fetches external docs for detected dependencies. Generates four context markdown files consumed by all downstream agents: `PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, `TESTING.md`.

2. **Dev Loop (Phase 1)** — A LangGraph-based stateful graph that orchestrates a 7-stage pipeline per task:

```
task_ingestion → context_assembly → planner → [human_gate] → parallel workers (backend, frontend, docs)
    → code_review_graph → review_gate → test_loop → artifact_update
```

Workers run in parallel. Review and test failures retry automatically; repeated failures escalate to `user_elicitation`.

3. **State & Checkpointing** — State flows through the LangGraph graph as a Pydantic-modeled object. Checkpointing occurs at each node transition via `langgraph-checkpoint-sqlite` backed by `aiosqlite`, enabling persistence, retry, and recovery on failure.

### Key Layers

| Layer | Description |
|---|---|
| **Graph Definition** | LangGraph graph(s) defining node transitions and conditional edges |
| **Nodes/Agents** | Individual agent logic under `src/nodes/`, organized by functional area |
| **State Schema** | Pydantic models defining the shared state passed between nodes |
| **Checkpointing** | SQLite-backed persistence for graph state via `langgraph-checkpoint-sqlite` |
| **Context Files** | Generated markdown files at repo root carrying shared knowledge between agents |

## Languages & Frameworks

| Technology | Version | Role |
|---|---|---|
| **Python** | 3.x | Primary language |
| **LangGraph** | ≥0.2.0 | Graph-based agent orchestration framework |
| **LangChain** | ≥0.2.0 | LLM interaction and chain abstractions |
| **langchain-anthropic** | ≥0.1.0 | Anthropic (Claude) model integration |
| **langchain-mcp-adapters** | ≥0.1.0 | MCP tool/server integration (used for external doc fetching) |
| **langgraph-checkpoint-sqlite** | ≥0.1.0 | SQLite-backed graph state checkpointing |
| **Pydantic** | ≥2.0.0 | State schema and settings validation |
| **pydantic-settings** | ≥2.0.0 | Environment-based configuration |
| **httpx** | ≥0.27.0 | Async HTTP client |
| **aiosqlite** | ≥0.19.0 | Async SQLite driver (checkpoint backend) |
| **unidiff** | ≥0.7.5 | Unified diff parsing (likely for code review/patch handling) |
| **networkx** | ≥3.0 | Graph analysis (likely for dependency/structure analysis) |
| **python-dotenv** | ≥1.0.0 | `.env` file loading |
| **pytest** | ≥8.0.0 | Test runner |
| **pytest-asyncio** | ≥0.23.0 | Async test support |
| **LangSmith** | ≥0.1.0 | Optional tracing and observability |

## Key Conventions

### Module Layout
- Source code lives under `src/`. Node/agent implementations are organized by function under `src/nodes/`.
- Graph nodes for the dev loop are grouped in `src/nodes/dev_loop/`.
- Scripts and runners go in `scripts/`.
- Context markdown files (`PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, `TESTING.md`) live at the repository root.

### Naming
- Files and directories: `snake_case`.
- Classes and Pydantic models: `PascalCase`.
- Functions and methods (including async): `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Test files: prefixed with `test_` (e.g., `test_loop.py`), following pytest discovery conventions.

### Async Patterns
- **Async-first**: Graph nodes and agent functions are implemented as `async def`.
- Event loop management is handled by LangGraph's execution runtime — node functions must not create or manage their own event loops.
- Async libraries (`httpx`, `aiosqlite`) are used throughout.

### Testing
- Hybrid test layout: co-located tests alongside source (`src/nodes/dev_loop/test_loop.py`) and a top-level `tests/` directory.
- Tests run via `pytest` with `pytest-asyncio` for async support (`--asyncio-mode=auto`).
- Coverage via `pytest --cov=src`.

### Configuration
- Environment variables loaded from a `.env` file at the project root via `python-dotenv`.
- `ANTHROPIC_API_KEY` is required. `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, and `ANTHROPIC_MODEL` are optional.
- Default model is `claude-opus-4-6` (overridable via `ANTHROPIC_MODEL`).

## Entry Points

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...
# Optional
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=AI-WORKFLOW
ANTHROPIC_MODEL=claude-sonnet-4-6
```

### Running

Runner scripts are located in `scripts/`. The system is invoked via these scripts (exact entry point script names are defined within that directory).

### Testing

```bash
pytest -v --asyncio-mode=auto
```

With coverage:

```bash
pytest --cov=src --cov-report=term-missing
```