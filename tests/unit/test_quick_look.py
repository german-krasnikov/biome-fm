"""Unit tests for utils/platform quick_look — no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.models.file_item import FileItem
from biome_fm.utils import platform as plat


def _item(name: str, path: Path | None = None) -> FileItem:
    p = path or Path(f"/tmp/{name}")
    return FileItem(name=name, path=p, is_dir=False, size=0, modified=0.0)


def test_quick_look_mac_calls_qlmanage(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    with (
        patch.object(plat, "IS_MAC", True),
        patch.object(plat, "IS_LINUX", False),
        patch.object(plat, "IS_WIN", False),
        patch("subprocess.Popen") as mock_popen,
    ):
        plat.quick_look(target)
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert args == ["qlmanage", "-p", str(target)]


def test_quick_look_linux_calls_xdg_open(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    with (
        patch.object(plat, "IS_MAC", False),
        patch.object(plat, "IS_LINUX", True),
        patch.object(plat, "IS_WIN", False),
        patch("subprocess.Popen") as mock_popen,
    ):
        plat.quick_look(target)
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert args == ["xdg-open", str(target)]


def test_quick_look_skips_dotdot() -> None:
    dotdot = _item("..")
    with patch("biome_fm.utils.platform.quick_look") as mock_ql:
        plat.quick_look_item(dotdot)
    mock_ql.assert_not_called()


def test_quick_look_item_calls_for_real_item(tmp_path: Path) -> None:
    target = tmp_path / "real.txt"
    item = _item("real.txt", target)
    with patch("biome_fm.utils.platform.quick_look") as mock_ql:
        plat.quick_look_item(item)
    mock_ql.assert_called_once_with(target)


def test_quick_look_item_skips_none() -> None:
    with patch("biome_fm.utils.platform.quick_look") as mock_ql:
        plat.quick_look_item(None)
    mock_ql.assert_not_called()
