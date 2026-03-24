from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from foldermix.converters.image_ocr import ImageOcrConverter
from foldermix.utils_ocr import normalize_ocr_text, redact_ocr_pii

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = REPO_ROOT / "tests" / "data" / "ocr_validation"
MANIFEST_PATH = VALIDATION_ROOT / "manifest.json"
MISSING_VALIDATION_SET = object()


@dataclass(frozen=True)
class OcrValidationItem:
    category: str
    image_path: Path
    expected_text_path: Path


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def load_validation_items() -> list[OcrValidationItem | object]:
    if not MANIFEST_PATH.exists():
        return [MISSING_VALIDATION_SET]

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise AssertionError("OCR validation manifest schema_version must be 1.")

    raw_items = manifest.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise AssertionError("OCR validation manifest must contain a non-empty items list.")

    items: list[OcrValidationItem] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise AssertionError("Each OCR validation manifest item must be an object.")

        category = raw_item.get("category")
        rel_image_path = raw_item.get("rel_image_path")
        rel_expected_text_path = raw_item.get("rel_expected_text_path")

        if not isinstance(category, str) or not category:
            raise AssertionError(
                "Each OCR validation manifest item must have a non-empty string category."
            )
        if not isinstance(rel_image_path, str) or not rel_image_path:
            raise AssertionError(
                "Each OCR validation manifest item must have a non-empty string rel_image_path."
            )
        if not isinstance(rel_expected_text_path, str) or not rel_expected_text_path:
            raise AssertionError(
                "Each OCR validation manifest item must have a non-empty string rel_expected_text_path."
            )

        image_path = VALIDATION_ROOT / rel_image_path
        expected_text_path = VALIDATION_ROOT / rel_expected_text_path
        if not image_path.exists():
            raise AssertionError(f"Missing OCR validation image: {image_path}")
        if not expected_text_path.exists():
            raise AssertionError(f"Missing OCR validation golden text: {expected_text_path}")
        items.append(
            OcrValidationItem(
                category=category,
                image_path=image_path,
                expected_text_path=expected_text_path,
            )
        )
    return items


VALIDATION_ITEMS = load_validation_items()


@pytest.mark.parametrize(
    "item",
    VALIDATION_ITEMS,
    ids=lambda item: (
        "missing-validation-set" if item is MISSING_VALIDATION_SET else item.image_path.as_posix()
    ),
)
def test_image_ocr_matches_validation_golden(item: OcrValidationItem | object) -> None:
    if item is MISSING_VALIDATION_SET:
        pytest.skip(
            "OCR validation set not present; run scripts/build_ocr_validation_set.py "
            "and commit tests/data/ocr_validation"
        )

    min_ratio = env_float("FOLDERMIX_OCR_MIN_RATIO", 0.60)
    min_chars_floor = env_int("FOLDERMIX_OCR_MIN_CHARS_FLOOR", 40)
    min_chars_frac = env_float("FOLDERMIX_OCR_MIN_CHARS_FRAC", 0.15)

    converter = ImageOcrConverter()
    expected_norm = redact_ocr_pii(
        normalize_ocr_text(item.expected_text_path.read_text(encoding="utf-8"))
    )
    actual_result = converter.convert(item.image_path, ocr_strict=True)
    actual_norm = redact_ocr_pii(normalize_ocr_text(actual_result.content))

    min_chars = max(min_chars_floor, int(min_chars_frac * len(expected_norm)))
    actual_chars = len(actual_norm.strip())
    assert actual_chars >= min_chars, (
        f"OCR output shorter than expected for {item.image_path.name} "
        f"(category={item.category}): got {actual_chars} chars, expected at least {min_chars}."
    )

    ratio = SequenceMatcher(None, expected_norm, actual_norm).ratio()
    if ratio < min_ratio:
        expected_preview = expected_norm[:300].encode("unicode_escape").decode("ascii")
        actual_preview = actual_norm[:300].encode("unicode_escape").decode("ascii")
        pytest.fail(
            f"OCR regression for category={item.category} file={item.image_path.name}: "
            f"ratio={ratio:.3f} < {min_ratio:.3f}\n"
            f"Expected: {expected_preview}\n"
            f"Actual:   {actual_preview}\n"
            "If OCR quality improved intentionally, regenerate goldens with:\n"
            "python scripts/build_ocr_validation_set.py "
            "--dataset-root /path/to/scanned-images-dataset-for-ocr-and-vlm-finetuning "
            "--out-dir tests/data/ocr_validation --per-category 5 --seed 1337 --force"
        )
