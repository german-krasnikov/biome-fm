"""Tests for ManagerPresenter.toggle_hidden."""
from unittest.mock import MagicMock

from biome_fm.config import Config
from biome_fm.event_bus import EventBus, ShowHiddenToggled
from biome_fm.presenters.manager_presenter import ManagerPresenter


def _make_manager(show_hidden=False):
    bus = EventBus()
    cfg = Config(show_hidden=show_hidden)
    left, right = MagicMock(), MagicMock()
    left.current_path = right.current_path = MagicMock()
    m = ManagerPresenter(left, right, MagicMock(), bus=bus, config=cfg)
    return m, bus, cfg


def test_toggle_hidden_publishes_event():
    m, bus, cfg = _make_manager(show_hidden=False)
    received = []
    bus.subscribe(ShowHiddenToggled, received.append)
    m.toggle_hidden()
    assert len(received) == 1
    assert received[0].enabled is True
    assert cfg.show_hidden is True


def test_toggle_hidden_twice():
    m, bus, cfg = _make_manager(show_hidden=False)
    received = []
    bus.subscribe(ShowHiddenToggled, received.append)
    m.toggle_hidden()
    m.toggle_hidden()
    assert received[-1].enabled is False
    assert cfg.show_hidden is False


def test_toggle_hidden_no_config():
    """toggle_hidden without config should not crash."""
    bus = EventBus()
    received = []
    bus.subscribe(ShowHiddenToggled, received.append)
    left, right = MagicMock(), MagicMock()
    left.current_path = right.current_path = MagicMock()
    m = ManagerPresenter(left, right, MagicMock(), bus=bus)
    m.toggle_hidden()
    # No config → event still published (defaults to True)
    assert len(received) == 1
