class QuickViewState:
    def __init__(self) -> None:
        self._active = False
        self._saved_sizes: tuple[int, int] | None = None

    @property
    def active(self) -> bool:
        return self._active

    def toggle(self, current_sizes: tuple[int, int]) -> tuple[int, int]:
        if self._active:
            self._active = False
            sizes = self._saved_sizes or current_sizes
            self._saved_sizes = None
            return sizes
        self._active = True
        self._saved_sizes = current_sizes
        return (current_sizes[0] + current_sizes[1], 0)
