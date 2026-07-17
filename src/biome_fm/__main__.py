"""Entry point for biome-fm."""

import sys

if len(sys.argv) > 1:
    from biome_fm.cli.cli import UNHANDLED, dispatch

    _result = dispatch(sys.argv[1:])
    if _result is not UNHANDLED:
        sys.exit(_result)


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from biome_fm.app import create_app
    from biome_fm.views.theme import apply_theme

    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")
    apply_theme(qt_app)
    window = create_app()

    if getattr(window, "_glass_cfg", False):
        from biome_fm.views.glass import enable_glass, prepare_glass
        from biome_fm.views.glass_style import GlassStyle
        qt_app.setStyle(GlassStyle())
        prepare_glass(window)
        enable_glass(window)
    else:
        window.show()

    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
