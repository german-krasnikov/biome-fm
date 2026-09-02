"""Unit tests for glass.py when pyqt_liquidglass is absent (no importorskip guard)."""
from __future__ import annotations

import logging
from unittest.mock import MagicMock

import biome_fm.views.glass as glass


def test_is_available_false_when_lib_missing(monkeypatch):
    monkeypatch.setattr(glass, "_HAS_LIB", False)
    assert glass.is_available() is False

    monkeypatch.setattr(glass, "_HAS_LIB", True)
    assert glass.is_available() is True


def test_prepare_glass_missing_lib_warns_once(monkeypatch, caplog):
    monkeypatch.setattr(glass, "_HAS_LIB", False)
    monkeypatch.setattr(glass, "_warned", False)

    with caplog.at_level(logging.WARNING, logger="biome_fm.views.glass"):
        r1 = glass.prepare_glass(MagicMock())
        r2 = glass.prepare_glass(MagicMock())

    assert r1 is False
    assert r2 is False
    records = [r for r in caplog.records if "pyqt_liquidglass" in r.message]
    assert len(records) == 1
