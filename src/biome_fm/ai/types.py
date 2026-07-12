"""Shared content-part types for multi-modal AI messages."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageContent:
    data: str  # base64-encoded bytes
    media_type: str = "image/png"


@dataclass(frozen=True)
class FileContent:
    path: Path
    content: str  # pre-read text


type ContentPart = str | ImageContent | FileContent
