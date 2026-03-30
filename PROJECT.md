# PROJECT.md — Multi-Agent Software Development Loop

## Purpose

This project is a multi-agent software development orchestration system built on LangGraph (Python). It automates the full dev cycle for a target repository: task intake → AI planning → parallel code generation → code review → test execution → artifact commit, with human-in-the-loop checkpoints and structured escalation paths.

## Architecture Overview

The system is composed of two independently runnable pipelines:

### Phase 0 — Ingestion Pipeline
Runs once per target repository. Analyzes the codebase and generates the four MD context files that all agents depend on. Skips if MD files are already current (hash comparison). Two parallel analysis tracks (markdown scan + structure detection) feed into four parallel MD generators.

### Dev Loop — Main Orchestration Pipeline
Receives a task spec (GitHub issue, Jira ticket, or plain prompt) and executes:

```
task_ingestion → context_assembly → planner → human_gate (HITL)
  → [parallel workers: backend / frontend / docs]
  → code_review_graph → review_gate → test_loop → artifact_update
```

Failure paths route to `user_elicitation`, which surfaces a structured escalation artifact instead of crashing.

## Key Frameworks and Technologies

| Component | Technology |
|---|---|
| Orchestration | LangGraph 0.2+ (Python) |
| LLM | Anthropic Claude (via `langchain-anthropic`) |
| Checkpointing | `AsyncSqliteSaver` (aiosqlite) |
| Observability | LangSmith (`LANGSMITH_PROJECT=AI-WORKFLOW`) |
| Import graph | NetworkX |
| Git diff parsing | unidiff |
| Code review | CodeRabbit API (LLM fallback when key absent) |
| Config | Pydantic BaseSettings |

## Languages Supported (Import Graph)

The `code_review_graph` node builds an import dependency graph for token-efficient code review. Supported: Python (AST), Go (regex), TypeScript/JavaScript (regex). Falls back gracefully to changed-files-only for other languages.

## Repository Layout

```
src/
  config.py              — Pydantic settings, env loading
  llm/client.py          — ChatAnthropic factory (cached, single source of truth)
  state/                 — TypedDict state schemas + reducers
  graphs/                — Graph wiring and compile functions
  nodes/ingestion/       — Ingestion pipeline nodes
  nodes/dev_loop/        — Dev loop nodes
  routers/               — Pure routing functions (no side effects)
  tools/                 — I/O tools: file, git, graph, context
scripts/
  run_ingestion.py       — CLI: run ingestion pipeline on a repo
  run_dev_loop.py        — CLI: run dev loop for a task (handles HITL)
```

## Inter-Agent Communication

Agents do not call each other. All communication flows through the shared `DevLoopState` dict managed by the orchestrator. The `worker_outputs` field uses an `operator.or_` reducer so parallel workers merge results without overwriting each other.

## Human-in-the-Loop

The `human_gate` node uses `interrupt()` to pause execution. The CLI surfaces the planner's subtask dependency graph, waits for approval, then resumes via `Command(resume=True)`. Thread ID is printed at the end of each run for resuming from checkpoints.

## Retry and Escalation Policy

| Gate | Max Retries | On Cap |
|---|---|---|
| Planner schema validation | 2 (in-node) | Halt |
| Review gate | 2 | User elicitation |
| Test loop | 3 | User elicitation |

## Dev Cycle Notes

- Install: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Run ingestion: `.venv/bin/python scripts/run_ingestion.py --repo-path /path/to/repo`
- Run dev loop: `.venv/bin/python scripts/run_dev_loop.py --task '{"title":"...","type":"feature","scope":"both"}'`
- Resume a run: add `--thread-id <id>` (printed at end of each run)
- Checkpoints: stored in `checkpoints.db` (SQLite, created automatically)
- Tracing: set `LANGSMITH_API_KEY` in `.env` — traces appear in project `AI-WORKFLOW`


## TO ADD LATER:
- Adding Langsmith to add observability to workflows
- Add library of skills to be injected at run time depending on framework/language/interfaces
- Transform this into a subgraph (no reason to yet)
