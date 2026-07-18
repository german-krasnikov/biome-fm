"""F201 — Multi-Rename Case Conversion: [TOKEN:modifier] syntax."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.presenters.rename_template import expand_template


@pytest.fixture()
def f(tmp_path: Path) -> Path:
    p = tmp_path / "hello world.txt"
    p.touch()
    return p


class TestCaseModifier:
    def test_upper_modifier(self, f: Path) -> None:
        assert expand_template("[N:upper]", f, 0) == "HELLO WORLD"

    def test_lower_modifier(self, tmp_path: Path) -> None:
        p = tmp_path / "HELLO.txt"
        p.touch()
        assert expand_template("[N:lower]", p, 0) == "hello"

    def test_title_modifier(self, f: Path) -> None:
        assert expand_template("[N:title]", f, 0) == "Hello World"

    def test_no_modifier_unchanged(self, f: Path) -> None:
        assert expand_template("[N]", f, 0) == "hello world"

    def test_ext_upper_modifier(self, tmp_path: Path) -> None:
        p = tmp_path / "file.txt"
        p.touch()
        assert expand_template("[E:upper]", p, 0) == "TXT"
