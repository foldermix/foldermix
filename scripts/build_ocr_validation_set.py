from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import random
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATASET_NAME = "scanned-images-dataset-for-ocr-and-vlm-finetuning"
DEFAULT_MAX_IMAGE_BYTES = 200_000  # 200 KB per committed image
DEFAULT_MAX_IMAGE_DIM = 1920  # max side length in pixels
DEFAULT_CATEGORIES = (
    "ADVE",
    "Email",
    "Form",
    "Letter",
    "Memo",
    "News",
    "Note",
    "Report",
    "Resume",
    "Scientific",
)
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class ValidationItem:
    category: str
    rel_image_path: str
    rel_expected_text_path: str
    sha256: str
    size_bytes: int


def shrink_image(src: Path, dest: Path, *, max_bytes: int, max_dim: int) -> None:
    """Copy *src* to *dest*, rescaling and/or recompressing if needed.

    An image is processed when either of these conditions holds:
      - its longest side exceeds *max_dim* pixels, or
      - its on-disk size exceeds *max_bytes* bytes.

    JPEG images are written as JPEG; PNG images are written as PNG.
    For JPEG output the quality setting is stepped down (85 → 70 → 55 → 40)
    until the encoded size fits within *max_bytes*; if no quality step achieves
    that target the result at the lowest quality is still written.
    """
    from PIL import Image  # noqa: PLC0415 - optional at script-level

    src_bytes = src.stat().st_size
    with Image.open(src) as img:
        src_dim = max(img.size)
        if src_bytes <= max_bytes and src_dim <= max_dim:
            shutil.copy2(src, dest)
            return
        img.load()
        work = img.copy()

    if max(work.size) > max_dim:
        work.thumbnail((max_dim, max_dim), Image.LANCZOS)

    ext = src.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        rgb = work.convert("RGB")
        last_buf: io.BytesIO | None = None
        for quality in (85, 70, 55, 40):
            buf = io.BytesIO()
            rgb.save(buf, format="JPEG", quality=quality, optimize=True)
            last_buf = buf
            if buf.tell() <= max_bytes:
                break
        assert last_buf is not None
        dest.write_bytes(last_buf.getvalue())
    else:
        buf = io.BytesIO()
        save_mode = work.mode if work.mode in ("RGBA", "RGB", "L", "P") else "RGB"
        work.convert(save_mode).save(buf, format="PNG", optimize=True)
        dest.write_bytes(buf.getvalue())


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a committable OCR validation set from a local source dataset."
    )
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--per-category", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated category names. Defaults to the published dataset categories.",
    )
    parser.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        help="Dataset name recorded in the manifest.",
    )
    parser.add_argument(
        "--lowercase",
        action="store_true",
        help="Lowercase normalized OCR goldens before writing them.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output directory.",
    )
    parser.add_argument(
        "--max-image-bytes",
        type=int,
        default=DEFAULT_MAX_IMAGE_BYTES,
        help=(
            "Maximum on-disk size (bytes) for a committed image. "
            "Images exceeding this limit are recompressed and/or rescaled. "
            f"Default: {DEFAULT_MAX_IMAGE_BYTES}."
        ),
    )
    parser.add_argument(
        "--max-image-dim",
        type=int,
        default=DEFAULT_MAX_IMAGE_DIM,
        help=(
            "Maximum side length (pixels) for a committed image. "
            "Images with a longer side are scaled down before compression. "
            f"Default: {DEFAULT_MAX_IMAGE_DIM}."
        ),
    )
    return parser.parse_args(argv)


def parse_categories(raw_categories: str) -> list[str]:
    categories = [category.strip() for category in raw_categories.split(",") if category.strip()]
    if not categories:
        raise ValueError("At least one category is required.")
    return categories


def category_seed(seed: int, category: str) -> int:
    digest = hashlib.sha256(f"{seed}:{category}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def image_candidates(category_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in category_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ],
        key=lambda path: path.name.casefold(),
    )


def sample_category_images(category_dir: Path, *, per_category: int, seed: int) -> list[Path]:
    candidates = image_candidates(category_dir)
    if len(candidates) < per_category:
        raise ValueError(
            f"Category {category_dir.name!r} has {len(candidates)} eligible images, "
            f"but --per-category={per_category} was requested."
        )
    rng = random.Random(category_seed(seed, category_dir.name))
    sampled = rng.sample(candidates, per_category)
    return sorted(sampled, key=lambda path: path.name.casefold())


def ensure_expected_categories(dataset_root: Path, categories: Sequence[str]) -> None:
    missing = [category for category in categories if not (dataset_root / category).is_dir()]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            f"Dataset root {dataset_root} is missing expected category directories: {joined}"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_image_ocr_converter() -> Any:
    ensure_project_root_on_sys_path()
    module = importlib.import_module("foldermix.converters.image_ocr")
    return module.ImageOcrConverter()


def normalize_ocr_text_value(text: str, *, lowercase: bool) -> str:
    ensure_project_root_on_sys_path()
    module = importlib.import_module("foldermix.utils_ocr")
    return module.redact_ocr_pii(module.normalize_ocr_text(text, lowercase=lowercase))


