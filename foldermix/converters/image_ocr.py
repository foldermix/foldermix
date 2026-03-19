from __future__ import annotations

import importlib
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
    @staticmethod
    def _load_rapidocr() -> tuple[Any | None, str | None]:
        try:
            module = importlib.import_module("rapidocr_onnxruntime")
        except (ImportError, OSError, RuntimeError) as exc:
            return None, str(exc)
        return getattr(module, "RapidOCR", None), None

    def can_convert(self, ext: str) -> bool:
        if ext.lower() not in IMAGE_OCR_EXTENSIONS:
            return False
        rapid_ocr_cls, _ = self._load_rapidocr()
        return rapid_ocr_cls is not None

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

        rapid_ocr_cls, import_error = self._load_rapidocr()
        if rapid_ocr_cls is None:
            suffix = f": {import_error}" if import_error else ""
            return unresolved_ocr(f"OCR dependencies missing{suffix}")

        try:
            ocr_engine = rapid_ocr_cls()
        except Exception as exc:
            return unresolved_ocr(f"OCR engine initialization failed: {exc}")

        try:
            ocr_text = self._extract_ocr_text(ocr_engine(str(path)))
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
