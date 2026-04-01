# LangGraph Multi-Agent Dev Loop

A LangGraph-based orchestration system that automates the software development cycle using specialised AI agents. Point it at any repo and it will analyse the codebase, generate context files, then run a continuous loop that plans, implements, reviews, and tests changes — with a human approval checkpoint before any code is written.

## How it works

**Phase 0 — Ingestion** runs once per repo. It scans the codebase, detects languages and frameworks, reads existing documentation, and generates four context markdown files that all downstream agents rely on:

| File | Purpose |
|---|---|
| `PROJECT.md` | Architecture, stack, entry points — read by the planner |
| `CODE_STYLES.md` | Coding conventions, module layout, error handling — read by backend worker |
| `BRAND_STYLES.md` | UI/doc conventions — read by frontend and docs workers |
| `TESTING.md` | Test runner commands and layout — read by the test loop |

**Phase 1 — Dev Loop** takes a task description and runs it through a 7-stage graph:

```
task_ingestion → context_assembly → planner → [human_gate] → parallel workers
    → code_review_graph → review_gate → test_loop → artifact_update
```

Workers (backend, frontend, docs) run in parallel. Review and test failures retry automatically; repeated failures escalate to `user_elicitation`.

---

## Setup

**1. Clone and install dependencies**

```bash
git clone <repo-url>
cd LangGraph
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Create a `.env` file** in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enables LangSmith tracing
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=AI-WORKFLOW

# Optional — override the default model (claude-opus-4-6)
# ANTHROPIC_MODEL=claude-sonnet-4-6
```

> `ANTHROPIC_API_KEY` is required. All other variables are optional.

---

## Context7 MCP (JS framework doc fetching)

When ingesting a repo that uses Next.js, React, Prisma, or similar JS frameworks,
Phase 0 fetches live library documentation via [Context7](https://github.com/upstash/context7)
and injects it into the generated context files.

**Requires `npx` on PATH** — the ingestion pipeline spawns `npx @upstash/context7-mcp` automatically as a subprocess. No separate server to start.

**Python-only repos skip this step entirely.** If `npx` is unavailable or Context7 fails,
a warning is logged and the pipeline continues without library docs.

---

## Usage

### Phase 0 — Run ingestion on a repo

```bash
python scripts/run_ingestion.py --repo-path /path/to/your/repo
```

This writes `PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, and `TESTING.md` directly into the target repo. Run this once before starting the dev loop, and re-run whenever the codebase changes significantly.

To run it on this repo itself:

```bash
python scripts/run_ingestion.py --repo-path .
```

### Phase 1 — Run the dev loop

Pass a task as an inline JSON string:

```bash
python scripts/run_dev_loop.py --task '{"title":"add login endpoint","type":"feature","scope":"backend"}'
```

Or point to a JSON file:

```bash
python scripts/run_dev_loop.py --task task.json
```

The graph runs until the planner produces a plan, then **pauses for human approval** before dispatching workers. Type `y` to approve or `n` to abort.

**Resume a previous run** (graph state is checkpointed in SQLite):

```bash
python scripts/run_dev_loop.py --task task.json --thread-id <thread-id-from-previous-run>
```

**Use a custom checkpoint database:**

```bash
python scripts/run_dev_loop.py --task task.json --db /path/to/checkpoints.db
```

### Task JSON schema

```json
{
  "title": "short description of the task",
  "type": "feature | bugfix | refactor | docs",
  "scope": "backend | frontend | fullstack | docs"
}
```

---

## Running tests

```bash
pytest -v --asyncio-mode=auto
```

Tests that call the Anthropic API require a valid `ANTHROPIC_API_KEY` in `.env`.
