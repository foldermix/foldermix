# foldermix Docs

`foldermix` packs a local folder into one LLM-friendly context artifact you can inspect, share, or pipe into automation.

## Where To Go Next

- [Quickstart](quickstart.md): install `foldermix`, run the first pack, and preview what will be included.
- [Workflows](workflows.md): copy-pasteable recipes for AI context, legal review, research, support, course refresh, config-first, and `jsonl` report pipelines.
- [Configuration](configuration.md): config precedence, `foldermix.toml` discovery, command sections, starter profiles, and effective-config diagnostics.
- [Output Formats And Reports](output-formats-and-reports.md): when to choose Markdown, XML, or JSONL, and how to use `--report`.
- [Safety And Troubleshooting](safety-and-troubleshooting.md): sensitive-file handling, filters, policy dry-runs, OCR notes, and common fixes.
- [CLI Presentation Roadmap](cli-presentation-roadmap.md): the M3 documentation and CLI presentation plan.

## First Command

```bash
foldermix pack . --out context.md
```

This writes a Markdown bundle for the current folder. Run `foldermix list .` and `foldermix skiplist .` first when you want to inspect include and skip decisions before producing a bundle.

## Install Paths

```bash
pip install foldermix
```

The default install is enough for text, Markdown, source code, config/data files, WebVTT, and notebooks.

Homebrew is available for the core CLI:

```bash
brew tap foldermix/foldermix
brew install foldermix
```

Homebrew does not install optional Python extras. Use a Python tool install when you need PDF, OCR, Office, or `markitdown` support:

```bash
uv tool install "foldermix[all,markitdown]"
```
