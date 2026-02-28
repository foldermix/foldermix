from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPORT_SCHEMA_VERSION = 2

SKIP_REASON_CODES: dict[str, str] = {
    "hidden": "SKIP_HIDDEN",
    "excluded_dir": "SKIP_EXCLUDED_DIR",
    "sensitive": "SKIP_SENSITIVE",
    "gitignored": "SKIP_GITIGNORED",
    "excluded_glob": "SKIP_EXCLUDED_GLOB",
    "excluded_ext": "SKIP_EXCLUDED_EXT",
    "unreadable": "SKIP_UNREADABLE",
    "oversize": "SKIP_OVERSIZE",
    "outside_root": "SKIP_OUTSIDE_ROOT",
    "missing": "SKIP_MISSING",
    "not_file": "SKIP_NOT_FILE",
}

SKIP_REASON_MESSAGES: dict[str, str] = {
    "hidden": "Hidden path excluded by default scanner rules.",
    "excluded_dir": "Path is inside an excluded directory.",
    "sensitive": "Path matches a sensitive-file pattern.",
    "gitignored": "Path is matched by .gitignore rules.",
    "excluded_glob": "Path is excluded by glob filtering.",
    "excluded_ext": "Path is excluded by extension filtering.",
    "unreadable": "Path could not be read from the filesystem.",
    "oversize": "Path exceeds --max-bytes with skip policy.",
    "outside_root": "Explicit path is outside the configured root.",
    "missing": "Explicit path does not exist.",
    "not_file": "Explicit path is not a regular file.",
}

OUTCOME_TRUNCATED = "OUTCOME_TRUNCATED"
OUTCOME_REDACTED = "OUTCOME_REDACTED"
OUTCOME_CONVERSION_WARNING = "OUTCOME_CONVERSION_WARNING"


@dataclass
class ReportData:
    included_count: int
    skipped_count: int
    total_bytes: int
    included_files: list[dict]
    skipped_files: list[dict]
    schema_version: int = REPORT_SCHEMA_VERSION
    reason_code_counts: dict[str, int] = field(default_factory=dict)


def _skip_reason_code(reason: str) -> str:
    return SKIP_REASON_CODES.get(reason, "SKIP_UNKNOWN")


def _skip_reason_message(reason: str) -> str:
    return SKIP_REASON_MESSAGES.get(reason, "Path skipped for an unspecified reason.")


def build_skipped_file_entry(*, path: str, reason: str) -> dict:
    return {
        "path": path,
        "reason": reason,
        "reason_code": _skip_reason_code(reason),
        "message": _skip_reason_message(reason),
    }


def build_included_file_entry(
    *,
    path: str,
    size: int,
    ext: str,
    truncated: bool,
    redacted: bool,
    warning_messages: Iterable[str],
    redact_mode: str,
) -> dict:
    outcomes: list[dict[str, str]] = []
    if truncated:
        outcomes.append(
            {
                "code": OUTCOME_TRUNCATED,
                "message": "File content was truncated to satisfy --max-bytes.",
            }
        )
    if redacted:
        outcomes.append(
            {
                "code": OUTCOME_REDACTED,
                "message": f"Content was redacted using mode '{redact_mode}'.",
            }
        )
    for warning in warning_messages:
        outcomes.append(
            {
                "code": OUTCOME_CONVERSION_WARNING,
                "message": warning,
            }
        )
    outcome_codes = list(dict.fromkeys(outcome["code"] for outcome in outcomes))

    return {
        "path": path,
        "size": size,
        "ext": ext,
        "outcome_codes": outcome_codes,
        "outcomes": outcomes,
    }


def build_reason_code_counts(
    *, included_files: list[dict], skipped_files: list[dict]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in skipped_files:
        reason_code = entry.get("reason_code")
        if reason_code is None:
            reason = entry.get("reason")
            if isinstance(reason, str):
                reason_code = _skip_reason_code(reason)
            else:
                reason_code = "SKIP_UNKNOWN"
        code = str(reason_code)
        counts[code] = counts.get(code, 0) + 1

    for entry in included_files:
        for code in entry.get("outcome_codes", []):
            code_str = str(code)
            counts[code_str] = counts.get(code_str, 0) + 1

    return dict(sorted(counts.items()))


def write_report(report_path: Path, data: ReportData) -> None:
    payload = asdict(data)
    if not payload["reason_code_counts"]:
        payload["reason_code_counts"] = build_reason_code_counts(
            included_files=payload["included_files"],
            skipped_files=payload["skipped_files"],
        )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
