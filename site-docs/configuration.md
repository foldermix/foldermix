# Configuration

`foldermix` can run with no config file, but repeatable workflows should use `foldermix.toml`.

## Resolution Order

Effective options are resolved in this deterministic order:

1. Built-in defaults
2. `foldermix.toml`
3. Explicit CLI flags

Higher layers override lower layers.

## Config Discovery

Use an explicit config path when you want the run to be unambiguous:

```bash
foldermix pack . --config foldermix.toml --out context.md
```

When `--config` is omitted, `foldermix` discovers `foldermix.toml` by walking upward from the target path.

## Sections

- `[pack]` controls file-selection and packing behavior shared by `pack`, `list`, and `skiplist`.
- `[stats]` keeps stats-specific defaults separate.
- `[common]` is copied into command sections, so use it only for keys that are valid for every command that will read that config.

Use this command to inspect the merged result and value sources:

```bash
foldermix pack . --config foldermix.toml --print-effective-config
foldermix list . --config foldermix.toml --print-effective-config
foldermix stats . --config foldermix.toml --print-effective-config
```

## Starter Profiles

Generate a commented starter config with `foldermix init`:

```bash
foldermix init --profile legal --out foldermix.toml --force
foldermix init --profile research --out foldermix.toml --force
foldermix init --profile support --out foldermix.toml --force
foldermix init --profile engineering-docs --out foldermix.toml --force
foldermix init --profile course-refresh --out foldermix.toml --force
```

Profile intent:

- `legal`: privacy-first defaults, full redaction, PDF OCR fallback enabled.
- `research`: broad mixed-document coverage, email redaction, OCR enabled.
- `support`: ticket and runbook focused filters with full redaction.
- `engineering-docs`: docs/code handoff defaults, frontmatter stripping, no redaction.
- `course-refresh`: teaching-material defaults with exclusions for student/admin paths.

## Stdin File Lists

Use stdin when the input list should come from another command:

```bash
printf 'a.txt\nnested/b.txt\n' | foldermix pack . --config foldermix.toml --stdin --format jsonl --out context.jsonl
find . -type f -print0 | foldermix pack . --config foldermix.toml --stdin --null --format md --out context.md
```

`--null` requires `--stdin` and is intended for NUL-delimited input such as `find -print0`.
