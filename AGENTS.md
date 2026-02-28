# AGENTS.md - foldermix

This file defines contributor and coding-agent rules for this repository.

## Scope and intent
- Keep changes focused, minimal, and test-backed.
- Preserve backward compatibility unless the issue or PR explicitly allows breaking changes.
- Prefer clear, deterministic behavior over implicit magic.

## Project basics
- Package: `foldermix`
- Purpose: pack folders into LLM-friendly output formats (`md`, `xml`, `jsonl`)
- Python: `>=3.10`
- Optional extras: `pdf`, `ocr`, `office`, `markitdown`, `all`

## Core quality requirements
- Lint must pass:
  - `ruff check .`
  - `ruff format --check .`
- Tests must pass:
  - `pytest -m "not integration and not slow" -o addopts=`
  - `pytest -m integration -o addopts=`
- Coverage gate:
  - `pytest --cov=foldermix --cov-branch --cov-report=term-missing:skip-covered tests/`
  - Required threshold: at least what CI enforces (currently >=98%).

## Coding expectations
- Maintain deterministic behavior and stable output ordering.
- Add tests for new behavior and edge cases.
- Do not silently swallow actionable errors.
- Keep dependency additions justified and documented.
- Update README and docs when user-visible behavior or options change.

## PR expectations
- Keep PR descriptions explicit: behavior change, flags and config keys, dependency impact, and test evidence.
- Prefer one logical change per PR.
- Ensure CI is green before merge.

## Local overrides (optional, untracked)
- If `LOCAL_AGENTS.md` exists at repo root, treat it as additive local instructions.
- On conflicts:
  - Security and repository policy rules take precedence.
  - Then `LOCAL_AGENTS.md` may refine local workflow and tool routing.
- Never commit machine-specific paths, personal tokens, or local MCP server names into tracked docs.

## Security and secrets
- Never commit secrets or credentials.
- Respect existing sensitive-file handling and redaction behavior.
