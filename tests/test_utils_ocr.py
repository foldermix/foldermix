from __future__ import annotations

from foldermix.utils_ocr import normalize_ocr_text, redact_ocr_pii


def test_normalize_ocr_text_normalizes_newlines_and_inline_whitespace() -> None:
    raw = "  Hello\t\tworld \r\nSecond   line\t \rThird\t\tline  "
    assert normalize_ocr_text(raw) == "Hello world\nSecond line\nThird line"


def test_normalize_ocr_text_preserves_case_by_default() -> None:
    assert normalize_ocr_text("MiXeD Case") == "MiXeD Case"


def test_normalize_ocr_text_optionally_lowercases_output() -> None:
    assert normalize_ocr_text("MiXeD\t Case", lowercase=True) == "mixed case"


def test_redact_ocr_pii_replaces_ssn_like_values() -> None:
    assert redact_ocr_pii("SSN 123-45-6789") == "SSN 000-00-0000"
