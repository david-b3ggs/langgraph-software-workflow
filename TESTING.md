# TESTING.md

## Test Runner

Run the full test suite from the project root:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

Since the project uses `pytest-asyncio` for async test support, ensure the asyncio mode is set. If not configured in `pyproject.toml` or `pytest.ini`, run with:

```bash
pytest -v --asyncio-mode=auto
```

## Test Layout

Tests exist in two locations:

| Location | Description |
|---|---|
| `tests/` | Top-level test directory (currently contains `__init__.py` only) |
| `src/nodes/dev_loop/test_loop.py` | Co-located test file alongside the dev loop source code |

The project uses a hybrid layout: unit/integration tests for specific modules are co-located with their source under `src/nodes/`, while the top-level `tests/` directory serves as an additional test root.

Both locations are discovered automatically by `pytest` with default settings, since test files follow the `test_*.py` naming convention.

## Test Types

| Type | Present | Notes |
|---|---|---|
| **Unit tests** | Yes | `src/nodes/dev_loop/test_loop.py` tests dev loop graph logic |
| **Integration tests** | Likely | Graph-based orchestration tests may exercise multiple nodes together; async patterns suggest integration-level coverage of LangGraph state transitions |
| **End-to-end tests** | Not evident | No dedicated e2e test files or fixtures observed |

Tests are not currently separated by type via directory structure or markers. All tests are discovered and run together by `pytest`.

## Coverage

Generate a coverage report using `pytest-cov` (install if not already present):

```bash
pip install pytest-cov
```

Run with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

For an HTML coverage report:

```bash
pytest --cov=src --cov-report=html
```

The HTML report will be generated in `htmlcov/`.

## Fixtures & Helpers

- **`tests/__init__.py`** — Present but likely empty; makes the `tests/` directory a package for import resolution.
- **Async test support** — `pytest-asyncio` (≥0.23.0) is a declared dependency. Async test functions should be decorated with `@pytest.mark.asyncio` or run with `--asyncio-mode=auto` to auto-detect async tests.
- **Environment configuration** — Tests that exercise LLM-calling agents or graph nodes may require a `.env` file with valid API keys (minimally `ANTHROPIC_API_KEY`). For unit tests that mock external calls, no API keys are needed.
- **SQLite checkpointing** — Tests involving graph state persistence use `aiosqlite` and `langgraph-checkpoint-sqlite`. These create temporary SQLite databases; no external database setup is required.

## CI Integration

No CI configuration files (e.g., `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`) were detected in the repository structure. If CI is added, the recommended test command is:

```bash
pytest -v --asyncio-mode=auto --tb=short
```

For CI environments where API keys are unavailable, consider marking LLM-dependent tests with a custom marker and skipping them:

```bash
pytest -v --asyncio-mode=auto -m "not requires_api_key"
```