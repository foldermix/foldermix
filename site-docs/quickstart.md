# Quickstart

Use this page to install `foldermix`, inspect a folder, and write your first context bundle.

## Install

Recommended default:

```bash
pip install foldermix
```

Use the default install for the core CLI and text-like files: plain text, Markdown, source code, config/data files, WebVTT, and notebooks.

Homebrew installs the core CLI only:

```bash
brew tap foldermix/foldermix
brew install foldermix
```

Homebrew does not install optional converter extras. Use a Python tool install when you need PDF, OCR, Office, or `markitdown` support:

```bash
uv tool install "foldermix[all,markitdown]"
```

## Pack A Folder

Run from the folder you want to pack:

```bash
foldermix pack . --out context.md
```

Expected artifact: `context.md`, a Markdown bundle with run metadata, a table of contents, and fenced file blocks.

Defaults worth knowing:

- Markdown (`md`) is the default output format.
- If `--out` is omitted, the generated timestamped filename uses the selected format extension.
- Hidden files and directories are skipped unless `--hidden` is set.
- `.gitignore` is respected by default.

## Preview Before Packing

Use these commands before producing a bundle:

```bash
foldermix list .
foldermix skiplist .
foldermix stats .
foldermix preview . README.md
```

- `list` shows files that would be included.
- `skiplist` shows files that would be skipped and why.
- `stats` summarizes selected files by extension and size.
- `preview` renders selected files through the pack pipeline without writing the full bundle.

`list`, `skiplist`, and `stats` print table-style summaries so include/skip decisions are easier to scan before packing.

## Config-First Quick Path

Use a starter profile when the workflow should be repeatable:

```bash
foldermix init --profile engineering-docs
foldermix pack . --config foldermix.toml --format md --out context.md --report report.json
```

Expected artifacts:

- `foldermix.toml`: editable configuration for future runs.
- `context.md`: packed Markdown context bundle.
- `report.json`: machine-readable include/skip and outcome report.
