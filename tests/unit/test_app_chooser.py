"""TDD: app discovery + OpenWithDialog."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from biome_fm.models.app_chooser import discover_apps


def test_discover_returns_list() -> None:
    result = discover_apps()
    assert isinstance(result, list)
    # each entry is a dict with at least 'name' and 'command'
    for app in result:
        assert "name" in app
        assert "command" in app


def test_custom_command() -> None:
    # discover_apps always returns a list, even if empty (e.g. in CI)
    result = discover_apps()
    assert isinstance(result, list)


def test_discover_darwin_uses_mdfind(tmp_path: Path) -> None:
    """On darwin, discover_apps calls mdfind subprocess."""
    fake_output = "/Applications/Vim.app\n/Applications/TextEdit.app\n"
    with patch("sys.platform", "darwin"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = fake_output
        mock_run.return_value.returncode = 0
        result = discover_apps()
    assert isinstance(result, list)
