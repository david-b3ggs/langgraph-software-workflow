# Multi-Agent Software Development Loop — LangGraph Implementation Context

## Overview

This document captures the full design of a multi-agent software development orchestration loop, intended as implementation context for a LangGraph (TypeScript or Python) build. It includes the ingestion bootstrap pipeline, architecture decisions, agent responsibilities, state schema, retry/failure logic, checkpointing strategy, and code sketches.

---

## Phase 0 — Ingestion Pipeline (Bootstrap)

Runs **once per repo**, before the dev loop is active. Solves the cold-start problem: analyzes an existing codebase and auto-generates all MD context files the dev loop depends on. If the MD files already exist and are current, this phase is skipped.

### Flow

```
Start
  ├─→ Analyze repo for README and existing markdown files  (parallel)
  └─→ Analyze structure, DB schema, frameworks, tests      (parallel)
            └─→ Fetch docs if needed
                      └─→ Generate Planner.MD (PROJECT.md equivalent)
                                ├─→ Generate BackEnd.MD     (parallel)
                                ├─→ Generate FrontEnd.MD    (parallel)
                                └─→ Generate DocsAgent.MD   (parallel)
                                          └─→ → Start dev loop
```

### Stage Descriptions

**Parallel Analysis (two tracks fire simultaneously):**
- *Track A* — Scan repo for existing `README`, markdown files, and any prior context docs. Extract project description, tech stack mentions, setup instructions.
- *Track B* — Analyze codebase structure: directory layout, DB schema files (migrations, ORM models), framework detection (Go modules, package.json, etc.), and existing test structure.

**Fetch Docs (conditional):**
- If framework or library versions are detected that require external docs (e.g., specific versions of a router, ORM, or UI library), fetch relevant documentation pages.
- Gate: only fires if Track B surfaces unrecognized or version-specific dependencies.

**Generate Planner.MD:**
- Synthesizes both analysis tracks + any fetched docs into a single `PROJECT.md`-equivalent file.
- Contains: project purpose, architecture overview, key frameworks and versions, languages, inter-service relationships, dev cycle notes.
- This becomes the Planner Agent's primary context file for all future tasks.

**Generate BackEnd.MD / FrontEnd.MD / DocsAgent.MD (parallel fan-out):**
- Each is a specialized context file derived from the Planner.MD + relevant analysis output.
- `BackEnd.MD` → maps to `CODE_STYLES.md` — inferred code patterns, API conventions, DB access patterns, testing structure.
- `FrontEnd.MD` → maps to `BRAND_STYLES.md` — inferred UI component patterns, styling conventions, design tokens if present.
- `DocsAgent.MD` → maps to `TESTING.md` — inferred test runner commands, test file locations, integration test entry points.

### LangGraph State Extension for Ingestion

```python
class IngestionState(TypedDict):
    repo_path: str
    existing_md: dict[str, str]       # filename → content, from Track A
    repo_structure: dict              # from Track B: dirs, schema, frameworks, tests
    fetched_docs: dict[str, str]      # url → content, conditional
    planner_md: str                   # generated PROJECT.md
    backend_md: str                   # generated CODE_STYLES.md
    frontend_md: str                  # generated BRAND_STYLES.md
    docs_agent_md: str                # generated TESTING.md
    ingestion_complete: bool
```

### LangGraph Ingestion Graph Sketch

```python
ingestion_graph = StateGraph(IngestionState)

ingestion_graph.add_node("analyze_markdown",   analyze_existing_markdown_node)
ingestion_graph.add_node("analyze_structure",  analyze_codebase_structure_node)
ingestion_graph.add_node("fetch_docs",         fetch_docs_node)             # conditional
ingestion_graph.add_node("generate_planner",   generate_planner_md_node)
ingestion_graph.add_node("generate_backend",   generate_backend_md_node)
ingestion_graph.add_node("generate_frontend",  generate_frontend_md_node)
ingestion_graph.add_node("generate_docs",      generate_docs_agent_md_node)
ingestion_graph.add_node("write_md_files",     write_md_files_to_repo_node)

# Parallel analysis tracks — use a fan-out then merge node
ingestion_graph.set_entry_point("analyze_markdown")  # fire both via asyncio.gather
ingestion_graph.add_edge("analyze_markdown",  "fetch_docs")
ingestion_graph.add_edge("analyze_structure", "fetch_docs")

# Conditional: fetch docs only if unrecognized deps found
ingestion_graph.add_conditional_edges("fetch_docs", route_fetch_docs, {
    "needed":     "generate_planner",
    "skip":       "generate_planner",
})

ingestion_graph.add_edge("generate_planner", "generate_backend")   # fan-out via gather
ingestion_graph.add_edge("generate_planner", "generate_frontend")
ingestion_graph.add_edge("generate_planner", "generate_docs")
ingestion_graph.add_edge("generate_backend",  "write_md_files")
ingestion_graph.add_edge("generate_frontend", "write_md_files")
ingestion_graph.add_edge("generate_docs",     "write_md_files")
ingestion_graph.add_edge("write_md_files",    END)
```

