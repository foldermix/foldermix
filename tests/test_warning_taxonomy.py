from __future__ import annotations

import pytest

from foldermix.warning_taxonomy import classify_warning_message, normalize_warning_entries


@pytest.mark.parametrize(
    ("message", "expected_code"),
    [
        ("Encoding fallback: used 'latin-1' instead of 'utf-8'", "encoding_fallback"),
        (
            "Page 1 has no extractable text. OCR is disabled; use --pdf-ocr to attempt OCR.",
            "ocr_disabled",
        ),
        (
            "Page 1 has no extractable text and OCR is unavailable. OCR dependencies missing: pypdfium2.",
            "ocr_dependencies_missing",
        ),
        (
            "Page 1 has no extractable text and OCR is unavailable. OCR engine initialization failed: boom.",
            "ocr_initialization_failed",
        ),
        ("Page 2 OCR failed: ocr boom", "ocr_failed"),
        ("Page 3 has no extractable text and OCR produced no text.", "ocr_no_text"),
        (
            "PDF OCR is enabled, but PDF/OCR dependencies are unavailable. Install the PDF/OCR extras or disable --pdf-ocr.",
            "converter_unavailable",
        ),
        ("some unstructured warning", "unclassified_warning"),
    ],
)
def test_classify_warning_message(message: str, expected_code: str) -> None:
    assert classify_warning_message(message) == expected_code


def test_normalize_warning_entries_maps_messages_to_code_and_message() -> None:
    entries = normalize_warning_entries(
        [
            "Encoding fallback: used 'latin-1' instead of 'utf-8'",
            "some unstructured warning",
        ]
    )
    assert entries == [
        {
            "code": "encoding_fallback",
            "message": "Encoding fallback: used 'latin-1' instead of 'utf-8'",
        },
        {
            "code": "unclassified_warning",
            "message": "some unstructured warning",
        },
    ]
