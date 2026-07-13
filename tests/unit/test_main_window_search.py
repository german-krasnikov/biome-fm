"""Test MainWindow search signal."""


def test_main_window_has_search_signal():
    from biome_fm.views.main_window import MainWindow
    assert hasattr(MainWindow, "search_requested")