### Parallel execution inside nodes (both tracks, and the MD fan-out):

```python
async def run_ingestion(repo_path: str):
    # Track A and Track B in parallel
    track_a, track_b = await asyncio.gather(
        analyze_existing_markdown(repo_path),
        analyze_codebase_structure(repo_path),
    )
    # ... rest of ingestion pipeline

async def generate_agent_mds(planner_md: str, structure: dict):
    backend_md, frontend_md, docs_md = await asyncio.gather(
        generate_backend_md(planner_md, structure),
        generate_frontend_md(planner_md, structure),
        generate_docs_agent_md(planner_md, structure),
    )
    return backend_md, frontend_md, docs_md
```

### Integration with Dev Loop

After ingestion completes, `write_md_files_to_repo_node` commits the four generated MD files to the repo. The dev loop's Stage 1 (Context Assembly) then reads these files as if they were manually authored — no special handling required. On subsequent runs, the ingestion phase checks file freshness (hash comparison) and skips if current.

---

## Repository Structure Assumptions

Every repo participating in this loop contains the following MD files, which serve as the "constitution" for each agent. They are versioned alongside code and the orchestrator pins the version used in each run. These are either **manually authored** or **auto-generated by the Ingestion Pipeline** above.

| File | Purpose | Ingestion Source |
|---|---|---|
| `PROJECT.md` | Project purpose, architecture, frameworks, languages, dev cycle notes | Generated from Planner.MD step |
| `TESTING.md` | How to run tests locally — unit tests and black-box integration tests. Updated at task completion. | Generated from DocsAgent.MD step |
| `BRAND_STYLES.md` | UI styling guidelines — colors, typography, component patterns | Generated from FrontEnd.MD step |
| `CODE_STYLES.md` | Code architecture standards, patterns, naming conventions | Generated from BackEnd.MD step |

---

## Workflow Stages

### Stage 0 — Task Ingestion
- Input: GitHub issue, Jira ticket, or plain natural language prompt
- Output: Normalized `TaskSpec` — `{ title, type: "feature"|"bug"|"refactor", scope: "frontend"|"backend"|"both"|"infra" }`
- Handled entirely by deterministic orchestrator code, no LLM call

### Stage 1 — Context Assembly
- Selectively loads and **compresses** MD files per agent based on task type
- Compression: summarize + strip irrelevant sections to fit token budget
- Each agent receives only what it needs (see Context Matrix below)
- Token budget threshold check — if combined MD exceeds budget, run a summarization pass before injection

**Context Matrix:**

| Agent | MD Files Injected |
|---|---|
| Planner | `PROJECT.md` |
| Backend Agent | `PROJECT.md` + `CODE_STYLES.md` |
| Frontend Agent | `PROJECT.md` + `BRAND_STYLES.md` + `CODE_STYLES.md` |
| Docs Agent | `TESTING.md` + task spec |
| Review Gate | `CODE_STYLES.md` + `BRAND_STYLES.md` (for UI tasks) |
| Test Agent | `TESTING.md` + task spec + generated code diffs |

### Stage 2 — Planner Agent (LLM)
- Input: `TaskSpec` + compressed `PROJECT.md`
- Output: Structured JSON dependency graph of subtasks
- Schema: `{ id, type: "backend"|"frontend"|"docs"|"migration", depends_on: string[], context_hint: string }[]`
- Migration scope is **folded into the planner output** — migration subtasks are tagged and distributed to BE or FE workers as annotated subtasks, not a separate agent
- Orchestrator **validates plan against schema** before proceeding. On malformed output: retry planner up to 2×, then halt.

