from __future__ import annotations

import importlib.util
import io
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


def make_jpeg(path: Path, width: int = 20, height: int = 20) -> None:
    """Write a minimal valid JPEG to *path* (solid grey rectangle)."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    path.write_bytes(buf.getvalue())


def load_builder_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_ocr_validation_set.py"
    spec = importlib.util.spec_from_file_location("build_ocr_validation_set", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load build_ocr_validation_set.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_build_validation_set_creates_manifest_images_and_goldens(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    for category in ("Email", "Memo"):
        category_dir = dataset_root / category
        category_dir.mkdir(parents=True)
        for index in range(3):
            make_jpeg(category_dir / f"{category.lower()}-{index}.jpg")

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del encoding, ocr_strict
            return SimpleNamespace(content=f" OCR\tfor {path.stem} \r\n")

    out_dir = tmp_path / "out"
    manifest = module.build_validation_set(
        dataset_root=dataset_root,
        out_dir=out_dir,
        categories=["Email", "Memo"],
        per_category=2,
        seed=1337,
        dataset_name="fixture-dataset",
        lowercase=False,
        force=False,
        converter=FakeConverter(),
        created_at=datetime(2026, 3, 22, tzinfo=timezone.utc),
    )

    assert manifest["schema_version"] == 1
    assert manifest["categories"] == ["Email", "Memo"]
    assert manifest["params"]["per_category"] == 2
    assert manifest["params"]["seed"] == 1337
    assert len(manifest["items"]) == 4

    for item in manifest["items"]:
        image_path = out_dir / item["rel_image_path"]
        expected_text_path = out_dir / item["rel_expected_text_path"]
        assert image_path.exists()
        assert expected_text_path.exists()
        assert expected_text_path.read_text(encoding="utf-8").endswith("\n")
        assert "OCR for" in expected_text_path.read_text(encoding="utf-8")


def test_build_validation_set_redacts_ssn_like_text(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    category_dir = dataset_root / "Resume"
    category_dir.mkdir(parents=True)
    for index in range(2):
        make_jpeg(category_dir / f"resume-{index}.jpg")

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del path, encoding, ocr_strict
            return SimpleNamespace(content="SSN: 123-45-6789")

    out_dir = tmp_path / "out"
    manifest = module.build_validation_set(
        dataset_root=dataset_root,
        out_dir=out_dir,
        categories=["Resume"],
        per_category=1,
        seed=1337,
        dataset_name="fixture-dataset",
        lowercase=False,
        force=False,
        converter=FakeConverter(),
        created_at=datetime(2026, 3, 22, tzinfo=timezone.utc),
    )

    expected_text_path = out_dir / manifest["items"][0]["rel_expected_text_path"]
    assert expected_text_path.read_text(encoding="utf-8") == "SSN: 000-00-0000\n"


def test_build_validation_set_requires_force_for_existing_output_dir(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    category_dir = dataset_root / "Email"
    category_dir.mkdir(parents=True)
    for index in range(2):
        make_jpeg(category_dir / f"email-{index}.jpg")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del path, encoding, ocr_strict
            return SimpleNamespace(content="fixture")

    try:
        module.build_validation_set(
            dataset_root=dataset_root,
            out_dir=out_dir,
            categories=["Email"],
            per_category=1,
            seed=7,
            dataset_name="fixture-dataset",
            lowercase=False,
            force=False,
            converter=FakeConverter(),
        )
    except ValueError as exc:
        assert "--force" in str(exc)
    else:
        raise AssertionError("Expected build_validation_set to require --force.")


def test_build_validation_set_rejects_force_when_output_path_is_a_file(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    category_dir = dataset_root / "Email"
    category_dir.mkdir(parents=True)
    for index in range(2):
        make_jpeg(category_dir / f"email-{index}.jpg")

    out_path = tmp_path / "out"
    out_path.write_text("not a directory", encoding="utf-8")

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del path, encoding, ocr_strict
            return SimpleNamespace(content="fixture")

    try:
        module.build_validation_set(
            dataset_root=dataset_root,
            out_dir=out_path,
            categories=["Email"],
            per_category=1,
            seed=7,
            dataset_name="fixture-dataset",
            lowercase=False,
            force=True,
            converter=FakeConverter(),
        )
    except ValueError as exc:
        assert "is not a directory" in str(exc)
    else:
        raise AssertionError("Expected build_validation_set to reject a file output path.")


def test_shrink_image_copies_small_jpeg_unchanged(tmp_path: Path) -> None:
    module = load_builder_module()
    src = tmp_path / "small.jpg"
    make_jpeg(src, width=10, height=10)
    original_bytes = src.read_bytes()

    dest = tmp_path / "dest.jpg"
    module.shrink_image(src, dest, max_bytes=200_000, max_dim=1920)

    assert dest.exists()
    assert dest.read_bytes() == original_bytes


def test_shrink_image_rescales_oversized_jpeg(tmp_path: Path) -> None:
    module = load_builder_module()
    src = tmp_path / "big.jpg"
    # Create a JPEG clearly wider than the max_dim threshold
    img = Image.new("RGB", (500, 200), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    src.write_bytes(buf.getvalue())

    dest = tmp_path / "dest.jpg"
    module.shrink_image(src, dest, max_bytes=200_000, max_dim=100)

    assert dest.exists()
    with Image.open(dest) as result:
        assert max(result.size) <= 100


def test_shrink_image_recompresses_oversize_byte_jpeg(tmp_path: Path) -> None:
    module = load_builder_module()
    src = tmp_path / "heavy.jpg"
    # Create a large JPEG clearly over a tiny byte limit by using a high-quality
    # render of a large solid-colour image (300×300 pixels at JPEG quality=100).
    # Solid colour at quality=100 still produces a file that exceeds 1 KB.
    img = Image.new("RGB", (300, 300), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=100)
    src.write_bytes(buf.getvalue())
    src_size = src.stat().st_size

    # Use a byte limit that the source file definitely exceeds
    byte_limit = src_size - 1
    assert byte_limit >= 1

    dest = tmp_path / "dest.jpg"
    module.shrink_image(src, dest, max_bytes=byte_limit, max_dim=1920)

    assert dest.exists()
    # Result should be strictly smaller than the source (was recompressed at lower quality)
    assert dest.stat().st_size < src_size


def test_shrink_image_records_in_manifest(tmp_path: Path) -> None:
    """build_validation_set records size_bytes from the (possibly shrunken) dest file."""
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    category_dir = dataset_root / "Note"
    category_dir.mkdir(parents=True)
    # Two large images (300×300 at quality=100 will be > DEFAULT_MAX_IMAGE_BYTES for a solid fill)
    for index in range(2):
        img = Image.new("RGB", (300, 300), color=(index * 50, 100, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=100)
        (category_dir / f"note-{index}.jpg").write_bytes(buf.getvalue())

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del path, encoding, ocr_strict
            return SimpleNamespace(content="text")

    out_dir = tmp_path / "out"
    manifest = module.build_validation_set(
        dataset_root=dataset_root,
        out_dir=out_dir,
        categories=["Note"],
        per_category=1,
        seed=1337,
        dataset_name="fixture-dataset",
        lowercase=False,
        force=False,
        max_image_bytes=module.DEFAULT_MAX_IMAGE_BYTES,
        max_image_dim=module.DEFAULT_MAX_IMAGE_DIM,
        converter=FakeConverter(),
        created_at=datetime(2026, 3, 22, tzinfo=timezone.utc),
    )

    assert manifest["params"]["max_image_bytes"] == module.DEFAULT_MAX_IMAGE_BYTES
    assert manifest["params"]["max_image_dim"] == module.DEFAULT_MAX_IMAGE_DIM
    for item in manifest["items"]:
        dest = out_dir / item["rel_image_path"]
        assert dest.stat().st_size == item["size_bytes"]


def test_shrink_image_copies_small_png_unchanged(tmp_path: Path) -> None:
    module = load_builder_module()
    src = tmp_path / "small.png"
    img = Image.new("RGB", (10, 10), color=(0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    src.write_bytes(buf.getvalue())
    original_bytes = src.read_bytes()

    dest = tmp_path / "dest.png"
    module.shrink_image(src, dest, max_bytes=200_000, max_dim=1920)

    assert dest.exists()
    assert dest.read_bytes() == original_bytes


def test_parse_args_default_size_policy(tmp_path: Path) -> None:
    module = load_builder_module()
    # parse_args requires --dataset-root and --out-dir
    args = module.parse_args(["--dataset-root", str(tmp_path), "--out-dir", str(tmp_path / "out")])
    assert args.max_image_bytes == module.DEFAULT_MAX_IMAGE_BYTES
    assert args.max_image_dim == module.DEFAULT_MAX_IMAGE_DIM


def test_parse_args_custom_size_policy(tmp_path: Path) -> None:
    module = load_builder_module()
    args = module.parse_args(
        [
            "--dataset-root",
            str(tmp_path),
            "--out-dir",
            str(tmp_path / "out"),
            "--max-image-bytes",
            "50000",
            "--max-image-dim",
            "800",
        ]
    )
    assert args.max_image_bytes == 50_000
    assert args.max_image_dim == 800
