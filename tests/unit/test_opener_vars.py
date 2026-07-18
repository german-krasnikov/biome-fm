"""F264 — Opener Rule Variables: $f/$d/$s and {} backward compat."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.opener_rules import apply_cmd


import shlex as _shlex


def _q(s: str) -> str:
    return _shlex.quote(s)


class TestApplyCmd:
    def test_apply_cmd_f_variable(self) -> None:
        result = apply_cmd("echo $f", Path("/a/b.txt"), [])
        assert result == f"echo {_q('/a/b.txt')}"

    def test_apply_cmd_d_variable(self) -> None:
        result = apply_cmd("echo $d", Path("/a/b.txt"), [])
        assert result == f"echo {_q('/a')}"

    def test_apply_cmd_s_selection(self) -> None:
        sel = [Path("/a/b.txt"), Path("/a/c.txt")]
        result = apply_cmd("echo $s", Path("/a/b.txt"), sel)
        assert result == f"echo {_q('/a/b.txt')} {_q('/a/c.txt')}"

    def test_apply_cmd_s_no_selection_falls_back_to_f(self) -> None:
        result = apply_cmd("echo $s", Path("/a/b.txt"), [])
        assert result == f"echo {_q('/a/b.txt')}"

    def test_apply_cmd_braces_compat(self) -> None:
        result = apply_cmd("open {}", Path("/a/b.txt"), [])
        assert result == f"open {_q('/a/b.txt')}"

    def test_apply_cmd_path_with_spaces_gets_quoted(self) -> None:
        result = apply_cmd("open $f", Path("/my docs/file name.txt"), [])
        assert result == f"open {_q('/my docs/file name.txt')}"
