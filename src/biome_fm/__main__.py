"""Entry point for biome-fm."""

import sys

if len(sys.argv) > 1:
    from biome_fm.mcp.cli import UNHANDLED, dispatch

    _result = dispatch(sys.argv[1:])
    if _result is not UNHANDLED:
        sys.exit(_result)


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from biome_fm.app import create_app
    from biome_fm.views.theme import apply_theme

    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")  # must precede setStyleSheet; fixes native controls on macOS
    apply_theme(qt_app)
    window = create_app()

    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
