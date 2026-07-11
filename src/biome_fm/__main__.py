"""Entry point for biome-fm."""

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from biome_fm.app import create_app
    from biome_fm.views.theme import apply_theme

    qt_app = QApplication(sys.argv)
    apply_theme(qt_app)
    window = create_app()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
