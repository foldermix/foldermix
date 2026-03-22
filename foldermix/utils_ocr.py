from __future__ import annotations

import re

_INLINE_WHITESPACE_RE = re.compile(r"[ \t]+")


def normalize_ocr_text(text: str, *, lowercase: bool = False) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_INLINE_WHITESPACE_RE.sub(" ", line).rstrip() for line in normalized.split("\n")]
    collapsed = "\n".join(lines).strip()
    if lowercase:
        return collapsed.lower()
    return collapsed
