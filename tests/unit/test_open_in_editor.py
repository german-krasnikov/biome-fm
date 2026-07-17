"""TDD tests for open_in_editor (Feature #4 — Open in IDE)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_custom_cmd_called(tmp_path: Path) -> None:
    p = tmp_path / "file.py"
    p.touch()
    with patch("subprocess.Popen") as mock_popen:
        from biome_fm.utils.opener import open_in_editor
        open_in_editor(p, "code -w")
        mock_popen.assert_called_once_with(["code", "-w", str(p)])


def test_empty_cmd_falls_back_to_open(tmp_path: Path) -> None:
    p = tmp_path / "file.txt"
    p.touch()
    with patch("biome_fm.utils.opener.open_file") as mock_open:
        from biome_fm.utils.opener import open_in_editor
        open_in_editor(p, "")
        mock_open.assert_called_once_with(p)


def test_config_has_editor_cmd() -> None:
    from biome_fm.config import Config
    cfg = Config()
    assert cfg.editor_cmd == ""


def test_config_editor_cmd_roundtrip(tmp_path: Path) -> None:
    from biome_fm.config import Config, save_config, load_config
    save_config(Config(editor_cmd="vim"), tmp_path / "cfg.toml")
    assert load_config(tmp_path / "cfg.toml").editor_cmd == "vim"