### Stage 2b — Human Gate (HITL)
- Planner output is surfaced to the engineer for review/modification before execution unlocks
- **Checkpoint 1** is written immediately after human approval
- In LangGraph: use `interrupt_before=["human_gate"]` — graph pauses, caller surfaces state
- Resume: `app.invoke({"human_approved": True}, config={"thread_id": task_id})`

### Stage 3 — Parallel Execution (Worker Tier)
Workers are fired in parallel based on the dependency graph from the planner. Independent subtasks run concurrently; dependent ones wait on their `depends_on` edges.

**Workers:**
- **Backend Agent** — handles Go/API code + any migration subtasks tagged from planner
- **Frontend Agent** — handles React/UI code using Brand + Code MD
- **Docs Agent** — updates READMEs, inline comments, `TESTING.md` patterns

Each worker receives:
- Its subtask spec
- Relevant compressed MD context
- Upstream artifacts (e.g., Frontend waits on Backend's API contract)

Each worker produces:
- Code diff
- List of modified file paths
- Brief rationale

**Checkpoint 2** is written per-worker on the collect bus (not a single collect-level save — if BE passes but FE fails, resume from BE's saved output).

### Stage 4 — Code Review Graph (Token Conservation)
- Builds a call/import dependency graph from the combined worker diffs
- Changed files = root nodes; direct callers and callees = neighbor nodes
- Only this subgraph is serialized into the CodeRabbit review prompt
- On a large monorepo this cuts review context by 70–90%
- Implementation: parse git diff → build NetworkX (Python) or custom graph (TS) of repo call/import relationships → extract neighborhood of changed files

### Stage 5 — Review Gate (CodeRabbit via Orchestration Layer)
- CodeRabbit lives in the orchestration layer, not as a separate agent
- Validates against `CODE_STYLES.md` and `BRAND_STYLES.md` (for UI diffs)
- Output: `{ passed: bool, feedback: LineAnnotation[] }`
- On **fail**: inject feedback into the responsible worker, retry. Cap: **2 retries**
- On **cap hit**: route to User Elicitation (see Failure Handling)

**Checkpoint 3** written after review passes.

### Stage 6 — Test Loop
Two responsibilities:
1. Write or update unit tests for generated code
2. Run existing integration test suite from `TESTING.md` against new code

On **test failure**: send structured failure report to responsible worker for targeted fix + retest. This is a tight inner loop — no full replanning, just fix + retest. Cap: **3 cycles**

On **consecutive cap hit**: route to User Elicitation.

**Checkpoint 4** written after tests pass.

### Stage 7 — Artifact Update
- Docs Agent updates `TESTING.md` if new test patterns were introduced
- Commits all code changes
- Logs full run trace: every prompt, response, tool call, retry, latency
- Marks task complete

---

## Failure Handling

### Retry Logic
| Gate | Max Retries | On Cap Hit |
|---|---|---|
| Planner schema validation | 2 | Halt — malformed plan |
| Review Gate (CodeRabbit) | 2 | User Elicitation |
| Test Loop | 3 | User Elicitation |

### User Elicitation (Human-in-the-Loop on Failure)
Triggered when any retry cap is hit. The orchestrator halts and surfaces a structured escalation artifact:
- Which worker failed
- Reviewer/test output from the last N retries
- Diff history across retry attempts
- Engineer choices: edit task spec and re-queue, manually patch and resume from nearest checkpoint, or abort

This is a **first-class output**, not an error state. The graph routes to a `user_elicitation` node explicitly.

### Escalation Artifact
On persistent failure, the orchestrator produces:
- Draft PR with failure annotations
- Structured failure report (last retry diff, test/review output)
- Suggested next steps

---

## Checkpointing Strategy

| Checkpoint | Location | What's Saved |
|---|---|---|
| **Checkpoint 1** | After human approves plan | Approved plan JSON, task spec, MD versions used |
| **Checkpoint 2** | Per-worker on collect bus | Individual worker output, file diffs, rationale |
| **Checkpoint 3** | After review gate passes | Reviewed diffs, CodeRabbit annotations (passed) |
| **Checkpoint 4** | After test loop passes | Test results, final diffs, ready-to-commit state |

Checkpoint 2 is intentionally **per-worker** — if BE passes but FE fails, resume from BE's saved output, not scratch.

---

## LangGraph State Schema

```python
from typing import TypedDict, Literal

class SubTask(TypedDict):
    id: str
    type: Literal["backend", "frontend", "docs"]
    depends_on: list[str]
    context_hint: str
    migration_scope: str | None  # folded in from planner

class WorkerOutput(TypedDict):
    agent: str
    diff: str
    modified_files: list[str]
    rationale: str
    passed_review: bool

class ReviewResult(TypedDict):
    passed: bool
    feedback: list[dict]  # LineAnnotation list

class TestResult(TypedDict):
    passed: bool
    failures: list[dict]
    retry_count: int

class DevLoopState(TypedDict):
    # Task
    task: dict                        # TaskSpec
    plan: list[SubTask] | None

    # HITL
    human_approved: bool

    # Execution
    worker_outputs: dict[str, WorkerOutput]
    review_subgraph: list[str]        # impacted file list from Code Review Graph

    # Gates
    review_result: ReviewResult | None
    test_result: TestResult | None

    # Retry counters
    review_retry_count: int
    test_retry_count: int

    # Escalation
    escalated: bool
    escalation_context: dict | None

    # MD versions (pinned per run)
    md_versions: dict[str, str]
```

---

## LangGraph Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

graph = StateGraph(DevLoopState)

# Nodes
graph.add_node("task_ingestion",      task_ingestion_node)
graph.add_node("context_assembly",    context_assembly_node)    # compression here
graph.add_node("planner",             planner_node)
graph.add_node("human_gate",          human_gate_node)
graph.add_node("parallel_workers",    parallel_workers_node)    # asyncio.gather inside
graph.add_node("code_review_graph",   build_review_subgraph_node)
graph.add_node("review_gate",         coderabbit_review_node)
graph.add_node("test_loop",           test_loop_node)
graph.add_node("artifact_update",     artifact_update_node)
graph.add_node("user_elicitation",    user_elicitation_node)

# Linear edges
graph.set_entry_point("task_ingestion")
graph.add_edge("task_ingestion",   "context_assembly")
graph.add_edge("context_assembly", "planner")
graph.add_edge("planner",          "human_gate")
graph.add_edge("human_gate",       "parallel_workers")
graph.add_edge("parallel_workers", "code_review_graph")
graph.add_edge("code_review_graph","review_gate")
graph.add_edge("artifact_update",  END)
graph.add_edge("user_elicitation", END)   # engineer takes over from here

# Conditional: review gate routing
graph.add_conditional_edges("review_gate", route_review, {
    "pass":            "test_loop",
    "retry_worker":    "parallel_workers",   # re-enter worker tier with feedback
    "elicitate":       "user_elicitation",
})

# Conditional: test loop routing
graph.add_conditional_edges("test_loop", route_test, {
    "pass":            "artifact_update",
    "retry_worker":    "parallel_workers",   # targeted fix, no replanning
    "elicitate":       "user_elicitation",
})

# Human-in-the-loop interrupt
graph.interrupt_before = ["human_gate"]

# Checkpointing — automatic per node
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = graph.compile(checkpointer=checkpointer, interrupt_before=["human_gate"])
```

---

## Routing Functions

```python
def route_review(state: DevLoopState) -> str:
    r = state["review_result"]
    if r and r["passed"]:
        return "pass"
    if state["review_retry_count"] >= 2:
        return "elicitate"
    return "retry_worker"

def route_test(state: DevLoopState) -> str:
    t = state["test_result"]
    if t and t["passed"]:
        return "pass"
    if state["test_retry_count"] >= 3:
        return "elicitate"
    return "retry_worker"
```

---

## Key Node Implementations (Sketches)

### context_assembly_node
```python
async def context_assembly_node(state: DevLoopState) -> dict:
    task = state["task"]
    md_map = load_md_files()  # load PROJECT, TESTING, BRAND_STYLES, CODE_STYLES

    # Pin MD versions for this run
    md_versions = {k: hash_file(v) for k, v in md_map.items()}

    # Compress: strip irrelevant sections per task scope
    compressed = compress_md_for_task(md_map, task["scope"], token_budget=4000)

    return {"md_versions": md_versions, "compressed_md": compressed}
```

### parallel_workers_node
```python
async def parallel_workers_node(state: DevLoopState) -> dict:
    plan = state["plan"]
    review_feedback = state.get("review_result", {}).get("feedback", [])

    # Respect dependency graph — fire independent tasks in parallel
    ready_tasks = get_ready_tasks(plan, state["worker_outputs"])

    results = await asyncio.gather(*[
        run_worker_agent(task, state, review_feedback)
        for task in ready_tasks
    ])

    outputs = {r["agent"]: r for r in results}
    return {"worker_outputs": {**state["worker_outputs"], **outputs}}
```

### build_review_subgraph_node
```python
def build_review_subgraph_node(state: DevLoopState) -> dict:
    all_diffs = [o["diff"] for o in state["worker_outputs"].values()]
    changed_files = extract_changed_files(all_diffs)

    # Build call/import graph and extract neighborhood
    repo_graph = build_repo_call_graph(".")
    impacted = get_impacted_subgraph(repo_graph, changed_files, depth=1)

    return {"review_subgraph": impacted}
```

### user_elicitation_node
```python
async def user_elicitation_node(state: DevLoopState) -> dict:
    # Surface structured failure context to engineer
    escalation = {
        "trigger":          "review_cap" if state["review_retry_count"] >= 2 else "test_cap",
        "last_diff":        get_last_diff(state),
        "failure_output":   state.get("review_result") or state.get("test_result"),
        "retry_history":    build_retry_history(state),
        "options": [
            "edit_task_spec",           # re-queue with modified spec
            "resume_from_checkpoint",   # manually patch + resume
            "abort"
        ]
    }
    # Notify engineer (webhook, Slack, email — implementation-specific)
    await notify_engineer(escalation)
    return {"escalated": True, "escalation_context": escalation}
```

---

## Invocation and Resume Patterns

```python
# Initial run
thread_config = {"configurable": {"thread_id": task_id}}
result = await app.ainvoke({"task": task_spec, "human_approved": False}, config=thread_config)
# Graph pauses at human_gate — surface plan to engineer

# After engineer approves plan
result = await app.ainvoke({"human_approved": True}, config=thread_config)

# Resume from checkpoint after elicitation (engineer patched something)
# LangGraph replays from the last saved checkpoint automatically
result = await app.ainvoke(
    {"task": updated_task_spec},  # optionally updated spec
    config=thread_config
)
```

---

## Design Principles

1. **Orchestrator is deterministic code** — the LLM does cognitive work (planning, writing, reviewing). The orchestrator does coordination (routing, sequencing, state, retries). Never mix these.

2. **MD files are the agent constitution** — versioned alongside code, pinned per run, injected selectively.

3. **Shared state store** — agents don't call each other. They read/write to the state dict managed by the orchestrator. Every run is reproducible from a state snapshot.

4. **Structured outputs at all boundaries** — JSON/schema-validated output between every stage. Free text only inside agent reasoning.

5. **Escalation is a first-class output** — cap hits produce structured artifacts, not crashes. Human-in-the-loop is designed in.

6. **Checkpoint 2 is per-worker** — granular enough to resume individual worker failures without re-running the full parallel tier.

7. **Code Review Graph is token conservation, not an LLM** — it's a graph traversal on the repo's call/import structure. The LLM only sees the subgraph, not the full codebase.

---

## LangGraph vs Mastra vs Claude Code Agents — Decision Summary

| Concern | LangGraph | Mastra | Claude Code Agents |
|---|---|---|---|
| Language | Python + TypeScript | TypeScript only | Prompt + MCP tools (any) |
| State modeling | Typed StateGraph | Typed workflow steps | Orchestrator working memory |
| Checkpointing | Automatic per-node | Built-in suspend/resume | Manual MCP tool calls |
| Human-in-loop | `interrupt_before` | Suspend indefinitely + resume via API | Blocking MCP tool |
| Evals / observability | LangSmith (external) | Built-in evals + tracing | External |
| MCP authoring | Consume only | Author + expose MCP servers | Consume + author |
| Go interop | Separate TS/Python runtime → Go APIs | Separate TS runtime → Go APIs | MCP servers can be Go-native |
| Boilerplate | High | Medium | Low |

**Recommended path for a Go-primary stack:** Start with Mastra (Studio + evals are high-value during build phase), expose Go services as MCP tools, expose the Mastra orchestrator itself as an MCP server for Claude Code to consume.
