"""E2E-style unit tests for CLI provider chain — real JSON shapes, mocked subprocess."""
import json
from unittest.mock import MagicMock, patch

from biome_fm.ai.cli.backend_def import CLAUDE_CODE
from biome_fm.ai.cli.cli_provider import CliProvider
from biome_fm.ai.cli.stream_parse import parse_claude_code_line

# Real JSON shape from `claude --output-format stream-json --verbose`
_REAL_LINE = json.dumps({
    "type": "assistant",
    "message": {
        "model": "claude-sonnet-5",
        "id": "msg_xxx",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello!"}],
        "stop_reason": None,
        "stop_sequence": None,
        "usage": {"input_tokens": 2, "output_tokens": 2},
    },
})


def test_parse_real_claude_code_output():
    assert parse_claude_code_line(_REAL_LINE) == "Hello!"


def test_verbose_flag_in_argv():
    argv = CLAUDE_CODE.build_argv("test prompt", "claude-sonnet-5")
    assert "--verbose" in argv


def _make_proc(stdout_lines, returncode=0):
    proc = MagicMock()
    proc.stdout.__iter__ = MagicMock(return_value=iter(stdout_lines))
    proc.terminate = MagicMock()
    proc.wait = MagicMock()
    proc.kill = MagicMock()
    proc.returncode = returncode
    return proc


def test_cli_provider_real_json_yields_token():
    proc = _make_proc([(_REAL_LINE + "\n").encode()])
    with patch("subprocess.Popen", return_value=proc), \
         patch("builtins.open", MagicMock()):
        tokens = list(CliProvider(CLAUDE_CODE).chat_stream([{"role": "user", "content": "hi"}]))
    assert tokens == ["Hello!"]


def test_error_token_on_nonzero_exit_no_output(tmp_path):
    proc = _make_proc([], returncode=1)
    err_file = tmp_path / "stderr.log"
    err_file.write_text("Error: --verbose flag required")
    with patch("subprocess.Popen", return_value=proc), \
         patch("builtins.open", MagicMock()), \
         patch("biome_fm.ai.cli.cli_provider._STDERR_LOG", err_file):
        tokens = list(CliProvider(CLAUDE_CODE).chat_stream([{"role": "user", "content": "hi"}]))
    assert len(tokens) == 1
    assert "Error" in tokens[0]


def test_no_error_token_on_success_with_tokens():
    proc = _make_proc([(_REAL_LINE + "\n").encode()], returncode=1)
    with patch("subprocess.Popen", return_value=proc), \
         patch("builtins.open", MagicMock()):
        tokens = list(CliProvider(CLAUDE_CODE).chat_stream([{"role": "user", "content": "hi"}]))
    assert tokens == ["Hello!"]