def ensure_project_root_on_sys_path() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def rapidocr_import_error() -> str | None:
    try:
        importlib.import_module("rapidocr_onnxruntime")
    except (ImportError, OSError, RuntimeError) as exc:
        return str(exc)
    return None


def strict_ocr_converter() -> Any:
    import_error = rapidocr_import_error()
    if import_error is not None:
        suffix = f"\nUnderlying error: {import_error}" if import_error else ""
        raise RuntimeError(
            'OCR dependencies missing. Install them with `pip install -e ".[ocr]"` '
            f'or `pip install -e ".[all]"` before building the validation set.{suffix}'
        )
    return get_image_ocr_converter()


def render_expected_text(
    converter: Any,
    image_path: Path,
    *,
    lowercase: bool,
) -> str:
    result = converter.convert(image_path, ocr_strict=True)
    return normalize_ocr_text_value(result.content, lowercase=lowercase)


def build_manifest(
    *,
    dataset_name: str,
    dataset_root: Path,
    categories: Sequence[str],
    per_category: int,
    seed: int,
    max_image_bytes: int,
    max_image_dim: int,
    items: Sequence[ValidationItem],
    created_at: datetime,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source": {
            "dataset_name": dataset_name,
            "dataset_root_basename": dataset_root.name,
        },
        "created_at": created_at.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "params": {
            "per_category": per_category,
            "seed": seed,
            "max_image_bytes": max_image_bytes,
            "max_image_dim": max_image_dim,
        },
        "categories": list(categories),
        "items": [
            {
                "category": item.category,
                "rel_image_path": item.rel_image_path,
                "rel_expected_text_path": item.rel_expected_text_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            for item in sorted(items, key=lambda item: (item.category, item.rel_image_path))
        ],
    }


def build_validation_set(
    *,
    dataset_root: Path,
    out_dir: Path,
    categories: Sequence[str],
    per_category: int,
    seed: int,
    dataset_name: str,
    lowercase: bool,
    force: bool,
    max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_image_dim: int = DEFAULT_MAX_IMAGE_DIM,
    converter: Any | None = None,
    created_at: datetime | None = None,
) -> dict[str, object]:
    if per_category <= 0:
        raise ValueError("--per-category must be a positive integer.")
    if out_dir.exists():
        if not force:
            raise ValueError(f"Output directory {out_dir} already exists. Re-run with --force.")
        if out_dir.is_dir():
            shutil.rmtree(out_dir)
        else:
            raise ValueError(
                f"Output path {out_dir} exists and is not a directory. "
                "Please remove it or choose a different output directory."
            )

    ensure_expected_categories(dataset_root, categories)
    out_dir.mkdir(parents=True, exist_ok=True)

    images_dir = out_dir / "images"
    expected_dir = out_dir / "expected_text"
    items: list[ValidationItem] = []
    ocr_converter = converter if converter is not None else strict_ocr_converter()

    for category in categories:
        category_dir = dataset_root / category
        sampled_images = sample_category_images(category_dir, per_category=per_category, seed=seed)
        dest_image_dir = images_dir / category
        dest_expected_dir = expected_dir / category
        dest_image_dir.mkdir(parents=True, exist_ok=True)
        dest_expected_dir.mkdir(parents=True, exist_ok=True)

        for source_path in sampled_images:
            copied_image_path = dest_image_dir / source_path.name
            shrink_image(
                source_path,
                copied_image_path,
                max_bytes=max_image_bytes,
                max_dim=max_image_dim,
            )

            expected_text = render_expected_text(
                ocr_converter,
                copied_image_path,
                lowercase=lowercase,
            )
            expected_text_path = dest_expected_dir / f"{source_path.stem}.txt"
            expected_text_path.write_text(f"{expected_text}\n", encoding="utf-8")

            items.append(
                ValidationItem(
                    category=category,
                    rel_image_path=copied_image_path.relative_to(out_dir).as_posix(),
                    rel_expected_text_path=expected_text_path.relative_to(out_dir).as_posix(),
                    sha256=sha256_file(copied_image_path),
                    size_bytes=copied_image_path.stat().st_size,
                )
            )

    manifest = build_manifest(
        dataset_name=dataset_name,
        dataset_root=dataset_root,
        categories=categories,
        per_category=per_category,
        seed=seed,
        max_image_bytes=max_image_bytes,
        max_image_dim=max_image_dim,
        items=items,
        created_at=created_at or datetime.now(timezone.utc),
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    dataset_root = args.dataset_root.resolve()
    out_dir = args.out_dir.resolve()

    try:
        categories = parse_categories(args.categories)
        manifest = build_validation_set(
            dataset_root=dataset_root,
            out_dir=out_dir,
            categories=categories,
            per_category=args.per_category,
            seed=args.seed,
            dataset_name=args.dataset_name,
            lowercase=args.lowercase,
            force=args.force,
            max_image_bytes=args.max_image_bytes,
            max_image_dim=args.max_image_dim,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    item_count = len(manifest["items"])
    print(
        "Built OCR validation set: "
        f"{len(manifest['categories'])} categories, "
        f"{item_count} images copied, "
        f"{item_count} expected-text files written."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
