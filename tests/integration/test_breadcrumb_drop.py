"""#19 — Breadcrumb Drop Target: _SegmentButton accepts drops."""
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.qt import QMimeData, Qt
from biome_fm.views.breadcrumb_bar import _SegmentButton
from biome_fm.views.dnd_utils import _MIME


def test_segment_accepts_drops(qtbot):
    btn = _SegmentButton("home", Path("/home"), active=False)
    qtbot.addWidget(btn)

    assert btn.acceptDrops()


def test_segment_drop_emits_signal(qtbot):
    btn = _SegmentButton("home", Path("/home"), active=False)
    qtbot.addWidget(btn)

    mime = QMimeData()
    mime.setData(_MIME, b"/tmp/foo.txt\n/tmp/bar.txt")

    received = []
    btn.files_dropped.connect(lambda paths, move, dest: received.append((paths, move, dest)))

    # Inject drop directly
    class FakeDrop:
        def mimeData(self): return mime
        def modifiers(self): return Qt.KeyboardModifier.NoModifier
        def acceptProposedAction(self): pass

    btn.dropEvent(FakeDrop())

    assert len(received) == 1
    paths, move, dest = received[0]
    assert Path("/tmp/foo.txt") in paths
    assert dest == Path("/home")
    assert move is False
