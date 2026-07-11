"""Application bootstrap and DI wiring."""

from biome_fm.views.main_window import MainWindow


def create_app() -> MainWindow:
    return MainWindow()
