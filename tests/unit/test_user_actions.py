"""TDD: UserAction + UserActionsStore."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.user_actions import UserAction, UserActionsStore


def test_actions_for_extension(tmp_path: Path) -> None:
    store = UserActionsStore(tmp_path / "actions.json")
    store.add(UserAction(label="Edit", command="vim {f}", extensions=[".py", ".txt"]))
    store.add(UserAction(label="Open", command="open {f}", extensions=[]))

    py_actions = store.actions_for(".py")
    assert any(a.label == "Edit" for a in py_actions)
    # "Open" has no extension filter → shows for everything
    assert any(a.label == "Open" for a in py_actions)

    md_actions = store.actions_for(".md")
    assert not any(a.label == "Edit" for a in md_actions)
    assert any(a.label == "Open" for a in md_actions)


def test_persist_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "actions.json"
    store = UserActionsStore(p)
    store.add(UserAction(label="Run", command="python {f}", extensions=[".py"]))
    store.save()

    store2 = UserActionsStore(p)
    store2.load()
    assert store2.actions_for(".py")[0].label == "Run"


# ── F337: project-scoped user actions ────────────────────────────────────────

import json

def test_load_project_actions(tmp_path: Path) -> None:
    proj = tmp_path / ".biome-fm"
    proj.mkdir()
    (proj / "actions.json").write_text(
        json.dumps([{"label": "Build", "command": "make", "extensions": []}])
    )
    actions = UserActionsStore.load_project(tmp_path)
    assert len(actions) == 1
    assert actions[0].label == "Build"


def test_load_project_actions_no_file_returns_empty(tmp_path: Path) -> None:
    assert UserActionsStore.load_project(tmp_path) == []
