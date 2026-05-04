# Workflows

These cookbook recipes are starting points for common local-folder jobs. Each recipe keeps commands copy-pasteable and names the expected artifact.

Write generated bundles and reports outside the source tree, or exclude previous `context.*`, `*-context.*`, and `*report.json` artifacts with `.gitignore`, `foldermix.toml`, or CLI filters before repeat runs.

## AI Context Packing

### When to use it

Use this when you want a readable context bundle for a codebase, docs folder, or mixed project notes.

### Commands

```bash
foldermix list .
foldermix pack . --format md --out context.md --report report.json
```

### Expected artifact

`context.md` for the LLM-facing bundle and `report.json` for the include/skip audit trail.

### Safety/filtering note

Sensitive files are skipped unconditionally, `.gitignore` is respected by default, and hidden paths stay out unless `--hidden` is set. Keep generated `context.md` and `report.json` out of later packs.

## Legal Review Bundles

### When to use it

Use this for privacy-sensitive matter folders where redaction, OCR fallback, checksums, and a report are useful.

### Commands

```bash
foldermix init --profile legal --out foldermix.toml --force
foldermix pack ./matter --config foldermix.toml --format md --out legal-context.md --report legal-report.json
```

### Expected artifact

`legal-context.md` for review and `legal-report.json` for traceability.

### Safety/filtering note

The `legal` profile enables full redaction and PDF OCR fallback defaults. Use [Safety And Troubleshooting](safety-and-troubleshooting.md) for policy dry-run and enforcement options when you need stricter gates.

## Research Corpus Bundles

### When to use it

Use this for literature-heavy or mixed-format corpora where machine-readable output is useful downstream.

### Commands

```bash
foldermix init --profile research --out foldermix.toml --force
find ./corpus -type f -print0 | foldermix pack ./corpus --config foldermix.toml --stdin --null --format jsonl --out research-context.jsonl --report research-report.json
```

### Expected artifact

`research-context.jsonl`, with one header object and one JSON object per included file, plus `research-report.json`.

### Safety/filtering note

The `research` profile favors broad recall and email redaction. The explicit `find -print0` pipeline makes the selected input list reproducible.

## Support Incident Bundles

### When to use it

Use this when packing tickets, logs, runbooks, and related notes for incident analysis.

### Commands

```bash
foldermix init --profile support --out foldermix.toml --force
printf 'tickets/a.md\ntickets/b.log\n' | foldermix pack . --config foldermix.toml --stdin --format md --out support-context.md --report support-report.json
```

### Expected artifact

`support-context.md` and `support-report.json`.

### Safety/filtering note

The `support` profile uses full redaction defaults. Prefer explicit stdin lists when only selected tickets or logs should be included.

## Course Refresh Bundles

### When to use it

Use this when preparing prior course material for refresh or reuse while avoiding common student/admin paths.

### Commands

```bash
foldermix init --profile course-refresh --out foldermix.toml --force
foldermix pack ./previous-course --config foldermix.toml --format md --out course-refresh-context.md --report course-refresh-report.json
```

### Expected artifact

`course-refresh-context.md` and `course-refresh-report.json`.

### Safety/filtering note

The `course-refresh` profile excludes common course-admin and student-specific paths such as grades, rosters, responses, feedback, and submissions.

## Config-First Workflows

### When to use it

Use this when a project needs repeatable packing behavior across local runs, reviews, or automation.

### Commands

```bash
foldermix init --profile engineering-docs --out foldermix.toml --force
foldermix pack . --config foldermix.toml --print-effective-config
foldermix list . --config foldermix.toml
foldermix pack . --config foldermix.toml --format md --out context.md --report report.json
```

### Expected artifact

`foldermix.toml`, `context.md`, and `report.json`.

### Safety/filtering note

Use `--print-effective-config` to verify which settings came from defaults, config, or CLI flags before writing output.

## Machine-Readable Reports And JSONL Pipelines

### When to use it

Use this when downstream tooling needs structured records or when you want an audit trail for included and skipped files.

### Commands

```bash
find ./corpus -type f -print0 | foldermix pack ./corpus --stdin --null --format jsonl --out context.jsonl --report report.json
```

### Expected artifact

`context.jsonl` for streaming or indexing, plus `report.json` for reason codes and outcome summaries.

### Safety/filtering note

JSONL is best for tools that process one object at a time. Use the report to inspect skip reasons, redaction outcomes, conversion warnings, and policy findings.
