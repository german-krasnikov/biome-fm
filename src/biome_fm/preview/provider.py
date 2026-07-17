"""Preview provider protocol and data types."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol


class ContentKind(Enum):
    IMAGE = auto()
    TEXT = auto()
    HTML = auto()
    MARKDOWN = auto()
    ERROR = auto()


class PreviewMode(Enum):
    AUTO = auto()
    TEXT = auto()
    HEX = auto()
    RAW = auto()
    GIT_LOG = auto()
    GIT_BLAME = auto()


@dataclass(frozen=True, slots=True)
class PreviewRequest:
    path: Path
    dark: bool = True


@dataclass(frozen=True, slots=True)
class PreviewResult:
    kind: ContentKind
    data: str | bytes
    title: str = ""


class PreviewProvider(Protocol):
    priority: int

    def can_handle(self, path: Path) -> bool: ...

    def render(self, req: PreviewRequest) -> PreviewResult:
        """Called in background thread. Must not touch Qt widgets."""
        ...
