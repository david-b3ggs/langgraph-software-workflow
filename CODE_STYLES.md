# CODE_STYLES.md

## File & Module Layout

```
src/
  └── nodes/
        └── dev_loop/       — Core development loop graph nodes and logic
scripts/                     — Utility and runner scripts
tests/                       — Top-level test suite
```

- **Source code** lives under `src/`. Node/agent implementations are organized by function under `src/nodes/`.
- **Graph nodes** for the dev loop are grouped in `src/nodes/dev_loop/`.
- **Scripts** (runners, utilities) go in `scripts/`.
- **New modules** that represent graph nodes or agent logic should be added under `src/nodes/`, in a subdirectory named for their functional area (e.g., `src/nodes/ingestion/`).
- **Shared state schemas and configuration** should live at the `src/` level or in a dedicated `src/models/` or `src/config/` module if one is created.
- **Context markdown files** (`PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, `TESTING.md`) live at the repository root and are both generated and consumed by agents.

## Naming Conventions

- **Files and directories**: `snake_case` (e.g., `dev_loop/`, `test_loop.py`).
- **Python modules**: `snake_case`.
- **Classes**: `PascalCase`. Pydantic models follow this convention (e.g., state schemas, settings classes).
- **Functions and methods**: `snake_case`. Async functions use the same convention with no special prefix.
- **Constants**: `UPPER_SNAKE_CASE`.
- **Test files**: Prefixed with `test_` (e.g., `test_loop.py`), following pytest discovery conventions.

## Async Patterns

- **Async-first**: The project uses async I/O throughout. Graph nodes and agent functions should be implemented as `async def`.
- **Libraries**: `httpx` (async HTTP), `aiosqlite` (async SQLite), and `pytest-asyncio` confirm the async-everywhere approach.
- **Event loop**: Assumed to be managed by LangGraph's execution runtime. Do not create or manually manage event loops inside node functions.
- **Checkpointing**: State persistence uses `langgraph-checkpoint-sqlite` backed by `aiosqlite`, so checkpoint operations are non-blocking.
- When calling any I/O-bound operation (HTTP requests, database access, file system operations), use the async variant. Avoid `sync` wrappers or `run_in_executor` unless interfacing with a library that has no async API.

## Error Handling

- **Graph-level retry/resume**: LangGraph checkpointing enables retry and recovery on node failure. Nodes should raise exceptions on unrecoverable errors rather than silently swallowing them, so the graph runtime can handle retry logic.
- **Let exceptions propagate**: Do not catch broad `Exception` unless adding meaningful context or performing cleanup. Prefer specific exception types.
- **Logging**: Use Python's standard `logging` module. Each module should define its own logger: `logger = logging.getLogger(__name__)`.
- **Validation errors**: Pydantic v2 models handle input validation; let `ValidationError` propagate to signal malformed state.

## Imports & Dependencies

- **Standard library imports first**, then third-party, then local — following PEP 8 import ordering.
- **Absolute imports** from the `src` package (e.g., `from src.nodes.dev_loop.module import ...`).
- **All dependencies** are declared in `requirements.txt` at the repo root with minimum version pins (e.g., `langgraph>=0.2.0`).
- **Adding new dependencies**: Append to `requirements.txt` with a minimum version pin. Do not use upper-bound pins unless there is a known incompatibility.
- **Environment variables**: Loaded via `python-dotenv` from a `.env` file. Access configuration through `pydantic-settings` models, not raw `os.getenv()` calls.

## Testing Approach

- **Framework**: `pytest` with `pytest-asyncio` for async test support.
- **Test locations**: Tests colocate with source when tightly coupled to a module (e.g., `src/nodes/dev_loop/test_loop.py`) and also exist in the top-level `tests/` directory for broader integration or cross-cutting tests.
- **Test file naming**: `test_*.py`, following pytest auto-discovery defaults.
- **Running tests**: Execute `pytest` from the project root. No special flags are required beyond what `pytest-asyncio` provides (async tests should be marked with `@pytest.mark.asyncio`).
- **New tests**: Place unit tests for a specific node alongside that node's source. Place integration or end-to-end tests in `tests/`.