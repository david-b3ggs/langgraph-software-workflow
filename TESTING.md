# TESTING.md — Test Execution Guide

## Test Runner

```bash
# Activate venv first
source .venv/bin/activate  # or: .venv/bin/python for direct execution

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_routers.py -v

# Run with logging output visible
pytest -s
```

## Test Structure

```
tests/
  __init__.py
  test_state_models.py     — TypedDict schemas and reducer behaviour
  test_routers.py          — Routing function logic (pure functions, no LLM)
  test_graph_tools.py      — Import graph builder and subgraph extraction
```

## Environment for Tests

Tests do not require `ANTHROPIC_API_KEY` — Phase 1 and 2 tests cover pure I/O and routing logic only. Set these in `.env` or as env vars for LLM integration tests (Phase 4+):

```
ANTHROPIC_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=AI-WORKFLOW
```

## Integration Test: Dev Loop End-to-End (Scaffold)

```bash
# Pipe 'y' to auto-approve the plan
echo "y" | .venv/bin/python scripts/run_dev_loop.py \
  --task '{"title":"smoke test","type":"feature","scope":"backend"}'
```

Expected output:
- All nodes log their names in order
- HITL prompt appears with plan
- After approval: workers execute, review passes, tests pass, artifact_update runs
- `checkpoints.db` created or updated

## Integration Test: Ingestion Pipeline

```bash
.venv/bin/python scripts/run_ingestion.py --repo-path /path/to/target/repo
```

Expected output:
- Both analysis tracks log simultaneously (parallel execution)
- 4 MD files written to the target repo root
- `ingestion_complete: True`

## Resuming a Suspended Run

Each run prints a `Thread ID` at completion. Use it to resume after a checkpoint:

```bash
.venv/bin/python scripts/run_dev_loop.py \
  --task '{"title":"add login","type":"feature","scope":"both"}' \
  --thread-id <thread-id-from-previous-run>
```

## Adding New Tests

- Place test files in `tests/`
- Name test functions `test_<what>_<condition>`
- Routing function tests: pass a minimal `DevLoopState` dict with only the fields the router reads
- Tool tests: use `tmp_path` (pytest fixture) for any file I/O
- Async tests: use `@pytest.mark.asyncio` and `pytest-asyncio`

```python
import pytest
from src.routers.dev_loop_routers import route_review

def test_route_review_passes_when_result_passed():
    state = {"review_result": {"passed": True, "feedback": []}, "review_retry_count": 0}
    assert route_review(state) == "test_loop"
```

## Checkpoints Database

`checkpoints.db` is created automatically in the project root. It is a SQLite database managed by `AsyncSqliteSaver`. Do not commit it to version control. Delete it to reset all run state.
