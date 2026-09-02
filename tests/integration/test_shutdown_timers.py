"""Integration tests for shutdown timer correctness (C05).

Verifies nav_timer is stopped in _on_close() and registered in _AppContext.timers
so stale _drain_navs() deliveries to destroyed presenter views cannot occur.
"""
from pathlib import Path

_APP_PY = Path(__file__).parents[2] / "src" / "biome_fm" / "app.py"


def _app_src() -> str:
    return _APP_PY.read_text(encoding="utf-8")


def test_nav_timer_stopped_on_close() -> None:
    """nav_timer.stop() must be called inside _on_close() before left_tabs.shutdown.

    Fails today: nav_timer is created at line ~859 with a 50ms interval but never
    stopped in _on_close(), so _drain_navs() keeps firing into destroyed presenters.
    Also fails: nav_timer is absent from the timers=[] list passed to _AppContext.
    """
    src = _app_src()

    # 1. nav_timer.stop must be called inside _on_close
    assert "nav_timer.stop" in src, (
        "nav_timer.stop() not called anywhere in app.py — "
        "_drain_navs() will fire into destroyed presenters after close"
    )

    # 2. nav_timer must appear before left_tabs.shutdown in the shutdown sequence
    stop_pos = src.index("nav_timer.stop")
    tabs_pos = src.index("left_tabs.shutdown")
    assert stop_pos < tabs_pos, (
        "nav_timer.stop() must come before left_tabs.shutdown in _on_close() "
        "to prevent delivery to an already-destroyed presenter"
    )

    # 3. nav_timer must be included in the timers list passed to _AppContext
    timers_line_start = src.index("timers=[")
    timers_line_end = src.index("]", timers_line_start)
    timers_segment = src[timers_line_start:timers_line_end]
    assert "nav_timer" in timers_segment, (
        "nav_timer not found in timers=[] passed to _AppContext — "
        "it will not be tracked for test inspection"
    )
