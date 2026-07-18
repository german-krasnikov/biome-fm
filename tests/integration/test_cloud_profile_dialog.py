"""F301 — Cloud Profile Dialog integration test."""
from __future__ import annotations

import pytest

from biome_fm.models.cloud_profile_store import CloudProfile, CloudProfileStore
from biome_fm.views.cloud_profile_dialog import CloudProfileDialog


@pytest.fixture
def store(tmp_path):
    s = CloudProfileStore(tmp_path / "profiles.toml")
    s.add(CloudProfile(name="my-s3", scheme="s3", host="s3.amazonaws.com", bucket="data"))
    s.add(CloudProfile(name="ftp-srv", scheme="ftp", host="ftp.example.com"))
    return s


def test_dialog_renders_without_crash(qtbot, store):
    dlg = CloudProfileDialog(store)
    qtbot.addWidget(dlg)
    dlg.show()
    assert dlg.isVisible()


def test_dialog_shows_profiles(qtbot, store):
    dlg = CloudProfileDialog(store)
    qtbot.addWidget(dlg)
    names = [dlg._list.item(i).text() for i in range(dlg._list.count())]
    assert "my-s3" in names
    assert "ftp-srv" in names


def test_dialog_scheme_combo_has_options(qtbot, store):
    dlg = CloudProfileDialog(store)
    qtbot.addWidget(dlg)
    schemes = [dlg._scheme_combo.itemText(i) for i in range(dlg._scheme_combo.count())]
    assert "s3" in schemes
    assert "sftp" in schemes
    assert "ftp" in schemes
