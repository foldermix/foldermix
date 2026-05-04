# Safety And Troubleshooting

`foldermix` is designed for local-folder context packing where users need to inspect what will be included before sharing output.

## Safety Defaults

- Sensitive files such as `.env`, private keys, and certificates are skipped unconditionally.
- `.gitignore` is respected by default.
- Hidden files and directories are skipped unless `--hidden` is set.
- Output ordering is deterministic.
- Size limits can skip or truncate oversized files depending on configuration.

Inspect before packing:

```bash
foldermix list . --config foldermix.toml
foldermix skiplist . --config foldermix.toml
foldermix stats . --config foldermix.toml
```

These commands print table-style summaries for included files, skipped files, and extension counts.

## Filtering And Cleanup

Use include/exclude flags or config settings to narrow the bundle:

```bash
foldermix pack . --include-ext .md,.py,.toml --out context.md
foldermix pack . --exclude-dirs node_modules,dist --out context.md
foldermix pack . --exclude-glob '*.tmp' --out context.md
```

Use duplicate suppression when exact duplicate content is noisy:

```bash
foldermix pack ./corpus --dedupe-content --report dedupe-report.json --out deduped-context.md
```

## Redaction And Policy Preview

Redact emails, phone numbers, or both:

```bash
foldermix pack . --redact all --out context.md --report report.json
```

Preview policy outcomes without writing a bundle:

```bash
foldermix pack . --policy-pack strict-privacy --policy-dry-run
foldermix pack . --policy-pack strict-privacy --policy-dry-run --policy-output json
```

Use policy enforcement only when the workflow requires a non-zero exit on findings:

```bash
foldermix pack . --policy-pack strict-privacy --fail-on-policy-violation --policy-fail-level high --report report.json
```

## Common Problems

### Expected files are missing

Run:

```bash
foldermix list . --config foldermix.toml
foldermix skiplist . --config foldermix.toml
```

Check `.gitignore`, hidden-path defaults, extension filters, glob filters, size limits, and sensitive-file protection.

### Optional converter warnings appear

Homebrew and the default `pip install foldermix` path do not install optional converter extras. Install the relevant extra through a Python environment:

```bash
pip install "foldermix[pdf]"
pip install "foldermix[ocr]"
pip install "foldermix[office]"
uv tool install "foldermix[all,markitdown]"
```

### `--null` fails

`--null` is valid only with `--stdin`:

```bash
find . -type f -print0 | foldermix pack . --stdin --null --out context.md
```

### OCR is needed for standalone images

Image files remain excluded by default. Include image extensions explicitly and enable image OCR:

```bash
foldermix pack . --include-ext .png,.jpg,.jpeg --image-ocr --out image-context.md
```

### Config values are surprising

Print the effective config and value sources:

```bash
foldermix pack . --config foldermix.toml --print-effective-config
foldermix list . --config foldermix.toml --print-effective-config
foldermix stats . --config foldermix.toml --print-effective-config
```
