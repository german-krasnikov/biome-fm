class ColumnState:
    COLUMNS = ("Name", "Size", "Modified", "Kind")

    def __init__(self) -> None:
        self._hidden: set[str] = set()

    def is_visible(self, col: str) -> bool:
        return col not in self._hidden

    def set_visible(self, col: str, visible: bool) -> None:
        if col == "Name":
            return
        if visible:
            self._hidden.discard(col)
        else:
            self._hidden.add(col)

    def toggle(self, col: str) -> None:
        self.set_visible(col, not self.is_visible(col))

    def visible_columns(self) -> list[str]:
        return [c for c in self.COLUMNS if c not in self._hidden]
