"""Tests for BackendDef discovery."""
from unittest.mock import patch

import pytest

from biome_fm.ai.cli.backend_def import ALL_BACKENDS, CLAUDE_CODE, CODEX, OPENCODE, make_cli_providers


def test_resolve_binary_found():
    with patch("shutil.which", return_value="/usr/bin/claude"):
        assert CLAUDE_CODE.resolve_binary() == "/usr/bin/claude"


def test_resolve_binary_missing():
    with patch("shutil.which", return_value=None):
        assert CLAUDE_CODE.resolve_binary() is None


def test_make_cli_providers_empty():
    with patch("shutil.which", return_value=None):
        assert make_cli_providers() == {}


def test_make_cli_providers_finds_claude():
    def fake_which(binary):
        return "/usr/bin/claude" if binary == "claude" else None

    with patch("shutil.which", side_effect=fake_which):
        providers = make_cli_providers()
    assert "claude-code" in providers
    assert "codex" not in providers
    assert "opencode" not in providers


def test_all_backends_count():
    assert len(ALL_BACKENDS) == 3


def test_build_argv_claude():
    argv = CLAUDE_CODE.build_argv("hello", "claude-sonnet-4-20250514")
    assert argv[0] == "claude"
    assert "--output-format" in argv
    assert "stream-json" in argv


def test_build_argv_codex():
    argv = CODEX.build_argv("hello", "o4-mini")
    assert argv[0] == "codex"
    assert "hello" in argv


def test_build_argv_opencode():
    argv = OPENCODE.build_argv("hello", "openai/gpt-4.1")
    assert argv[0] == "opencode"
    assert "hello" in argv
