"""ScriptingEngine — exec Python in a BiomeContext namespace."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_fm.scripting.context import BiomeContext


class ScriptError(Exception):
    pass


class ScriptingEngine:
    def __init__(self, context: "BiomeContext") -> None:
        self._ctx = context

    def exec_code(self, source: str) -> None:
        namespace = {"biome": self._ctx, "__builtins__": __builtins__}
        try:
            exec(compile(source, "<script>", "exec"), namespace)  # noqa: S102
        except SyntaxError as e:
            raise ScriptError(f"Syntax error at line {e.lineno}: {e.msg}") from e
        except Exception as e:
            raise ScriptError(str(e)) from e
