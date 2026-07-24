"""Integration tests for session auto-save timer (Item #28)."""


def test_app_context_has_session_timer_field():
    """_AppContext dataclass exposes session_timer for testability."""
    from biome_fm.app import _AppContext
    import dataclasses
    fields = {f.name for f in dataclasses.fields(_AppContext)}
    assert "session_timer" in fields


def test_session_timer_wired_in_create_app():
    """create_app() wires session_timer at 60_000ms against session.json.

    Avoids calling create_app() (it spins up AI workers, fswatch, etc.) but
    verifies the three load-bearing lines directly in the source — enough to
    catch someone changing the interval or removing the stop() call.
    """
    import inspect
    from biome_fm.app import create_app

    src = inspect.getsource(create_app)
    assert "session_timer.setInterval(60_000)" in src, "wrong or missing interval"
    assert 'cfg_dir / "session.json"' in src, "save target wrong or missing"
    assert "session_timer.stop()" in src, "timer not stopped in _on_close"
