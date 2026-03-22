from __future__ import annotations

import re

_INLINE_WHITESPACE_RE = re.compile(r"[ \t]+")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_REDACTED_SSN = "000-00-0000"


def normalize_ocr_text(text: str, *, lowercase: bool = False) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_INLINE_WHITESPACE_RE.sub(" ", line).rstrip() for line in normalized.split("\n")]
    collapsed = "\n".join(lines).strip()
    if lowercase:
        return collapsed.lower()
    return collapsed


def redact_ocr_pii(text: str) -> str:
    return _SSN_RE.sub(_REDACTED_SSN, text)
