# CLI Presentation And Documentation Roadmap

This roadmap is the next documentation and CLI presentation milestone for `foldermix`.
It tracks a focused sequence of four PRs that improve how the project explains itself,
how users discover practical workflows, and how the terminal experience presents scan
and pack decisions.

## Milestone Goal

Make `foldermix` easier to evaluate, install, and trust as an LLM-context packing CLI.
The work should learn from prominent CLI projects without copying their voice or
turning `foldermix` into a broader tool than it is.

Reference projects to study:

- `repomix` and `files-to-prompt` for AI-context positioning and direct comparisons.
- `uv` and `ruff` for crisp installation, quickstart, feature framing, and docs hierarchy.
- `llm` for plugin-like workflows, shell composition, and examples-first docs.
- `ripgrep`, `fd`, and `bat` for practical command examples, readable filtering docs,
  and visual terminal presentation.
- `gh` and `jq` for command reference structure, workflow recipes, and machine-readable
  output examples.

## Planned PR Split

### PR 1: DOCS-PRES-1: Planning And Docs Roadmap

Purpose:
- Record the milestone as an explicit roadmap item.
- Capture the four-PR split so the work stays reviewable.
- Link the roadmap from contributor, agent, README, and docs-site entry points.

Scope:
- Planning docs only.
- No user-facing CLI behavior changes.
- No README rewrite beyond short references to this roadmap.

Validation:
- Markdown/docs build check when docs dependencies are available.
- No Python test run required unless touched files expand beyond docs.

### PR 2: DOCS-PRES-2: README Presentation Refresh

Purpose:
- Make the repository front page explain the tool faster and more concretely.
- Improve the first-screen path from install to useful output.
- Clarify who `foldermix` is for and when to use `md`, `xml`, or `jsonl`.

Scope:
- Tighten the README title, tagline, quickstart, install matrix, and feature framing.
- Add compact examples that show input folder, command, and resulting artifact.
- Keep existing operational and maintainer details, but move or compress material if the
  README becomes too long for first-time evaluation.

Borrowed patterns:
- `uv` and `ruff`: concise top section and installation clarity.
- `repomix` and `files-to-prompt`: AI-context language and direct, concrete examples.
- `bat`: visual or transcript-style demonstration near the top when practical.

Validation:
- Link/anchor sanity check.
- Docs build if README content is imported by the docs site.

### PR 3: DOCS-PRES-3: Docs Site And Cookbook Expansion

Purpose:
- Turn the docs site from a one-page reference into a practical workflow guide while
  keeping it compact.
- Give users copy-pasteable recipes for common `foldermix` jobs.

Scope:
- Add docs-site pages or sections for:
  - AI context packing.
  - Legal review bundles.
  - Research corpus bundles.
  - Support incident bundles.
  - Course refresh bundles.
  - Config-first workflows.
  - Machine-readable reports and `jsonl` output.
- Keep the README and docs site complementary: README for evaluation, docs site for use.
- Update `mkdocs.yml` navigation as pages are added.

Borrowed patterns:
- `llm`: recipe-driven workflows.
- `jq` and `gh`: command reference and machine-readable output examples.
- `ripgrep` and `fd`: filtering explanations with clear examples.

Validation:
- `mkdocs build --strict`.
- Link/anchor sanity check.

### PR 4: DOCS-PRES-4: CLI Output And Help Presentation

Purpose:
- Improve the terminal experience for discovery, preview, and trust-building commands.
- Make include/skip decisions easier to inspect before users generate context bundles.

Scope:
- Review and refine command help text, option grouping, and examples.
- Improve readable output for `list`, `skiplist`, `stats`, and dry-run style flows where
  useful.
- Preserve existing machine-readable contracts and backward compatibility.
- Add or update focused tests for any behavioral or output changes.

Borrowed patterns:
- `rich` and `bat`: terminal readability and concise presentation.
- `gh`: command help and workflow-oriented examples.
- `ruff`: clear diagnostics and deterministic output.

Validation:
- `ruff check .`
- `ruff format --check .`
- `pytest -m "not integration and not slow" -o addopts=`
- Add integration or snapshot updates only if intentional output changes require them.

## Coordination Rules

- Keep each PR independently reviewable and mergeable.
- Do not bundle CLI output changes into docs-only PRs.
- Update README and docs when any CLI-facing behavior or terminology changes.
- Preserve sensitive-file protections and deterministic output ordering throughout the
  milestone.
- Treat each PR as incomplete until it satisfies the repository PR completion gate:
  labeled, non-draft, detailed description, and milestone assignment when available.
