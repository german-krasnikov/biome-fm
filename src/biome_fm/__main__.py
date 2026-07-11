"""Entry point for biome-fm."""

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from biome_fm.app import create_app

    qt_app = QApplication(sys.argv)
    window = create_app()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
