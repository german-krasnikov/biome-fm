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


# --- Extended protocol tests ---

def test_noop_provider_has_required_attrs():
    from biome_fm.ai.provider import NoOpProvider
    p = NoOpProvider()
    assert p.name == "none"
    assert p.models == []
    assert p.active_model == ""
    assert not p.available
    assert p.chat([]) == ""
    assert list(p.chat_stream([])) == []


def test_noop_set_model():
    from biome_fm.ai.provider import NoOpProvider
    p = NoOpProvider()
    p.set_model("x")  # should not raise


def test_claude_provider_has_models():
    from biome_fm.ai.claude_provider import ClaudeProvider
    assert "claude-sonnet-4-20250514" in ClaudeProvider.models


def test_claude_normalize_text_message():
    from biome_fm.ai.claude_provider import ClaudeProvider
    provider = ClaudeProvider.__new__(ClaudeProvider)
    provider._client = MagicMock()
    provider._model = "test"
    provider.active_model = "test"
    result = provider._normalize_messages([{"role": "user", "content": "hello"}])
    assert result == [{"role": "user", "content": "hello"}]


def test_claude_normalize_image_content():
    from biome_fm.ai.claude_provider import ClaudeProvider
    from biome_fm.ai.types import ImageContent
    provider = ClaudeProvider.__new__(ClaudeProvider)
    provider._client = MagicMock()
    provider._model = "test"
    provider.active_model = "test"
    msg = {"role": "user", "content": [ImageContent(data="abc", media_type="image/png")]}
    result = provider._normalize_messages([msg])
    assert result[0]["content"][0]["type"] == "image"
    assert result[0]["content"][0]["source"]["data"] == "abc"


def test_claude_normalize_file_content():
    from pathlib import Path

    from biome_fm.ai.claude_provider import ClaudeProvider
    from biome_fm.ai.types import FileContent
    provider = ClaudeProvider.__new__(ClaudeProvider)
    provider._client = MagicMock()
    provider._model = "test"
    provider.active_model = "test"
    msg = {"role": "user", "content": [FileContent(path=Path("test.py"), content="x=1")]}
    result = provider._normalize_messages([msg])
    assert result[0]["content"][0]["type"] == "text"
    assert "[test.py]" in result[0]["content"][0]["text"]
    assert "x=1" in result[0]["content"][0]["text"]


def test_make_providers_no_keys_returns_noop(monkeypatch):
    from biome_fm.ai.provider import make_providers
    from biome_fm.config import Config
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Patch out ollama import so it fails
    with patch.dict("sys.modules", {"httpx": None}):
        cfg = Config()
        result = make_providers(cfg)
    assert "none" in result or any(p.name == "none" for p in result.values())


def test_noop_chat_stream_returns_empty_iter():
    from biome_fm.ai.provider import NoOpProvider
    p = NoOpProvider()
    result = list(p.chat_stream([{"role": "user", "content": "x"}]))
    assert result == []
