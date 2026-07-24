"""Integration test — verify _new_tab connects all wire helpers via source inspection."""
import inspect


def test_new_tab_wires_ctx():
    """_new_tab() must call _wire_ctx so context_action_requested is connected."""
    from biome_fm.app import create_app
    src = inspect.getsource(create_app)
    assert "_wire_ctx(v)" in src
    assert "_wire_clipboard(v)" in src
    assert "_wire_git(v, watcher)" in src
