"""foldermix - pack a folder into a single LLM-friendly context file."""

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

import tomllib


def _read_version_from_pyproject() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]


try:
    __version__ = package_version("foldermix")
except PackageNotFoundError:
    # Fallback for environments that import source directly without installed metadata.
    __version__ = _read_version_from_pyproject()
