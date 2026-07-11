"""Application bootstrap and DI wiring."""

from pathlib import Path

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.pane_presenter import PanePresenter
from biome_fm.views.main_window import MainWindow
from biome_fm.views.pane_view import PaneView


def create_app() -> MainWindow:
    vfs = LocalVFS()
    left_view = PaneView()
    right_view = PaneView()

    left_p = PanePresenter(view=left_view, vfs=vfs)
    right_p = PanePresenter(view=right_view, vfs=vfs)

    left_view.item_activated.connect(left_p.on_item_activated)
    left_view.path_change_requested.connect(left_p.navigate_to)
    right_view.item_activated.connect(right_p.on_item_activated)
    right_view.path_change_requested.connect(right_p.navigate_to)

    window = MainWindow(left_view, right_view)

    home = Path.home()
    left_p.navigate_to(home)
    right_p.navigate_to(home)

    return window
