"""Test OS theme auto-switch config and wiring."""
from __future__ import annotations

from biome_fm.app import _wire_system_theme
from biome_fm.config import Config


class _FakeSig:
    def __init__(self):
        self._cbs = []

    def connect(self, cb):
        self._cbs.append(cb)

    def emit(self):
        for cb in self._cbs:
            cb()


class _FakeHints:
    def __init__(self):
        self.colorSchemeChanged = _FakeSig()


def test_config_has_follow_system_theme():
    cfg = Config()
    assert cfg.follow_system_theme is True


def test_follow_false_blocks_switch():
    cfg = Config(follow_system_theme=False)
    hints = _FakeHints()
    called = []
    _wire_system_theme(cfg, hints, lambda: called.append(1))
    hints.colorSchemeChanged.emit()
    assert called == []


def test_follow_true_connects_switch():
    cfg = Config(follow_system_theme=True)
    hints = _FakeHints()
    called = []
    _wire_system_theme(cfg, hints, lambda: called.append(1))
    hints.colorSchemeChanged.emit()
    assert called == [1]
