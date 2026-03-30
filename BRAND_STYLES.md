# BRAND_STYLES.md

## UI Framework & Component Library

This project has **no frontend or UI layer**. It is a pure backend/CLI Python application — a multi-agent orchestration system built on LangGraph. There are no web frameworks, component libraries, or client-side rendering technologies in use.

---

## Styling Approach

Not applicable. The project contains no CSS, design tokens, theming configuration, or visual styling of any kind. All output is either:

- **Structured markdown files** (PROJECT.md, CODE_STYLES.md, BRAND_STYLES.md, TESTING.md) consumed by AI agents
- **Terminal/CLI output** from script execution and test runners

---

## Tone & Voice

### Documentation Tone

- **Technical and direct.** Markdown context files are written for consumption by AI agents, not end users. Prioritize precision and completeness over friendliness.
- **Declarative.** State what the system does and how, not what it "tries to" or "aims to" do.
- **Structured.** Use headers, tables, and code blocks liberally. Avoid long prose paragraphs — prefer bullet points and short declarative sentences.
- **Context-aware.** Every generated markdown file assumes the reader (human or AI) needs to act on the information immediately. Include concrete file paths, command examples, and technology versions where relevant.

### Naming & Terminology

| Term | Usage |
|---|---|
| **Dev loop** | The primary LangGraph-based orchestration cycle (not "development loop" or "dev cycle") |
| **Phase 0** / **Ingestion pipeline** | The one-time bootstrap analysis phase |
| **Node** | A single step/agent in the LangGraph graph |
| **State** | The Pydantic-modeled data object passed between nodes |
| **Context files** / **MD files** | The generated markdown files that carry shared knowledge between agents |

---

## Typography & Colour

Not applicable for runtime UI. For generated markdown and documentation:

- Use **ATX-style headers** (`#`, `##`, `###`) — not setext (underline) style.
- Use **fenced code blocks** with language identifiers (` ```python `, ` ```bash `, ` ```json `).
- Use **pipe tables** for structured comparisons and reference data.
- Use **bold** for key terms on first introduction; avoid italic for emphasis (reserve italic for file paths or variable names only if not using backticks).
- Wrap all file names, module paths, CLI commands, environment variables, and code references in **backtick inline code** (e.g., `src/nodes/dev_loop/`, `pytest`, `ANTHROPIC_API_KEY`).

---

## Component Conventions

There are no UI components. The analogous organizational unit is the **graph node**:

- Node implementations live under `src/nodes/`, organized by function (e.g., `src/nodes/dev_loop/`).
- Each node is an **async Python function** that receives and returns the shared Pydantic state object.
- Node files should be named descriptively for their responsibility (planning, implementation, validation).
- Tests colocate with source where appropriate (`test_loop.py` alongside loop logic) and also exist in the top-level `tests/` directory.

### Documentation File Conventions

| File | Purpose | Audience |
|---|---|---|
| `PROJECT.md` | Architecture, tech stack, data flow, entry points | All agents |
| `CODE_STYLES.md` | Code patterns, formatting, module structure | Implementation agent |
| `BRAND_STYLES.md` | Documentation style, tone, terminology (this file) | Docs agent, frontend agent |
| `TESTING.md` | Test commands, frameworks, coverage expectations | Validation agent |

All context markdown files live at the **repository root**.

---

## Accessibility

Not applicable — no user-facing UI exists. For documentation accessibility:

- Use descriptive link text (not "click here").
- Provide `alt`-equivalent descriptions in any markdown diagrams (e.g., ASCII flow diagrams should be preceded by a brief prose summary of the flow).
- Maintain a logical heading hierarchy (no skipping from `##` to `####`).
- Keep table content concise so it remains parseable by screen readers and AI agents alike.