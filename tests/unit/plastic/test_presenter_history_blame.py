"""Unit tests for PlasticPresenter.file_history + blame_file — no Qt."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.plastic._models import BlameLine, PlasticItem, Revision
from biome_fm.plastic._presenter import PlasticPresenter

_DT = datetime(2026, 7, 24, 10, 0, 0)


def _make_presenter(tmp_path: Path) -> tuple[PlasticPresenter, MagicMock]:
    view = MagicMock()
    p = PlasticPresenter(view, tmp_path)
    return p, view


def test_file_history_queues_result(tmp_path):
    p, view = _make_presenter(tmp_path)
    item = PlasticItem("CO", tmp_path / "foo.py")
    revs = [Revision(rev_id=1, cs_id=42, date=_DT, owner="alice", comment="x", branch="/main")]
    with patch("biome_fm.plastic._presenter.get_file_history", return_value=revs):
        p.file_history(item)
        p.drain()
    view.show_history.assert_called_once_with(item.path, revs)


def test_blame_file_queues_result(tmp_path):
    p, view = _make_presenter(tmp_path)
    item = PlasticItem("CO", tmp_path / "foo.py")
    blame = [BlameLine(line_no=1, owner="bob", cs_id=9, date=_DT, content="pass")]
    with patch("biome_fm.plastic._presenter.get_blame", return_value=blame):
        p.blame_file(item)
        p.drain()
    view.show_blame.assert_called_once_with(item.path, blame)
