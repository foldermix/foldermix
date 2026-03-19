from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import ConversionResult

IMAGE_OCR_EXTENSIONS = {".png", ".jpg", ".jpeg"}

_IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class ImageOcrConverter:
    def can_convert(self, ext: str) -> bool:
        if ext.lower() not in IMAGE_OCR_EXTENSIONS:
            return False
        try:
            from rapidocr_onnxruntime import RapidOCR  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def _extract_ocr_text(ocr_result: Any) -> str:
        entries = ocr_result
        if isinstance(entries, tuple) and entries:
            entries = entries[0]

        if entries is None:
            return ""
        if isinstance(entries, str):
            return entries.strip()

        texts: list[str] = []
        if isinstance(entries, list):
            for entry in entries:
                if (
                    isinstance(entry, (list, tuple))
                    and len(entry) > 1
                    and isinstance(entry[1], str)
                ):
                    text = entry[1].strip()
                    if text:
                        texts.append(text)
                elif isinstance(entry, dict):
                    text = entry.get("text")
                    if isinstance(text, str):
                        text = text.strip()
                        if text:
                            texts.append(text)
        return "\n".join(texts)

    def convert(
        self,
        path: Path,
        encoding: str = "utf-8",
        *,
        ocr_strict: bool = False,
    ) -> ConversionResult:
        del encoding
        warnings: list[str] = []

        def unresolved_ocr(message: str) -> ConversionResult:
            warnings.append(message)
            if ocr_strict:
                raise RuntimeError(message)
            return ConversionResult(
                content="",
                warnings=warnings,
                converter_name="rapidocr",
                original_mime=_IMAGE_MIME_TYPES.get(path.suffix.lower(), ""),
            )

        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:  # pragma: no cover - guarded by can_convert/_convert_record
            return unresolved_ocr(f"OCR dependencies missing: {exc}")

        try:
            ocr_engine = RapidOCR()
        except Exception as exc:
            return unresolved_ocr(f"OCR engine initialization failed: {exc}")

        try:
            ocr_text = self._extract_ocr_text(ocr_engine(path.read_bytes()))
        except Exception as exc:
            return unresolved_ocr(f"Image OCR failed: {exc}")

        if not ocr_text.strip():
            return unresolved_ocr("Image OCR produced no text.")

        return ConversionResult(
            content=ocr_text,
            warnings=warnings,
            converter_name="rapidocr",
            original_mime=_IMAGE_MIME_TYPES.get(path.suffix.lower(), ""),
        )
