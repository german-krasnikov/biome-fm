"""Base command."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @property
    def description(self) -> str:
        return self.__class__.__name__

    def preview(self) -> list[str]:
        """Human-readable lines describing what execute() will do."""
        return [self.description]
