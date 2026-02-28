from __future__ import annotations

import json
from pathlib import Path

from foldermix.report import (
    ReportData,
    build_included_file_entry,
    build_skipped_file_entry,
    write_report,
)


def test_build_skipped_file_entry_unknown_reason_uses_fallback_code_and_message() -> None:
    entry = build_skipped_file_entry(path="mystery.bin", reason="mystery_reason")

    assert entry["path"] == "mystery.bin"
    assert entry["reason"] == "mystery_reason"
    assert entry["reason_code"] == "SKIP_UNKNOWN"
    assert entry["message"] == "Path skipped for an unspecified reason."


def test_write_report_backfills_reason_code_counts_when_missing(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    data = ReportData(
        included_count=1,
        skipped_count=1,
        total_bytes=3,
        included_files=[
            {
                "path": "a.txt",
                "size": 3,
                "ext": ".txt",
                "outcome_codes": ["OUTCOME_CONVERSION_WARNING"],
                "outcomes": [
                    {
                        "code": "OUTCOME_CONVERSION_WARNING",
                        "message": "example warning",
                    }
                ],
            }
        ],
        skipped_files=[{"path": "missing.txt", "reason": "missing"}],
    )

    write_report(report_path, data)
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["reason_code_counts"] == {
        "OUTCOME_CONVERSION_WARNING": 1,
        "SKIP_MISSING": 1,
    }


def test_build_included_file_entry_deduplicates_outcome_codes() -> None:
    entry = build_included_file_entry(
        path="a.txt",
        size=3,
        ext=".txt",
        truncated=False,
        redacted=False,
        warning_messages=["warn-1", "warn-2"],
        redact_mode="none",
    )

    assert entry["outcome_codes"] == ["OUTCOME_CONVERSION_WARNING"]
    assert len(entry["outcomes"]) == 2
