# Output Formats And Reports

Choose the output format based on how the bundle will be read.

## Formats

| Format | Choose it when | Shape |
|---|---|---|
| Markdown (`md`) | You want a readable context file to paste into chat, inspect in an editor, or share with a reviewer. | One document with metadata, table of contents, and fenced file blocks. |
| XML (`xml`) | You want explicit file boundaries for tools or prompts that parse tagged sections. | One `<foldermix>` document with `<header>` metadata and `<files>` containing one `<file>` element per included file. |
| JSONL (`jsonl`) | You want streaming, indexing, or pipeline-friendly machine input. | One header object followed by one JSON object per included file. |

Examples:

```bash
foldermix pack . --format md --out context.md
foldermix pack . --format xml --out context.xml
foldermix pack . --format jsonl --out context.jsonl
```

## Reports

Use `--report` when you need a machine-readable audit trail:

```bash
foldermix pack . --format md --out context.md --report report.json
```

The report includes high-level run counters and per-file details:

- `schema_version`
- `included_count`, `skipped_count`, and `total_bytes`
- `included_files[]`
- `skipped_files[]`
- `reason_code_counts`
- `warning_code_counts`
- `redaction_summary`
- `policy_findings`
- `policy_finding_counts`

Minimal shape:

```json
{
  "schema_version": 5,
  "included_count": 2,
  "skipped_count": 1,
  "total_bytes": 1234,
  "included_files": [
    {"path": "README.md", "outcome_codes": []}
  ],
  "skipped_files": [
    {
      "path": ".env",
      "reason_code": "SKIP_SENSITIVE",
      "message": "Path matches a sensitive-file pattern."
    }
  ],
  "reason_code_counts": {"SKIP_SENSITIVE": 1}
}
```

Read reports in this order:

1. Check `included_count`, `skipped_count`, and `total_bytes` to confirm the run size.
2. Review `reason_code_counts` for the most common skip or outcome reasons.
3. Inspect `skipped_files[]` when expected files are missing.
4. Inspect `included_files[]` for truncation, redaction, and conversion warnings.
5. Review `policy_findings[]` and `policy_finding_counts` when policy packs or custom rules are enabled.

## Reason-Code Families

Reports group outcomes into stable families:

- Skip reasons: hidden paths, excluded directories, sensitive files, `.gitignore`, globs, extensions, unreadable paths, oversized files, missing paths, and outside-root stdin entries.
- Included-file outcomes: truncation, redaction, and conversion warnings.
- Warning taxonomy: encoding fallback, converter availability, OCR dependency or extraction issues, and unclassified warnings.
- Policy findings: rule matches, skip-reason matches, content regex matches, and file/count/byte threshold findings.

Use these families to decide whether to adjust filters, install optional converters, enable redaction, or investigate policy findings.
