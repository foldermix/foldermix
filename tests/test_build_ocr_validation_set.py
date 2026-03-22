from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


def load_builder_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_ocr_validation_set.py"
    spec = importlib.util.spec_from_file_location("build_ocr_validation_set", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load build_ocr_validation_set.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_validation_set_creates_manifest_images_and_goldens(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    for category in ("Email", "Memo"):
        category_dir = dataset_root / category
        category_dir.mkdir(parents=True)
        for index in range(3):
            (category_dir / f"{category.lower()}-{index}.jpg").write_bytes(
                f"{category}-{index}".encode()
            )

    class FakeConverter:
        def convert(self, path: Path, encoding: str = "utf-8", *, ocr_strict: bool = False):
            del encoding, ocr_strict
            return SimpleNamespace(content=f" OCR\tfor {path.stem} \r\n")

    out_dir = tmp_path / "out"
    manifest, warnings = module.build_validation_set(
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

    assert warnings == []
    assert manifest["schema_version"] == 1
    assert manifest["categories"] == ["Email", "Memo"]
    assert manifest["params"] == {"per_category": 2, "seed": 1337}
    assert len(manifest["items"]) == 4

    for item in manifest["items"]:
        image_path = out_dir / item["rel_image_path"]
        expected_text_path = out_dir / item["rel_expected_text_path"]
        assert image_path.exists()
        assert expected_text_path.exists()
        assert expected_text_path.read_text(encoding="utf-8").endswith("\n")
        assert "OCR for" in expected_text_path.read_text(encoding="utf-8")


def test_build_validation_set_requires_force_for_existing_output_dir(tmp_path: Path) -> None:
    module = load_builder_module()

    dataset_root = tmp_path / "dataset"
    category_dir = dataset_root / "Email"
    category_dir.mkdir(parents=True)
    for index in range(2):
        (category_dir / f"email-{index}.jpg").write_bytes(b"fixture")

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
