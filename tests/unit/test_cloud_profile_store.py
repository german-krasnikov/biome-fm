"""F301 — Cloud Storage Profile Manager store tests."""
from __future__ import annotations

import pytest

from biome_fm.models.cloud_profile_store import CloudProfile, CloudProfileStore


@pytest.fixture
def store(tmp_path):
    s = CloudProfileStore(tmp_path / "cloud_profiles.toml")
    return s


class TestCRUD:
    def test_add_and_get(self, store):
        p = CloudProfile(name="my-s3", scheme="s3", host="s3.amazonaws.com", bucket="mybucket")
        store.add(p)
        assert store.get("my-s3") == p

    def test_get_missing_returns_none(self, store):
        assert store.get("nonexistent") is None

    def test_delete(self, store):
        store.add(CloudProfile(name="ftp-srv", scheme="ftp", host="ftp.example.com"))
        store.delete("ftp-srv")
        assert store.get("ftp-srv") is None

    def test_delete_missing_is_noop(self, store):
        store.delete("no-such-profile")  # must not raise

    def test_list_all_empty(self, store):
        assert store.list_all() == []

    def test_list_all_returns_all(self, store):
        store.add(CloudProfile(name="a", scheme="s3", host="h"))
        store.add(CloudProfile(name="b", scheme="ftp", host="h2"))
        names = {p.name for p in store.list_all()}
        assert names == {"a", "b"}


class TestTOMLRoundTrip:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "profiles.toml"
        s1 = CloudProfileStore(path)
        s1.add(CloudProfile(
            name="webdav-office",
            scheme="webdav",
            host="dav.office.com",
            port=443,
            user="alice",
            bucket="",
            extra={"ssl": "true"},
        ))
        s1.save()

        s2 = CloudProfileStore(path)
        s2.load()
        p = s2.get("webdav-office")
        assert p is not None
        assert p.scheme == "webdav"
        assert p.host == "dav.office.com"
        assert p.port == 443
        assert p.user == "alice"
        assert p.extra == {"ssl": "true"}

    def test_load_nonexistent_file_is_noop(self, tmp_path):
        s = CloudProfileStore(tmp_path / "missing.toml")
        s.load()  # must not raise
        assert s.list_all() == []

    def test_save_creates_parent_dir(self, tmp_path):
        path = tmp_path / "subdir" / "profiles.toml"
        s = CloudProfileStore(path)
        s.add(CloudProfile(name="x", scheme="s3", host="h"))
        s.save()
        assert path.exists()
