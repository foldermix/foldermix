# CLI Presentation Roadmap

This page summarizes the `M3 CLI Presentation & Docs` milestone. The detailed source
of truth lives in the repository at `docs/presentation-roadmap.md`; this published page
keeps the reviewable PR split visible from the docs site without requiring readers to
jump to GitHub for the basic plan.

## Goal

Make `foldermix` easier to evaluate, install, and trust as an LLM-context packing CLI.
The milestone improves presentation and documentation without expanding `foldermix`
beyond folder packing.

## Principles

- Lead with the concrete job: pack a folder into one LLM-friendly artifact.
- Prefer runnable examples over feature claims.
- Separate evaluation docs from operating docs.
- Keep safety and determinism visible: sensitive-file skipping, preview commands,
  reports, and stable ordering.
- Preserve output contracts unless a later PR explicitly proposes and tests a behavior
  change.

## Reference Projects

The milestone uses prominent CLI tools as pattern references:

| Project | Borrow | Avoid |
|---|---|---|
| `repomix` | AI-context positioning and first-output flow | Over-claiming parity with repo-specialized tools |
| `files-to-prompt` | Minimal shell-friendly examples | Docs that are too sparse for safety-sensitive workflows |
| `uv` | Install clarity and first-screen structure | A general Python packaging tutorial |
| `ruff` | Clear promises around speed and deterministic behavior | Benchmark claims without local evidence |
| `llm` | Recipe-driven workflows | Making optional converters sound required |
| `ripgrep` and `fd` | Precise filtering examples | Dense option dumps before workflow context |
| `bat` | Useful terminal transcripts or screenshots | Decorative visuals that do not show real output |
| `gh` and `jq` | Command-reference structure and machine-readable examples | Domain-specific assumptions that do not fit `foldermix` |

## PR Split

### DOCS-PRES-1: Planning And Docs Roadmap

Records this roadmap, links it from contributor and agent docs, and keeps the docs-site
version useful on its own. It does not change CLI behavior or rewrite the README.

Acceptance criteria:
- Stable `DOCS-PRES-*` notation exists.
- Follow-up PRs have deliverables, non-goals, validation, and acceptance criteria.
- Public docs avoid time-sensitive "current milestone" language.

### DOCS-PRES-2: README Presentation Refresh

Refreshes the README opening, install guidance, format guidance, and short workflow
entry points.

Acceptance criteria:
- A new user can identify the purpose and run a useful command from the first visible
  README section.
- Optional extras are clear without implying Homebrew supports them.
- Maintainer, security, and release details remain discoverable.

### DOCS-PRES-3: Docs Site And Cookbook Expansion

Expands the docs site into a compact workflow guide with cookbook recipes for AI context
packing, legal review, research corpora, support incidents, course refreshes,
config-first workflows, and machine-readable reports.

Acceptance criteria:
- `mkdocs build --strict` passes.
- Every new page is reachable from navigation.
- Recipes use real `foldermix` commands and current option names.

### DOCS-PRES-4: CLI Output And Help Presentation

Improves command help and human-readable output for discovery, preview, and trust-building
commands while preserving machine-readable contracts.

Acceptance criteria:
- Help text remains accurate for changed options.
- Output changes are deterministic and covered by tests.
- Report JSON, JSONL bundle output, and scanner ordering stay backward compatible unless
  explicitly changed and documented.

## Coordination Rules

- Keep each PR independently reviewable and mergeable.
- Keep docs-only PRs separate from CLI behavior changes.
- Update README and docs when CLI-facing terminology or behavior changes.
- Preserve sensitive-file protections and deterministic output ordering.
