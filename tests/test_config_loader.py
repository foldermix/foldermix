from __future__ import annotations

from pathlib import Path

import pytest

from foldermix.config_loader import ConfigLoadError, load_command_config


def test_load_command_config_from_tool_section(tmp_path: Path) -> None:
    config_path = tmp_path / "foldermix.toml"
    config_path.write_text(
        "\n".join(
            [
                "[tool.foldermix.pack]",
                'format = "xml"',
                "workers = 2",
                'include_ext = [".py", ".md"]',
                "include_toc = false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    values, used_path = load_command_config("pack", root=tmp_path, config_path=config_path)

    assert used_path == config_path
    assert values["format"] == "xml"
    assert values["workers"] == 2
    assert values["include_ext"] == [".py", ".md"]
    assert values["include_toc"] is False


def test_load_command_config_discovers_parent_file(tmp_path: Path) -> None:
    config_path = tmp_path / "foldermix.toml"
    config_path.write_text(
        "\n".join(
            [
                "[list]",
                "hidden = true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    values, used_path = load_command_config("list", root=nested, config_path=None)

    assert used_path == config_path
    assert values["hidden"] is True


def test_load_command_config_rejects_invalid_types(tmp_path: Path) -> None:
    config_path = tmp_path / "foldermix.toml"
    config_path.write_text(
        "\n".join(
            [
                "[pack]",
                'workers = "fast"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError) as exc:
        load_command_config("pack", root=tmp_path, config_path=config_path)

    message = str(exc.value)
    assert "Invalid config at" in message
    assert "workers: expected an integer" in message


def test_load_command_config_rejects_unknown_key(tmp_path: Path) -> None:
    config_path = tmp_path / "foldermix.toml"
    config_path.write_text(
        "\n".join(
            [
                "[stats]",
                "unknown = 1",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError) as exc:
        load_command_config("stats", root=tmp_path, config_path=config_path)

    assert "unknown key" in str(exc.value)
