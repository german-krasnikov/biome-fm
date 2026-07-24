"""Parametrized atomic-write tests for 8 model stores (Item #26)."""
import os
from pathlib import Path

import pytest


# ── Store factory helpers — each returns (written_path, callable_that_saves) ──


def _make_cloud(tmp_path: Path):
    from biome_fm.models.cloud_profile_store import CloudProfileStore
    p = tmp_path / "profiles.toml"
    return p, CloudProfileStore(p).save


def _make_ssh(tmp_path: Path):
    from biome_fm.models.ssh_profiles import SSHProfileStore
    p = tmp_path / "ssh.toml"
    return p, SSHProfileStore(p).save


def _make_search(tmp_path: Path):
    from biome_fm.models.search_template_store import SearchTemplate, SearchTemplateStore
    p = tmp_path / "search.toml"
    s = SearchTemplateStore(p)
    return p, lambda: s.save(SearchTemplate(name="t", pattern="*.py", mode="wildcard"))


def _make_tab_group(tmp_path: Path):
    from biome_fm.models.tab_group_store import TabGroupStore
    p = tmp_path / "groups.json"
    s = TabGroupStore(p)
    return p, lambda: s.save_group("grp", [Path("/tmp")])


def _make_associations(tmp_path: Path):
    from biome_fm.models.associations import FileAssociations
    p = tmp_path / "assoc.json"
    s = FileAssociations(p)
    s.set(".py", "vim")
    return p, s.save


def _make_user_actions(tmp_path: Path):
    from biome_fm.models.user_actions import UserAction, UserActionsStore
    p = tmp_path / "actions.json"
    s = UserActionsStore(p)
    s.add(UserAction(label="test", command="echo"))
    return p, s.save


def _make_finder_tags(tmp_path: Path):
    from biome_fm.models.finder_tags import _meta_path, _set_comment_fallback
    src = tmp_path / "target.txt"
    src.write_text("data")
    return _meta_path(src), lambda: _set_comment_fallback(src, "note")


CASES = [
    _make_cloud, _make_ssh, _make_search,
    _make_tab_group, _make_associations, _make_user_actions, _make_finder_tags,
]


@pytest.fixture(params=CASES, ids=lambda f: f.__name__[6:])
def case(request, tmp_path):
    return request.param(tmp_path)


def test_no_tmp_left_after_save(case):
    path, do_save = case
    do_save()
    tmp = path.with_suffix(path.suffix + ".tmp")
    assert not tmp.exists()


def test_target_preserved_on_write_failure(case, monkeypatch):
    path, do_save = case
    do_save()  # write good data first
    original = path.read_text()

    def fail_replace(src, dst):
        raise OSError("simulated crash")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError):
        do_save()

    assert path.read_text() == original
