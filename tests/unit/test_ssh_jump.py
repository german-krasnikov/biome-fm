"""TDD: F413 SSH Jump Host / Proxy."""
import tempfile
from pathlib import Path

import pytest

from biome_fm.models.sftp_vfs import SFTPSession, make_jump_proxy_command
from biome_fm.models.ssh_profiles import SSHProfile, SSHProfileStore


def test_make_jump_proxy_command_with_user():
    result = make_jump_proxy_command("bastion.example.com", 22, "ops", "db.internal", 22)
    assert result == "ssh -W db.internal:22 -p 22 ops@bastion.example.com"


def test_make_jump_proxy_command_no_user():
    result = make_jump_proxy_command("bastion.example.com", 22, "", "db.internal", 22)
    assert result == "ssh -W db.internal:22 -p 22 bastion.example.com"


def test_sftp_session_proxy_command_field():
    s = SFTPSession(host="x", proxy_command="ssh -W x:22 bastion")
    assert s.proxy_command == "ssh -W x:22 bastion"
    assert SFTPSession(host="x").proxy_command == ""


def test_ssh_profile_jump_fields():
    p = SSHProfile(name="test", host="x", jump_host="bastion", jump_user="ops")
    assert p.jump_host == "bastion"
    assert p.jump_user == "ops"


def test_ssh_profile_store_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "profiles.toml"
        store = SSHProfileStore(path)
        store.add(SSHProfile(name="prod", host="db.internal", jump_host="bastion.example.com", jump_user="ops"))
        store.save()

        store2 = SSHProfileStore(path)
        store2.load()
        p = store2.get("prod")
        assert p.jump_host == "bastion.example.com"
        assert p.jump_user == "ops"
