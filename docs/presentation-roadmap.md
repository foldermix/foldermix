# CLI Presentation And Documentation Roadmap

This roadmap tracks the `M3 CLI Presentation & Docs` milestone for `foldermix`.
The milestone is split into four PRs so planning, README work, docs-site expansion,
and CLI behavior changes can be reviewed independently.

## Milestone Goal

Make `foldermix` easier to evaluate, install, and trust as an LLM-context packing CLI.
The work should improve the path from "what is this?" to "I can safely generate the
context bundle I need" without expanding `foldermix` beyond folder packing.

## Positioning Principles

- Lead with the concrete job: pack a folder into one LLM-friendly artifact.
- Prefer runnable examples over feature claims.
- Separate evaluation docs from operating docs.
- Keep safety and determinism visible: sensitive-file skipping, preview commands,
  reports, and stable ordering are product strengths.
- Preserve existing output contracts unless a later PR explicitly proposes and tests a
  behavior change.

## Reference Evaluation Matrix

Use these projects as a checklist for specific patterns, not as generic inspiration.
Each follow-up PR should name which rows it used and what it deliberately avoided.

| Project | Inspect | Borrow For `foldermix` | Avoid |
|---|---|---|---|
| `repomix` | AI-context positioning, install-to-first-output flow, comparison language | A concise explanation of why context packing exists and where `foldermix` differs | Over-claiming parity with repo-specialized tools |
| `files-to-prompt` | Minimal examples, shell-friendly usage | A low-friction baseline example for users who want one command | A README that is too sparse for safety-sensitive document workflows |
| `uv` | First-screen structure, install clarity, docs hierarchy | Short install paths and a clear "recommended path" for extras | Turning install docs into a general Python packaging tutorial |
| `ruff` | Feature framing, diagnostics style, migration/confidence messaging | Clear promises around speed, determinism, and predictable behavior | Broad benchmark claims unless locally measured |
| `llm` | Recipes, shell composition, plugin-like workflow docs | Cookbook pages that show end-to-end LLM workflow usage | Making optional converters sound required for core use |
| `ripgrep` | Filtering examples and comparison framing | Concrete include/exclude examples and precise defaults | Dense option dumps before the user understands the workflow |
| `fd` | Friendly discovery docs and examples | Human-readable file-selection explanations | Hiding edge cases such as hidden files and gitignore behavior |
| `bat` | Terminal screenshots/transcripts and visual proof | Compact output transcripts or screenshots where they clarify behavior | Decorative visuals that do not show real `foldermix` output |
| `gh` | Command reference organization and workflow language | Task-oriented command docs and help examples | GitHub-specific assumptions in general CLI docs |
| `jq` | Machine-readable examples and pipelines | `jsonl` and `--report` examples users can pipe into other tools | Advanced query examples that distract from core packing workflows |

## Planned PR Split

### DOCS-PRES-1: Planning And Docs Roadmap

Purpose:
- Record the milestone as an explicit roadmap item.
- Capture the four-PR split so the work stays reviewable.
- Link the roadmap from contributor, agent, and docs-site entry points.

Deliverables:
- Canonical roadmap in `docs/presentation-roadmap.md`.
- Docs-site roadmap page with enough content to stand on its own.
- Links from `CONTRIBUTING.md`, `AGENTS.md`, `docs/agents.md`, and the docs site.
- GitHub milestone and PR metadata using `M3 CLI Presentation & Docs`.

Non-goals:
- No user-facing CLI behavior changes.
- No README presentation rewrite.
- No new screenshots, benchmarks, or command-output changes.

Acceptance criteria:
- The roadmap names all four PRs with stable `DOCS-PRES-*` notation.
- Each follow-up PR has deliverables, non-goals, validation, and acceptance criteria.
- The docs-site page does not send users to a main-branch repository blob as its primary
  content.
- Public user-facing docs avoid time-sensitive "current milestone" language.

Validation:
- `uv run --extra docs mkdocs build --strict`.
- `git diff --check`.
- Commit hook `pytest-fast`.

### DOCS-PRES-2: README Presentation Refresh

Purpose:
- Make the repository front page explain the tool faster and more concretely.
- Improve the first-screen path from install to useful output.
- Clarify who `foldermix` is for and when to use `md`, `xml`, or `jsonl`.

