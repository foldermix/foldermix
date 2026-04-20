from __future__ import annotations

from pathlib import Path

from .base import ConversionResult

_OFFICE_MIME_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
}


class MarkitdownConverter:
    EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppsx", ".xlsx"}

    def can_convert(self, ext: str) -> bool:
        try:
            import markitdown  # noqa: F401

            return ext.lower() in self.EXTENSIONS
        except ImportError:
            return False

    def convert(self, path: Path, encoding: str = "utf-8") -> ConversionResult:
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(str(path))
        ext = path.suffix.lower()
        return ConversionResult(
            content=result.text_content,
            converter_name="markitdown",
            original_mime=_OFFICE_MIME_TYPES.get(ext, f"application/{ext.lstrip('.')}"),
        )
