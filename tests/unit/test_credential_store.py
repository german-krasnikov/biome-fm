"""F300 — Cloud Credential Keychain tests."""
from __future__ import annotations

import sys

import pytest


# Force fallback by removing keyring from sys.modules if present
@pytest.fixture(autouse=True)
def _no_keyring(monkeypatch):
    """Ensure tests always run against the in-process fallback, not a real keyring."""
    monkeypatch.setitem(sys.modules, "keyring", None)  # type: ignore[arg-type]
    # Clear the fallback dict before each test
    from biome_fm.models import credential_store
    monkeypatch.setattr(credential_store, "_keyring", None)
    credential_store._FALLBACK.clear()
    yield
    credential_store._FALLBACK.clear()


def test_roundtrip_fallback():
    from biome_fm.models.credential_store import get_credential, set_credential
    set_credential("biome-fm/s3", "user@host", "secret123")
    assert get_credential("biome-fm/s3", "user@host") == "secret123"


def test_missing_returns_none():
    from biome_fm.models.credential_store import get_credential
    assert get_credential("biome-fm/s3", "nobody@nowhere") is None


def test_delete_removes_key():
    from biome_fm.models.credential_store import delete_credential, get_credential, set_credential
    set_credential("biome-fm/ftp", "user@host", "pass")
    delete_credential("biome-fm/ftp", "user@host")
    assert get_credential("biome-fm/ftp", "user@host") is None


def test_delete_missing_is_noop():
    from biome_fm.models.credential_store import delete_credential
    delete_credential("biome-fm/s3", "noone@nowhere")  # must not raise


def test_set_credential_no_keyring_returns_false():
    from biome_fm.models.credential_store import set_credential
    # _no_keyring fixture already sets _keyring=None
    result = set_credential("biome-fm/s3", "user@host", "secret")
    assert result is False


def test_set_credential_with_keyring_returns_true():
    from unittest.mock import MagicMock
    from unittest.mock import patch
    from biome_fm.models import credential_store
    mock_kr = MagicMock()
    mock_kr.set_password.return_value = None  # does not raise
    with patch.object(credential_store, "_keyring", mock_kr):
        result = credential_store.set_credential("biome-fm/s3", "user@host", "secret")
    assert result is True
    mock_kr.set_password.assert_called_once_with("biome-fm/s3", "user@host", "secret")
