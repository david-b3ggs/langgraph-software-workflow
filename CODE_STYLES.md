# CODE_STYLES.md — Code Architecture Standards

## Guiding Principles

1. **Orchestrator is deterministic code** — LLMs do cognitive work (planning, writing, reviewing). The orchestrator does coordination (routing, sequencing, state, retries). Never mix these.
2. **Structured outputs at all boundaries** — JSON/schema-validated output between every stage. Free text only inside agent reasoning.
3. **Shared state, no direct agent-to-agent calls** — agents read/write `DevLoopState`. Every run is reproducible from a state snapshot.
4. **Escalation is a first-class output** — retry cap hits produce structured artifacts, not exceptions.

## Node Patterns

### Async node signature
```python
async def my_node(state: DevLoopState) -> dict:
    # Read from state
    # Do work (I/O, LLM call, subprocess)
    # Return ONLY the fields that changed — partial update dict
    return {"field": new_value}
```

Nodes must return partial dicts, not the full state object. Never mutate state in place.

### LLM nodes — structured output
```python
llm = get_llm().with_structured_output(MySchema)
result = await llm.ainvoke([SystemMessage(system_prompt), HumanMessage(user_content)])
```

### Retry pattern (in-node, not graph-level)
```python
for attempt in range(MAX_RETRIES):
    try:
        result = await llm.ainvoke(...)
        break
    except ValidationError:
        if attempt == MAX_RETRIES - 1:
            return {"plan": None}  # Signal halt via state
        continue
```

## Routing Functions

Routing functions in `src/routers/` are **pure functions** — no I/O, no side effects. They inspect state and return either a destination string or a list of `Send` objects. They are unit-testable without a running graph.

```python
def route_review(state: DevLoopState):
    if state.get("review_result", {}).get("passed"):
        return "test_loop"
    if state.get("review_retry_count", 0) >= 2:
        return "user_elicitation"
    return dispatch_workers(state)  # Returns [Send(...), ...]
```

## State Reducers

Fields that accumulate parallel worker results use `operator.or_` (dict merge):
```python
worker_outputs: Annotated[dict[str, WorkerOutput], operator.or_]
```

Fields that accumulate list results use `operator.add`:
```python
messages: Annotated[list, operator.add]
```

All other fields are plain assignment (last-write wins).

## Tools Layer (`src/tools/`)

Tools are side-effectful I/O helpers separated from node logic. Nodes call tools; nodes do not contain raw subprocess calls or file reads directly. This keeps nodes unit-testable by mocking tool functions.

- `file_tools.py` — MD file loading, hashing, writing
- `git_tools.py` — `unidiff` diff parsing, subprocess git ops
- `graph_tools.py` — NetworkX import graph builder
- `context_tools.py` (Phase 3) — MD compression, token budget enforcement

## LLM Client

Always use `get_llm()` from `src/llm/client.py`. Never instantiate `ChatAnthropic` directly in node code. This ensures model name, temperature, and LangSmith tracing are configured in one place.

## Config and Secrets

All configuration via `src/config.py` (Pydantic `BaseSettings`). All secrets in `.env`. Never hardcode API keys or paths.

## Error Handling

| Error type | Strategy |
|---|---|
| Transient (network, rate limit) | `RetryPolicy` on `add_node()` |
| LLM tool failures | `ToolNode(handle_tool_errors=True)` |
| Schema validation failure | In-node retry up to cap, then return sentinel value |
| Unexpected | Let bubble up — don't swallow |

## File Naming

- Node files: `src/nodes/<pipeline>/<node_name>.py` — one node per file
- Router files: `src/routers/<pipeline>_routers.py` — all routing for one graph
- Tool files: `src/tools/<domain>_tools.py`

## Import Conventions

```python
# Absolute imports only (src/ is on sys.path via CLI scripts)
from src.state.dev_loop_state import DevLoopState
from src.tools.file_tools import load_md_files
from src.llm.client import get_llm
```
