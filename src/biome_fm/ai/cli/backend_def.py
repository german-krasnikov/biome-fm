"""Backend definitions for CLI-based AI providers."""
from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from biome_fm.ai.cli.stream_parse import parse_claude_code_line, parse_codex_line, parse_plain_line

if TYPE_CHECKING:
    from biome_fm.ai.cli.cli_provider import CliProvider


@dataclass(frozen=True)
class BackendDef:
    name: str
    binary: str
    models: tuple[str, ...]
    build_argv: Callable[[str, str], list[str]]  # (prompt, model) -> argv
    parse_line: Callable[[str], str | None]

    def resolve_binary(self) -> str | None:
        return shutil.which(self.binary)


CLAUDE_CODE = BackendDef(
    name="claude-code",
    binary="claude",
    models=("claude-sonnet-4-20250514", "claude-opus-4-20250514"),
    build_argv=lambda p, m: ["claude", "-p", p, "--model", m, "--output-format", "stream-json"],
    parse_line=parse_claude_code_line,
)

CODEX = BackendDef(
    name="codex",
    binary="codex",
    models=("o4-mini", "gpt-4.1"),
    build_argv=lambda p, m: ["codex", "--model", m, "--", p],
    parse_line=parse_codex_line,
)

OPENCODE = BackendDef(
    name="opencode",
    binary="opencode",
    models=("anthropic/claude-sonnet-4-5", "openai/gpt-4.1"),
    build_argv=lambda p, m: ["opencode", "run", "--model", m, "-p", p],
    parse_line=parse_plain_line,
)

ALL_BACKENDS: list[BackendDef] = [CLAUDE_CODE, CODEX, OPENCODE]


def make_cli_providers() -> dict[str, CliProvider]:
    """Return only backends whose binary is on PATH."""
    from biome_fm.ai.cli.cli_provider import CliProvider  # lazy to avoid circular
    return {b.name: CliProvider(b) for b in ALL_BACKENDS if b.resolve_binary() is not None}
