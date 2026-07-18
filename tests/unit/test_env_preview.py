"""Unit tests for EnvFileProvider (F058)."""
import pytest
from pathlib import Path
from biome_fm.preview.providers.dotenv import EnvFileProvider
from biome_fm.preview.provider import ContentKind, PreviewRequest


@pytest.fixture
def provider():
    return EnvFileProvider()


def test_can_handle_env(provider):
    assert provider.can_handle(Path(".env")) is True


def test_can_handle_env_local(provider):
    assert provider.can_handle(Path(".env.local")) is True


def test_can_handle_env_production(provider):
    assert provider.can_handle(Path(".env.production")) is True


def test_cannot_handle_py(provider):
    assert provider.can_handle(Path("script.py")) is False


def test_values_masked(provider, tmp_path):
    f = tmp_path / ".env"
    f.write_text("API_KEY=secret123\n")
    result = provider.render(PreviewRequest(path=f))
    assert result.data == "API_KEY=***\n"
    assert result.kind == ContentKind.TEXT


def test_comments_preserved(provider, tmp_path):
    f = tmp_path / ".env"
    f.write_text("# comment\n")
    result = provider.render(PreviewRequest(path=f))
    assert result.data == "# comment\n"


def test_empty_value_not_masked(provider, tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=\n")
    result = provider.render(PreviewRequest(path=f))
    assert result.data == "KEY=\n"


def test_export_prefix_handled(provider, tmp_path):
    f = tmp_path / ".env"
    f.write_text("export FOO=bar\n")
    result = provider.render(PreviewRequest(path=f))
    assert result.data == "export FOO=***\n"
