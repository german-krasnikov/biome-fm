"""Unit tests for Makefile/Justfile target parsing (F295)."""
from __future__ import annotations

from pathlib import Path


def test_parse_makefile_targets(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "all: build test\n"
        "\tbuild something\n"
        "build:\n"
        "\tgcc -o app main.c\n"
        "test: build\n"
        "\t./run_tests.sh\n"
        "clean:\n"
        "\trm -rf build/\n"
    )
    from biome_fm.models.project_detector import parse_makefile_targets

    targets = parse_makefile_targets(makefile)
    assert set(targets) == {"all", "build", "test", "clean"}


def test_parse_justfile_targets(tmp_path: Path) -> None:
    justfile = tmp_path / "Justfile"
    justfile.write_text(
        "build:\n"
        "    cargo build\n"
        "\n"
        "test: build\n"
        "    cargo test\n"
        "\n"
        "run-dev:\n"
        "    cargo run\n"
    )
    from biome_fm.models.project_detector import parse_justfile_targets

    targets = parse_justfile_targets(justfile)
    assert set(targets) == {"build", "test", "run-dev"}


def test_parse_ignores_comments_and_variables(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "# This is a comment\n"
        "CC = gcc\n"
        "CFLAGS := -O2\n"
        ".PHONY: all test\n"
        "all:\n"
        "\t$(CC) main.c\n"
        "test:\n"
        "\techo test\n"
    )
    from biome_fm.models.project_detector import parse_makefile_targets

    targets = parse_makefile_targets(makefile)
    assert ".PHONY" not in targets
    assert "CC" not in targets
    assert "CFLAGS" not in targets
    assert "all" in targets
    assert "test" in targets
