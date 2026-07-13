"""Tests for CliProvider — subprocess mocked, no real binary needed."""
import io
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.ai.cli.backend_def import CLAUDE_CODE
from biome_fm.ai.cli.cli_provider import CliProvider


def _make_provider(binary_found: bool = True) -> CliProvider:
    with patch("shutil.which", return_value="/usr/bin/claude" if binary_found else None):
        return CliProvider(CLAUDE_CODE)


def _mock_popen(lines: list[str]):
    """Return a mock Popen whose stdout yields encoded lines."""
    import json
    proc = MagicMock()
    encoded = [json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": t}]},
    }).encode() + b"\n" for t in lines]
    proc.stdout.__iter__ = MagicMock(return_value=iter(encoded))
    proc.terminate = MagicMock()
    proc.wait = MagicMock()
    proc.kill = MagicMock()
    proc.stderr.read.return_value = b""
    return proc


def test_chat_stream_yields_tokens():
    proc = _mock_popen(["Hello", " world"])
    with patch("subprocess.Popen", return_value=proc):
        provider = CliProvider(CLAUDE_CODE)
        tokens = list(provider.chat_stream([{"role": "user", "content": "hi"}]))
    assert tokens == ["Hello", " world"]


def test_chat_stream_terminates_on_close():
    proc = _mock_popen(["tok1", "tok2", "tok3"])
    with patch("subprocess.Popen", return_value=proc):
        provider = CliProvider(CLAUDE_CODE)
        gen = provider.chat_stream([{"role": "user", "content": "hi"}])
        next(gen)  # consume one
        gen.close()  # trigger finally
    proc.terminate.assert_called_once()
    proc.wait.assert_called()


def test_available_false_when_no_binary():
    with patch("shutil.which", return_value=None):
        provider = CliProvider(CLAUDE_CODE)
    assert provider.available is False


def test_available_true_when_binary_found():
    with patch("shutil.which", return_value="/usr/bin/claude"):
        provider = CliProvider(CLAUDE_CODE)
    assert provider.available is True


def test_set_model():
    provider = CliProvider(CLAUDE_CODE)
    provider.set_model("claude-opus-4-20250514")
    assert provider.active_model == "claude-opus-4-20250514"


def test_build_prompt_flattens():
    provider = CliProvider(CLAUDE_CODE)
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Bye"},
    ]
    prompt = provider._build_prompt(messages, system="Be helpful")
    assert "Hello" in prompt
    assert "Hi" in prompt
    assert "Bye" in prompt
    assert "Be helpful" in prompt


def test_chat_delegates_to_stream():
    proc = _mock_popen(["answer"])
    with patch("subprocess.Popen", return_value=proc):
        provider = CliProvider(CLAUDE_CODE)
        result = provider.chat([{"role": "user", "content": "hi"}])
    assert result == "answer"


def test_chat_stream_binary_missing_yields_error():
    provider = CliProvider(CLAUDE_CODE)
    with patch("subprocess.Popen", side_effect=FileNotFoundError("not found")):
        tokens = list(provider.chat_stream([{"role": "user", "content": "hi"}]))
    assert any("Error" in t for t in tokens)