Deliverables:
- Revised README opening with:
  - one plain-language product sentence;
  - one copy-paste quickstart command;
  - a short "what you get" output example or transcript;
  - a concise list of the main safety guarantees.
- Install section with a clearly recommended default path and an extras decision table.
- Format guidance explaining when to choose Markdown, XML, and JSONL.
- A compact "common workflows" block that points to the deeper docs-site cookbook.
- Preserved maintainer/developer sections, moved lower or compressed when needed.

Non-goals:
- No CLI output or option behavior changes.
- No docs-site restructuring beyond links needed to keep navigation coherent.
- No performance or adoption claims without evidence in the PR.

Acceptance criteria:
- A new user can identify the tool's purpose and run a useful command within the first
  visible README section.
- Optional extras are explained without implying Homebrew supports them.
- Existing release, security, and maintainer information remains discoverable.
- The README does not duplicate long command-reference material that belongs in the docs
  site.

Validation:
- Link and anchor sanity check for changed README sections.
- `uv run --extra docs mkdocs build --strict` if docs-site links are changed.

### DOCS-PRES-3: Docs Site And Cookbook Expansion

Purpose:
- Turn the docs site from a one-page reference into a practical workflow guide while
  keeping it compact.
- Give users copy-pasteable recipes for common `foldermix` jobs.

Deliverables:
- MkDocs navigation for at least:
  - Quickstart;
  - Workflows;
  - Configuration;
  - Output formats and reports;
  - Safety and troubleshooting.
- Cookbook recipes for:
  - AI context packing;
  - legal review bundles;
  - research corpus bundles;
  - support incident bundles;
  - course refresh bundles;
  - config-first workflows;
  - machine-readable reports and `jsonl` pipelines.
- Each recipe must include:
  - when to use it;
  - command sequence;
  - expected artifact;
  - relevant safety or filtering note.
- README links to the docs-site pages instead of duplicating recipe details.

Non-goals:
- No CLI output or option behavior changes.
- No broad redesign or custom theme work.
- No claims that optional converters are installed by default.

Acceptance criteria:
- `mkdocs build --strict` passes.
- Every new page is reachable from `mkdocs.yml` navigation.
- The docs site is useful without reading the full README first.
- Workflow pages use real `foldermix` commands and current option names.

Validation:
- `uv run --extra docs mkdocs build --strict`.
- Link and anchor sanity check.

### DOCS-PRES-4: CLI Output And Help Presentation

Purpose:
- Improve the terminal experience for discovery, preview, and trust-building commands.
- Make include/skip decisions easier to inspect before users generate context bundles.

Deliverables:
- Review and refine command help text for `pack`, `list`, `skiplist`, `preview`,
  `stats`, `init`, and `version`.
- Add help examples or command epilogues only where Typer/Rich can present them cleanly.
- Improve readable output for `list`, `skiplist`, `stats`, and dry-run style flows where
  the current output makes include/skip decisions hard to inspect.
- Preserve machine-readable output and report schemas unless an intentional schema change
  is separately documented.
- Update README/docs-site examples affected by any output or terminology change.

Non-goals:
- No new output format.
- No new converter stack.
- No dependency addition unless the PR explicitly justifies it and proves it is needed;
  prefer the existing Typer/Rich stack.
- No breaking change to report JSON, JSONL bundle output, or scanner ordering.

Acceptance criteria:
- Help text remains accurate for every changed option.
- Human-readable output is easier to scan while staying deterministic.
- Tests cover changed help/output behavior.
- Any snapshot or integration fixture changes are intentional and explained in the PR.

Validation:
- `ruff check .`.
- `ruff format --check .`.
- `pytest -m "not integration and not slow" -o addopts=`.
- Integration/snapshot tests only when changed output requires them.

## Coordination Rules

- Keep each PR independently reviewable and mergeable.
- Do not bundle CLI output changes into docs-only PRs.
- Update README and docs when any CLI-facing behavior or terminology changes.
- Preserve sensitive-file protections and deterministic output ordering throughout the
  milestone.
- Use the `DOCS-PRES-*` notation in PR titles and the PR body's planning notation
  section.
- Treat each PR as incomplete until it satisfies the repository PR completion gate:
  labeled, non-draft, detailed description, and milestone assignment when available.
