"""Unit tests for ClipboardService history ring (F446)."""
from pathlib import Path

import pytest

from biome_fm.models.clipboard_service import ClipboardEntry, ClipboardService


@pytest.fixture
def svc() -> ClipboardService:
    return ClipboardService()


A = Path("/a")
B = Path("/b")
C = Path("/c")


def test_empty_history(svc: ClipboardService) -> None:
    assert svc.history() == []


def test_copy_adds_to_history(svc: ClipboardService) -> None:
    svc.copy([A, B])
    entry = svc.history()[0]
    assert entry.paths == (A, B)
    assert entry.is_cut is False


def test_cut_adds_to_history(svc: ClipboardService) -> None:
    svc.cut([C])
    assert svc.history()[0].is_cut is True


def test_history_most_recent_first(svc: ClipboardService) -> None:
    svc.copy([A])
    svc.copy([B])
    assert svc.history()[0].paths == (B,)


def test_history_cap(svc: ClipboardService) -> None:
    for i in range(21):
        svc.copy([Path(f"/{i}")])
    assert len(svc.history()) == 20


def test_restore_history(svc: ClipboardService) -> None:
    svc.copy([A])
    svc.cut([B])
    older = svc.history()[1]  # [A], is_cut=False
    svc.restore_history(older)
    paths, is_cut = svc.paste(Path("/dest"))
    assert paths == [A]
    assert is_cut is False
