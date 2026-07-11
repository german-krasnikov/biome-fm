"""Unit tests for AI providers — no Qt, no real anthropic calls."""
from unittest.mock import MagicMock, patch

from biome_fm.ai.provider import NoOpProvider, make_provider


def test_noop_available_is_false():
    assert NoOpProvider().available is False


def test_noop_chat_returns_empty():
    assert NoOpProvider().chat([{"role": "user", "content": "hi"}]) == ""


def test_make_provider_no_key_returns_noop():
    with patch.dict("os.environ", {}, clear=True):
        p = make_provider()
    assert isinstance(p, NoOpProvider)


def test_make_provider_with_key_returns_claude():
    with patch("biome_fm.ai.provider.ClaudeProvider") as MockClaude:
        MockClaude.return_value = MagicMock()
        p = make_provider(api_key="sk-test")
    assert not isinstance(p, NoOpProvider)


def test_make_provider_import_error_falls_back_to_noop():
    with patch("biome_fm.ai.provider._import_claude", side_effect=ImportError):
        p = make_provider(api_key="sk-test")
    assert isinstance(p, NoOpProvider)


def test_claude_provider_available_is_true():
    mock_client = MagicMock()
    with patch("biome_fm.ai.claude_provider.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        with patch("biome_fm.ai.claude_provider._HAS_ANTHROPIC", True):
            from biome_fm.ai.claude_provider import ClaudeProvider
            p = ClaudeProvider("sk-test")
    assert p.available is True


def test_claude_provider_chat_calls_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="hello")]
    with patch("biome_fm.ai.claude_provider.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        with patch("biome_fm.ai.claude_provider._HAS_ANTHROPIC", True):
            from biome_fm.ai.claude_provider import ClaudeProvider
            p = ClaudeProvider("sk-test")
            result = p.chat([{"role": "user", "content": "hi"}])
    assert result == "hello"


def test_claude_provider_passes_system():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="ok")]
    with patch("biome_fm.ai.claude_provider.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        with patch("biome_fm.ai.claude_provider._HAS_ANTHROPIC", True):
            from biome_fm.ai.claude_provider import ClaudeProvider
            p = ClaudeProvider("sk-test")
            p.chat([{"role": "user", "content": "hi"}], system="be concise")
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs.get("system") == "be concise"
