"""Integration tests for GitCommitDialog."""
import pytest
from pathlib import Path
from pytestqt.qtbot import QtBot

import biome_fm.views.git_commit_dialog as dialog_mod
from biome_fm.views.git_commit_dialog import GitCommitDialog


@pytest.fixture
def repo(tmp_path):
    return tmp_path


def test_dialog_shows_staged_count(qtbot, repo, monkeypatch):
    monkeypatch.setattr(dialog_mod, "staged_files", lambda _: ["a.py", "b.py"])
    dlg = GitCommitDialog(repo)
    qtbot.addWidget(dlg)
    labels = [w for w in dlg.findChildren(dlg.__class__.__mro__[-2]) if hasattr(w, "text")]
    # find QLabel with staged count text
    from PySide6.QtWidgets import QLabel
    label = next(w for w in dlg.findChildren(QLabel) if "file(s)" in w.text())
    assert "2 file(s)" in label.text()


def test_ai_suggest_populates_message(qtbot, repo, monkeypatch):
    monkeypatch.setattr(dialog_mod, "staged_files", lambda _: ["a.py"])
    monkeypatch.setattr(dialog_mod, "staged_diff", lambda _: "some diff")

    def sync_ai(prompt: str) -> str:
        return "feat: suggested message"

    dlg = GitCommitDialog(repo, ai_call=sync_ai)
    qtbot.addWidget(dlg)
    dlg.show()

    from PySide6.QtWidgets import QPushButton
    btn = next(w for w in dlg.findChildren(QPushButton) if w.text() == "AI Suggest")
    with qtbot.waitSignal(dlg._msg.textChanged, timeout=2000):
        btn.click()

    assert "suggested message" in dlg._msg.toPlainText()


def test_empty_message_no_commit(qtbot, repo, monkeypatch):
    monkeypatch.setattr(dialog_mod, "staged_files", lambda _: [])
    committed = []
    monkeypatch.setattr(dialog_mod, "commit", lambda r, m: committed.append(m))

    dlg = GitCommitDialog(repo)
    qtbot.addWidget(dlg)
    dlg._do_commit()

    assert not committed
    assert not dlg.result()  # dialog not accepted
