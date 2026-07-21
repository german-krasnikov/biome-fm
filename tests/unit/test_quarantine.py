"""Unit tests for macOS quarantine flag helpers."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
class TestQuarantineDarwin:
    def test_has_quarantine_flag_true(self):
        from biome_fm.models.finder_tags import has_quarantine_flag

        with patch("biome_fm.models.finder_tags._getxattr", return_value=b"0001;"):
            assert has_quarantine_flag(Path("/fake/file.app")) is True

    def test_has_quarantine_flag_false(self):
        from biome_fm.models.finder_tags import has_quarantine_flag

        with patch("biome_fm.models.finder_tags._getxattr", side_effect=OSError):
            assert has_quarantine_flag(Path("/fake/file.app")) is False

    def test_remove_quarantine_flag_calls_removexattr(self):
        from biome_fm.models.finder_tags import remove_quarantine_flag, _QUARANTINE_ATTR

        mock_libc = MagicMock()
        mock_libc.removexattr.return_value = 0
        with patch("biome_fm.models.finder_tags._libc", mock_libc):
            remove_quarantine_flag(Path("/fake/file.app"))
        mock_libc.removexattr.assert_called_once_with(b"/fake/file.app", _QUARANTINE_ATTR, 0)

    def test_remove_quarantine_flag_raises_on_failure(self):
        from biome_fm.models.finder_tags import remove_quarantine_flag

        mock_libc = MagicMock()
        mock_libc.removexattr.return_value = -1
        with patch("biome_fm.models.finder_tags._libc", mock_libc):
            with pytest.raises(OSError):
                remove_quarantine_flag(Path("/fake/file.app"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
class TestRemoveQuarantineCmd:
    def test_execute_saves_old_value_and_removes(self):
        from biome_fm.commands.quarantine_cmd import RemoveQuarantineCmd

        p = Path("/fake/file.app")
        with (
            patch("biome_fm.models.finder_tags._getxattr", return_value=b"0001;xyz") as mock_get,
            patch("biome_fm.models.finder_tags.remove_quarantine_flag") as mock_rm,
        ):
            cmd = RemoveQuarantineCmd([p])
            cmd.execute()
        mock_get.assert_called_once_with(str(p), "com.apple.quarantine")
        mock_rm.assert_called_once_with(p)
        assert cmd._removed == [(p, b"0001;xyz")]

    def test_execute_skips_files_without_quarantine(self):
        from biome_fm.commands.quarantine_cmd import RemoveQuarantineCmd

        p = Path("/fake/clean.app")
        with (
            patch("biome_fm.models.finder_tags._getxattr", side_effect=OSError),
            patch("biome_fm.models.finder_tags.remove_quarantine_flag") as mock_rm,
        ):
            cmd = RemoveQuarantineCmd([p])
            cmd.execute()
        mock_rm.assert_not_called()
        assert cmd._removed == []

    def test_undo_restores_xattr(self):
        from biome_fm.commands.quarantine_cmd import RemoveQuarantineCmd

        p = Path("/fake/file.app")
        cmd = RemoveQuarantineCmd([p])
        cmd._removed = [(p, b"0001;xyz")]
        with patch("biome_fm.models.finder_tags._setxattr") as mock_set:
            cmd.undo()
        mock_set.assert_called_once_with(str(p), "com.apple.quarantine", b"0001;xyz")


@pytest.mark.skipif(sys.platform == "darwin", reason="non-macOS stubs only")
class TestQuarantineStubs:
    def test_has_quarantine_flag_returns_false(self):
        from biome_fm.models.finder_tags import has_quarantine_flag

        assert has_quarantine_flag(Path("/any/path")) is False

    def test_remove_quarantine_flag_is_noop(self):
        from biome_fm.models.finder_tags import remove_quarantine_flag

        remove_quarantine_flag(Path("/any/path"))  # must not raise
