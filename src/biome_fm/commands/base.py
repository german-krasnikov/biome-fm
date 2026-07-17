"""Base command and history for undo/redo."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Command(ABC):
    undoable: bool = True

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...

    @property
    def description(self) -> str:
        return self.__class__.__name__


class CommandHistory:
    def __init__(self, max_depth: int = 50) -> None:
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
        self._max_depth = max_depth
        self.on_changed = None  # Callable[[], None] | None — set by app to update UI labels

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        if cmd.undoable:
            self._undo_stack.append(cmd)
            if len(self._undo_stack) > self._max_depth:
                self._undo_stack.pop(0)
        self._redo_stack.clear()
        if self.on_changed:
            self.on_changed()

    def push(self, cmd: Command) -> None:
        """Record an already-executed command for undo (no execute call)."""
        if not cmd.undoable:
            return
        self._undo_stack.append(cmd)
        if len(self._undo_stack) > self._max_depth:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        if self.on_changed:
            self.on_changed()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        if self.on_changed:
            self.on_changed()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        if self.on_changed:
            self.on_changed()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)
