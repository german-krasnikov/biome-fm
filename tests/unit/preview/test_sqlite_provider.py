"""Unit tests for SqlitePreviewProvider — Qt-free."""
import sqlite3
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.sqlite_preview import SqlitePreviewProvider


@pytest.fixture
def provider():
    return SqlitePreviewProvider()


def test_can_handle_db(provider):
    assert provider.can_handle(Path("data.db"))
    assert provider.can_handle(Path("data.sqlite"))
    assert provider.can_handle(Path("data.sqlite3"))
    assert not provider.can_handle(Path("data.txt"))


def test_render_tables(provider, tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice')")
    conn.commit()
    conn.close()

    result = provider.render(PreviewRequest(path=db_path))
    assert result.kind == ContentKind.HTML
    assert "users" in result.data


def test_corrupted_db_error(provider, tmp_path):
    db_path = tmp_path / "corrupt.db"
    db_path.write_bytes(b"not a db file at all")
    result = provider.render(PreviewRequest(path=db_path))
    assert result.kind == ContentKind.ERROR
