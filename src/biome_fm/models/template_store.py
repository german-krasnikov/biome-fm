"""File templates for new-file creation."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FileTemplate:
    name: str
    ext: str
    content: bytes = field(default=b"")


class TemplateStore:
    BUILTIN: list[FileTemplate] = [
        FileTemplate("Python Script", ".py", b""),
        FileTemplate("Markdown",      ".md", b""),
        FileTemplate("Text File",     ".txt", b""),
    ]

    def all_templates(self) -> list[FileTemplate]:
        return list(self.BUILTIN)
