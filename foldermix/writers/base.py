from __future__ import annotations

from dataclasses import dataclass, field
from typing import IO


@dataclass
class HeaderInfo:
    root: str
    generated_at: str
    version: str
    args: dict
    file_count: int
    total_bytes: int


@dataclass
class FileBundleItem:
    relpath: str
    ext: str
    size_bytes: int
    mtime: str
    sha256: str | None
    content: str
    converter_name: str
    original_mime: str
    warnings: list[str] = field(default_factory=list)
    warning_entries: list[dict[str, object]] = field(default_factory=list)
    truncated: bool = False
    redacted: bool = False
    redaction_mode: str = "none"
    redaction_event_count: int = 0
    redaction_categories: list[str] = field(default_factory=list)


@dataclass
class SkippedFileEntry:
    path: str
    reason_code: str
    message: str


class Writer:
    def write(
        self,
        out: IO[str],
        header: HeaderInfo,
        items: list[FileBundleItem],
        skipped_entries: list[SkippedFileEntry] | None = None,
    ) -> None:
        raise NotImplementedError
