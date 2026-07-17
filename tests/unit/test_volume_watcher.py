"""Unit tests for VolumeWatcher hot-plug detection."""
from pathlib import Path


def test_detects_new_volume(qapp, monkeypatch):
    import biome_fm.models.volume_watcher as vw
    monkeypatch.setattr(vw, "_list_volumes", lambda: {Path("/Volumes/USB")})
    from biome_fm.models.volume_watcher import VolumeWatcher
    w = VolumeWatcher()
    w._known = set()
    added: list[Path] = []
    w.volume_added.connect(added.append)
    w._poll()
    assert Path("/Volumes/USB") in added


def test_detects_removed_volume(qapp, monkeypatch):
    import biome_fm.models.volume_watcher as vw
    monkeypatch.setattr(vw, "_list_volumes", lambda: set())
    from biome_fm.models.volume_watcher import VolumeWatcher
    w = VolumeWatcher()
    w._known = {Path("/Volumes/OLD")}
    removed: list[Path] = []
    w.volume_removed.connect(removed.append)
    w._poll()
    assert Path("/Volumes/OLD") in removed
