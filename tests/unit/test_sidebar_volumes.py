"""TDD tests for Item #44 — Volume/Device Sidebar enhancements."""
from pathlib import Path
from unittest.mock import MagicMock


def test_set_volumes_label_includes_free_space(qtbot, monkeypatch):
    """set_volumes must include 'free' in the child label."""
    from biome_fm.views import sidebar_panel as sp_mod

    # Mock QStorageInfo so test doesn't depend on real mounts
    mock_info = MagicMock()
    mock_info.bytesAvailable.return_value = 10 * 1_073_741_824  # 10 GB
    monkeypatch.setattr(sp_mod, "QStorageInfo", lambda p: mock_info)

    from biome_fm.views.sidebar_panel import SidebarPanel
    panel = SidebarPanel()
    qtbot.addWidget(panel)
    panel.set_volumes([Path("/Volumes/USB")])

    vol_section = panel._tree.topLevelItem(0)
    child = vol_section.child(0)
    assert "free" in child.text(0).lower()


def test_eject_signal_fires(qtbot, monkeypatch):
    """volume_eject_requested signal must exist and carry Path."""
    from biome_fm.views import sidebar_panel as sp_mod

    mock_info = MagicMock()
    mock_info.bytesAvailable.return_value = 0
    monkeypatch.setattr(sp_mod, "QStorageInfo", lambda p: mock_info)

    from biome_fm.views.sidebar_panel import SidebarPanel
    panel = SidebarPanel()
    qtbot.addWidget(panel)
    panel.set_volumes([Path("/Volumes/USB")])

    received: list[Path] = []
    panel.volume_eject_requested.connect(received.append)

    vol_section = panel._tree.topLevelItem(0)
    item = vol_section.child(0)
    panel.volume_eject_requested.emit(item.data(0, 256))

    assert received == [Path("/Volumes/USB")]


def test_volume_watcher_signals_update_sidebar(qapp, monkeypatch):
    """volume_added from VolumeWatcher must call sidebar.set_volumes."""
    import biome_fm.models.volume_watcher as vw_mod

    # _known = {A}, _poll returns {A, B} → volume_added(B) fires
    monkeypatch.setattr(vw_mod, "_list_volumes", lambda: {Path("/vol/A"), Path("/vol/B")})

    from biome_fm.models.volume_watcher import VolumeWatcher
    sidebar = MagicMock()
    vol_set: set[Path] = {Path("/vol/A")}

    watcher = VolumeWatcher(interval_ms=50)
    watcher.volume_added.connect(lambda p: (vol_set.add(p), sidebar.set_volumes(sorted(vol_set))))
    watcher._known = {Path("/vol/A")}
    watcher._poll()

    sidebar.set_volumes.assert_called_once_with([Path("/vol/A"), Path("/vol/B")])
