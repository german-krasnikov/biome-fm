"""Unit tests for DiskUsageWidget."""
from pathlib import Path
import shutil
from collections import namedtuple


_Usage = namedtuple("Usage", ["total", "used", "free"])


def test_percentage_correct(qapp, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda _: _Usage(100, 60, 40))
    from biome_fm.views.disk_usage_widget import DiskUsageWidget
    w = DiskUsageWidget()
    w.update_path(Path("/"))
    assert w.value() == 60


def test_tooltip_shows_free(qapp, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda _: _Usage(100 * 1024**3, 60 * 1024**3, 40 * 1024**3))
    from biome_fm.views.disk_usage_widget import DiskUsageWidget
    w = DiskUsageWidget()
    w.update_path(Path("/"))
    assert "40" in w.toolTip()
