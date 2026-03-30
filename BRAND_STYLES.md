# BRAND_STYLES.md

## UI Framework & Component Library

This project has **no frontend or UI layer**. It is a pure backend/CLI Python application — a multi-agent orchestration system built on LangGraph. There are no web frameworks, component libraries, or client-side rendering technologies in use.

If a frontend or docs site is added in the future, this file should be updated with the chosen framework, component library, and design system details.

---

## Styling Approach

Not applicable. The project contains no CSS, design tokens, theming configuration, or visual styling of any kind. All output is either:

- **Structured markdown files** (`PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, `TESTING.md`) consumed by AI agents
- **Terminal/CLI output** from script execution and test runners

---

## Tone & Voice

### Documentation Tone

- **Technical and direct.** Markdown context files are written for consumption by AI agents, not end users. Prioritize precision and completeness over friendliness.
- **Declarative.** State what the system does and how, not what it "tries to" or "aims to" do.
- **Structured.** Use headers, tables, and code blocks liberally. Avoid long prose paragraphs — prefer bullet points and short declarative sentences.
- **Context-aware.** Every generated markdown file assumes the reader (human or AI) needs to act on the information immediately. Include concrete file paths, command examples, and technology versions where relevant.

### README & User-Facing Copy

- The README uses a **concise, instructional tone** — short setup steps, tables for structure, and inline code blocks for commands.
- Avoid marketing language. Describe capabilities factually.
- Use second person ("you") sparingly; prefer imperative mood for instructions ("Clone the repo", "Create a `.env` file").

### Naming & Terminology

| Term | Usage |
|---|---|
| **Dev loop** | The primary LangGraph-based orchestration cycle. Do not use "development loop" or "dev cycle". |
| **Phase 0** / **Ingestion** | The one-time bootstrap pipeline that analyzes a repo and generates context files. Use interchangeably. |
| **Phase 1** | The persistent dev loop. Refer to it as "the dev loop" in most contexts; use "Phase 1" only when contrasting with Phase 0. |
| **Context files** | The four generated markdown files (`PROJECT.md`, `CODE_STYLES.md`, `BRAND_STYLES.md`, `TESTING.md`). Do not call them "config files" or "templates". |
| **Human gate** | The approval checkpoint before code is written. Do not call it "human-in-the-loop" generically — be specific about where it occurs. |
| **Node** | A single step in the LangGraph graph. Do not use "stage" or "step" as synonyms when referring to graph structure. |
| **Worker** | One of the parallel execution agents (backend, frontend, docs). Always specify which worker when context requires it. |

---

## Typography & Colour

No typographic or colour conventions exist in the project. All output is plain markdown rendered by whatever viewer the consumer uses (GitHub, IDE preview, terminal).

### Markdown Formatting Conventions

- **Headings**: Use `##` for top-level sections within a context file, `###` for subsections. Reserve `#` for the file title only.
- **Code blocks**: Always specify the language identifier (` ```python `, ` ```bash `, ` ```env `). Never use bare fenced blocks.
- **Tables**: Preferred over nested bullet lists when presenting structured key-value or multi-column data.
- **Emphasis**: Use **bold** for terms being defined or key nouns on first reference. Use `inline code` for file names, paths, commands, environment variables, and class/function names. Avoid italics.

---

## Component Conventions

Not applicable — no UI components exist. If a frontend is introduced, document the following here:

- Component file structure and naming pattern
- Props/typing conventions
- Composition and slot patterns
- State management approach

For the current codebase, the analogous conventions for **graph nodes and agents** are documented in `CODE_STYLES.md`.

---

## Accessibility

Not applicable — no user-facing interface exists. If a frontend or web-based dashboard is added, this section should define:

- Target WCAG conformance level (e.g., WCAG 2.1 AA)
- Semantic HTML requirements
- Keyboard navigation standards
- Screen reader testing expectations
- Colour contrast minimums