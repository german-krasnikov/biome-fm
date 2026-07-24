"""Unit tests for demand-driven drain timer callbacks (_on_idle).

No Qt needed — all presenters are pure Python at this layer.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


from biome_fm.presenters.ai_presenter import AIPresenter, _AIEvent
from biome_fm.presenters.search_coordinator import SearchCoordinator
from biome_fm.preview.presenter import PreviewPresenter


# ── helpers ────────────────────────────────────────────────────────────────

def _fake_view(**extras):
    v = MagicMock()
    for k, val in extras.items():
        setattr(v, k, val)
    return v


def _ai_presenter() -> AIPresenter:
    provider = MagicMock()
    provider.available = False
    p = AIPresenter(view=_fake_view(), providers={"mock": provider})
    return p


def _search_coordinator() -> SearchCoordinator:
    return SearchCoordinator(
        vfs=MagicMock(),
        coord=MagicMock(),
        manager=MagicMock(),
        panel=MagicMock(),
        get_active=MagicMock(),
    )


def _preview_presenter() -> PreviewPresenter:
    view = MagicMock()
    view.is_panel_visible.return_value = True
    registry = MagicMock()
    return PreviewPresenter(view=view, registry=registry)


# ── AIPresenter ──────────────────────────────────────────────────────────

def test_ai_presenter_has_on_idle_attr():
    p = _ai_presenter()
    assert p._on_idle is None


def test_ai_presenter_calls_on_idle_when_done():
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = True
    p._events.put(_AIEvent("done", epoch=p._epoch))
    p.drain()
    assert calls == [1]


def test_ai_presenter_no_idle_on_token():
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = True
    p._events.put(_AIEvent("token", "hello", epoch=p._epoch))
    p.drain()
    assert calls == []
    assert p._draining is True  # still draining


def test_ai_presenter_calls_on_idle_on_error():
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = True
    p._events.put(_AIEvent("error", "boom", epoch=p._epoch))
    p.drain()
    assert calls == [1]


def test_ai_presenter_calls_on_idle_on_cancelled():
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = True
    p._events.put(_AIEvent("cancelled", epoch=p._epoch))
    p.drain()
    assert calls == [1]


def test_ai_presenter_calls_on_idle_on_attachment_ready():
    from biome_fm.presenters.ai_presenter import Attachment
    from pathlib import Path
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = True
    att = Attachment(path=Path("x.txt"), kind="text", content="hi")
    p._events.put(_AIEvent("attachment_ready", attachment=att, epoch=p._epoch))
    p.drain()
    assert calls == [1]


def test_ai_presenter_no_idle_when_not_draining():
    """drain() returns early when _draining is False — _on_idle not called."""
    p = _ai_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p._draining = False
    p.drain()
    assert calls == []


# ── SearchCoordinator ────────────────────────────────────────────────────

def test_search_coordinator_has_on_idle_attr():
    sc = _search_coordinator()
    assert sc._on_idle is None


def test_search_coordinator_calls_on_idle_when_done():
    sc = _search_coordinator()
    calls: list[int] = []
    sc._on_idle = lambda: calls.append(1)
    sc._queue.put(None)  # done sentinel
    sc.drain()
    assert calls == [1]


def test_search_coordinator_calls_on_idle_on_cancelled():
    sc = _search_coordinator()
    calls: list[int] = []
    sc._on_idle = lambda: calls.append(1)
    sc._queue.put(sc._CANCELLED)
    sc.drain()
    assert calls == [1]


def test_search_coordinator_no_idle_on_partial():
    sc = _search_coordinator()
    calls: list[int] = []
    sc._on_idle = lambda: calls.append(1)
    fake_result = MagicMock()
    sc._queue.put(fake_result)
    sc.drain()
    assert calls == []


def test_search_coordinator_no_idle_when_queue_empty():
    sc = _search_coordinator()
    calls: list[int] = []
    sc._on_idle = lambda: calls.append(1)
    sc.drain()  # nothing in queue
    assert calls == []


# ── PreviewPresenter ─────────────────────────────────────────────────────

def test_preview_presenter_has_on_idle_attr():
    p = _preview_presenter()
    assert p._on_idle is None


def test_preview_presenter_calls_on_idle_when_queue_empty():
    from biome_fm.preview.provider import ContentKind, PreviewResult
    p = _preview_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    # put one result, then queue empty → _on_idle fires after draining
    result = PreviewResult(kind=ContentKind.TEXT, data="hello")
    p._queue.put(result)
    p.drain()
    assert calls == [1]


def test_preview_presenter_calls_on_idle_on_empty_drain():
    """_on_idle fires even when queue is already empty (timer fires after stop)."""
    p = _preview_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    p.drain()  # empty queue
    assert calls == [1]


def test_preview_presenter_no_idle_while_in_flight():
    """_on_idle must NOT fire when background task is still running (_in_flight > 0)."""
    p = _preview_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    # simulate in-flight task: timer fires before pool thread finishes
    with p._cache_lock:
        p._in_flight = 1
    p.drain()  # queue empty, but in_flight=1 → must not stop timer
    assert calls == [], "timer must not stop while background task is in-flight"


def test_preview_presenter_idle_fires_after_in_flight_clears():
    """_on_idle fires once in_flight drops to 0 and queue is empty."""
    p = _preview_presenter()
    calls: list[int] = []
    p._on_idle = lambda: calls.append(1)
    with p._cache_lock:
        p._in_flight = 1
    p.drain()  # in_flight=1 → no idle
    assert calls == []
    with p._cache_lock:
        p._in_flight = 0
    p.drain()  # in_flight=0, queue empty → idle fires
    assert calls == [1]


# ── Search cancel path ────────────────────────────────────────────────────

def test_search_coordinator_calls_on_idle_when_dialog_cancelled():
    """_on_idle must fire when request_search() returns early (user cancels dialog)."""
    sc = _search_coordinator()
    calls: list[int] = []
    sc._on_idle = lambda: calls.append(1)
    with patch("biome_fm.views.search_dialog.SearchDialog.get_params", return_value=None):
        sc.request_search()
    assert calls == [1], "_on_idle must stop the timer on dialog cancel"


# ── op_timer stop logic (pure-Python simulation) ──────────────────────────

def test_op_timer_stop_condition():
    """Simulate _drain_op_events stop logic without Qt."""
    timer_active = [True]

    class FakeOpQueue:
        def drain(self):
            return []

        def active_count(self):
            return 0

    q = FakeOpQueue()

    def drain():
        events = q.drain()
        if not events and q.active_count() == 0:
            timer_active[0] = False

    drain()
    assert timer_active[0] is False


def test_op_timer_stays_active_when_tasks_running():
    timer_active = [True]

    class FakeOpQueue:
        def drain(self):
            return []

        def active_count(self):
            return 1  # task still running

    q = FakeOpQueue()

    def drain():
        events = q.drain()
        if not events and q.active_count() == 0:
            timer_active[0] = False

    drain()
    assert timer_active[0] is True
