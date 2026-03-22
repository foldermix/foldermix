from __future__ import annotations

from foldermix.utils_ocr import normalize_ocr_text


def test_normalize_ocr_text_normalizes_newlines_and_inline_whitespace() -> None:
    raw = "  Hello\t\tworld \r\nSecond   line\t \rThird\t\tline  "
    assert normalize_ocr_text(raw) == "Hello world\nSecond line\nThird line"


def test_normalize_ocr_text_preserves_case_by_default() -> None:
    assert normalize_ocr_text("MiXeD Case") == "MiXeD Case"


def test_normalize_ocr_text_optionally_lowercases_output() -> None:
    assert normalize_ocr_text("MiXeD\t Case", lowercase=True) == "mixed case"
