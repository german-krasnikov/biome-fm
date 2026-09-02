"""Integration test — verify _new_tab connects all wire helpers via source inspection."""
import inspect


def test_new_tab_wires_ctx():
    """_new_tab() must call _wire_ctx so context_action_requested is connected."""
    from biome_fm.app import create_app
    src = inspect.getsource(create_app)
    assert "_wire_ctx(v)" in src
    assert "_wire_clipboard(v)" in src
    assert "_wire_git(v, watcher)" in src


def test_each_wire_helper_and_handler_connected_once():
    """Each of the 4 path_updated handlers must be connected exactly once in create_app."""
    from biome_fm.app import create_app
    src = inspect.getsource(create_app)
    for handler in (
        "_on_project_navigate",
        "plugins.on_navigate",
        "terminal_panel.set_cwd",
        "_update_git_branch",
    ):
        count = src.count(f".connect({handler})")
        assert count == 1, f".connect({handler}) appears {count}× (expected 1)"
    # Each _wire_* helper called exactly once (inside _wire_all)
    for call_form in ("_wire_ctx(v)", "_wire_clipboard(v)", "_wire_git(v, watcher)"):
        count = src.count(call_form)
        assert count == 1, f"'{call_form}' appears {count}× (expected 1)"


def test_restore_delegates_to_replace_all_and_callback():
    """_restore must call replace_all, contain no _wire_ calls, and on_tab_created must be set."""
    from biome_fm.app import create_app
    src = inspect.getsource(create_app)
    restore_src = src[src.index("def _restore(") : src.index("home = Path.home()")]
    assert "replace_all(" in restore_src, "_restore does not call replace_all"
    assert "_wire_" not in restore_src, "_restore still contains _wire_ calls"
    assert "on_tab_created = " in src, "on_tab_created is never set in create_app"
