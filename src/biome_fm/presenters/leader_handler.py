from collections.abc import Callable


class LeaderHandler:
    def __init__(self) -> None:
        self._bindings: dict[str, Callable] = {}
        self._buffer: str = ""

    def register(self, sequence: str, action: Callable) -> None:
        self._bindings[sequence] = action

    def feed(self, key: str) -> str:
        """Feed a key. Returns 'pending', 'triggered', or 'reset'."""
        self._buffer += key
        if self._buffer in self._bindings:
            action = self._bindings[self._buffer]
            self._buffer = ""
            action()
            return "triggered"
        if any(seq.startswith(self._buffer) for seq in self._bindings):
            return "pending"
        self._buffer = ""
        return "reset"

    def reset(self) -> None:
        self._buffer = ""

    def available(self) -> list[tuple[str, str]]:
        """Return (remaining_keys, sequence) for current prefix."""
        return [(seq[len(self._buffer):], seq) for seq in self._bindings if seq.startswith(self._buffer)]
