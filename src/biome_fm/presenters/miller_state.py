from pathlib import Path


class MillerState:
    MAX_COLUMNS = 4

    def __init__(self, root: Path) -> None:
        self._columns: list[Path] = [root]

    @property
    def columns(self) -> list[Path]:
        return list(self._columns)

    @property
    def active_column(self) -> Path:
        return self._columns[-1]

    def select_dir(self, path: Path) -> None:
        self._columns.append(path)
        if len(self._columns) > self.MAX_COLUMNS:
            self._columns.pop(0)

    def go_back(self) -> bool:
        if len(self._columns) <= 1:
            return False
        self._columns.pop()
        return True
