"""Unit tests for SSHProfileStore — RED phase."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from biome_fm.models.ssh_profiles import SSHProfile, SSHProfileStore


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _store(tmp_path: Path) -> SSHProfileStore:
    store = SSHProfileStore(tmp_path / "profiles.toml")
    store.load()
    return store


def _profile(**kw) -> SSHProfile:
    defaults = dict(name="web", host="example.com", port=22, user="deploy", key_path="")
    defaults.update(kw)
    return SSHProfile(**defaults)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_save_load_profile(tmp_path):
    store = _store(tmp_path)
    p = _profile()
    store.add(p)
    store.save()

    store2 = SSHProfileStore(tmp_path / "profiles.toml")
    store2.load()
    loaded = store2.get("web")
    assert loaded.host == "example.com"
    assert loaded.port == 22
    assert loaded.user == "deploy"
    assert loaded.key_path == ""


def test_persistence_round_trip(tmp_path):
    store = _store(tmp_path)
    store.add(_profile(name="prod", host="prod.example.com", port=2222, key_path="/home/me/.ssh/id_rsa"))
    store.save()

    store2 = SSHProfileStore(tmp_path / "profiles.toml")
    store2.load()
    p = store2.get("prod")
    assert p.port == 2222
    assert p.key_path == "/home/me/.ssh/id_rsa"


def test_unknown_profile_raises(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(KeyError):
        store.get("nope")


def test_delete_profile(tmp_path):
    store = _store(tmp_path)
    store.add(_profile(name="a"))
    store.add(_profile(name="b", host="b.com"))
    store.delete("a")
    assert [p.name for p in store.list_all()] == ["b"]
    with pytest.raises(KeyError):
        store.get("a")


def test_ssh_config_import(tmp_path):
    cfg = tmp_path / "ssh_config"
    cfg.write_text(textwrap.dedent("""\
        Host myserver
            HostName myserver.example.com
            User alice
            Port 2222
            IdentityFile ~/.ssh/id_ed25519

        Host bastion
            HostName bastion.corp
            User bastion-user

        Host *
            ServerAliveInterval 60
    """))

    store = _store(tmp_path)
    store.import_ssh_config(cfg)

    names = [p.name for p in store.list_all()]
    assert "myserver" in names
    assert "bastion" in names
    assert "*" not in names  # wildcard entries skipped

    ms = store.get("myserver")
    assert ms.host == "myserver.example.com"
    assert ms.user == "alice"
    assert ms.port == 2222
    assert "id_ed25519" in ms.key_path

    bas = store.get("bastion")
    assert bas.host == "bastion.corp"
    assert bas.port == 22  # default
