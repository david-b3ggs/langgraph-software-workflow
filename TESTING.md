# TESTING.md

## Test Runner

Run the full test suite from the project root:

```bash
pytest -v --asyncio-mode=auto
```

The `--asyncio-mode=auto` flag is required because the project uses `pytest-asyncio` for async test support. If a `pyproject.toml` or `pytest.ini` is added with `asyncio_mode = auto` configured, the flag can be omitted.

To run a specific test file:

```bash
pytest -v --asyncio-mode=auto src/nodes/dev_loop/test_loop.py
```

To run tests matching a keyword expression:

```bash
pytest -v --asyncio-mode=auto -k "test_some_function"
```

## Test Layout

The project uses a **hybrid layout** — tests are both co-located with source code and placed in a top-level directory:

| Location | Description |
|---|---|
| `src/nodes/dev_loop/test_loop.py` | Co-located tests for the dev loop graph logic |
| `tests/` | Top-level test directory (currently contains `__init__.py` only; use for cross-cutting or integration tests) |

Both locations are discovered automatically by `pytest` since test files follow the `test_*.py` naming convention.

**When adding new tests:**

- **Unit tests for a specific module** — co-locate alongside the source file in the same directory (e.g., `src/nodes/dev_loop/test_planner.py` for planner logic).
- **Integration or cross-module tests** — place in `tests/` with a descriptive filename (e.g., `tests/test_graph_integration.py`).
- **All test files** must be prefixed with `test_` and all test functions must be prefixed with `test_`.

## Test Types

| Type | Present | How to Identify | Notes |
|---|---|---|---|
| **Unit tests** | Yes | Co-located `test_*.py` files under `src/nodes/` | `src/nodes/dev_loop/test_loop.py` tests dev loop graph node logic |
| **Integration tests** | Likely | Tests exercising multiple graph nodes or full state transitions | Async graph-based tests may implicitly cover integration paths; no dedicated markers yet |
| **End-to-end tests** | Not yet present | Would live in `tests/` with `e2e` in the name or marked with `@pytest.mark.e2e` | No e2e test files or fixtures observed |

Tests are **not currently separated** by type via directory structure or pytest markers. All tests run together in a single `pytest` invocation.

**Convention for future separation** — use pytest markers:

```python
import pytest

@pytest.mark.unit
async def test_node_returns_expected_state():
    ...

@pytest.mark.integration
async def test_full_graph_execution():
    ...
```

Then run selectively:

```bash
pytest -v --asyncio-mode=auto -m unit
pytest -v --asyncio-mode=auto -m integration
```

Markers must be registered in `pyproject.toml` or `pytest.ini` to avoid warnings.

## Coverage

Generate a coverage report with:

```bash
pytest --cov=src --cov-report=term-missing --asyncio-mode=auto
```

For an HTML report:

```bash
pytest --cov=src --cov-report=html --asyncio-mode=auto
```

The HTML report is written to `htmlcov/`. Open `htmlcov/index.html` in a browser to inspect line-by-line coverage.

Coverage is scoped to `src/` — this ensures only project source code is measured, excluding test files and scripts.

## Fixtures & Helpers

### Async test functions

All graph node functions are `async def`. Test functions that exercise them must also be async:

```python
import pytest

@pytest.mark.asyncio
async def test_some_node():
    result = await some_node(state)
    assert result["status"] == "complete"
```

With `--asyncio-mode=auto`, the `@pytest.mark.asyncio` decorator is optional — all `async def test_*` functions are automatically treated as async tests.

### State construction

Graph nodes consume and return Pydantic-modeled state objects. Tests should construct minimal valid state instances for the node under test. Example pattern:

```python
from src.nodes.dev_loop.state import DevLoopState  # adjust import to actual module

def make_state(**overrides):
    """Create a minimal DevLoopState with sensible defaults, applying overrides."""
    defaults = {
        "task": "test task",
        "status": "pending",
        # ... other required fields with safe defaults
    }
    defaults.update(overrides)
    return DevLoopState(**defaults)
```

Place shared fixtures and helpers in a `conftest.py` file:

- `src/nodes/dev_loop/conftest.py` — fixtures for dev loop tests
- `tests/conftest.py` — fixtures shared across all top-level tests

### Mocking LLM calls

Tests should **not** make real API calls to Anthropic or any external service. Mock LLM responses using `unittest.mock.AsyncMock` or `pytest-mock`:

```python
from unittest.mock import AsyncMock, patch

async def test_planner_node(mocker):
    mock_llm = AsyncMock(return_value="mocked plan output")
    mocker.patch("src.nodes.dev_loop.planner.llm_call", mock_llm)
    result = await planner_node(state)
    assert result["plan"] is not None
```

### Checkpoint / SQLite fixtures

If testing checkpointing behavior, use a temporary SQLite database:

```python
import tempfile
import os

@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    os.unlink(f.name)
```

## CI Integration

No CI configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.) were detected in the repository.

**Recommended CI command:**

```bash
pip install -r requirements.txt
pytest -v --asyncio-mode=auto --cov=src --cov-report=term-missing
```

**Environment requirements for CI:**

- Python 3.x
- `ANTHROPIC_API_KEY` must be set as a secret (required by `pydantic-settings` validation at import time in some modules). For test runs that mock all LLM calls, set it to a dummy value: `ANTHROPIC_API_KEY=sk-ant-test-dummy`.
- No other external services are required if LLM calls are properly mocked.