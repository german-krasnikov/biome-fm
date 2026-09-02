"""Entry point for biome-fm."""

import sys

if len(sys.argv) > 1:
    from biome_fm.cli.cli import UNHANDLED, dispatch

    _result = dispatch(sys.argv[1:])
    if _result is not UNHANDLED:
        sys.exit(_result)


def _show(qt_app, window) -> None:
    """Show the main window; glass when configured and working, plain otherwise."""
    if getattr(window, "_glass_cfg", False):
        from biome_fm.views.glass import enable_glass, prepare_glass
        from biome_fm.views.glass_style import GlassStyle, unmark_glass
        qt_app.setStyle(GlassStyle())
        if prepare_glass(window) and enable_glass(window):
            return
        unmark_glass(window, recursive=True)
        qt_app.setStyle("Fusion")
    window.show()


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from biome_fm.app import create_app
    from biome_fm.views.theme import apply_theme

    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")
    apply_theme(qt_app)
    window = create_app()
    _show(qt_app, window)
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
