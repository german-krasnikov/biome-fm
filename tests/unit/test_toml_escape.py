"""Tests for DRY TOML escape consolidation (Item #17)."""


def test_toml_escape_canonical():
    from biome_fm.models._store_base import toml_escape
    assert toml_escape("\\") == "\\\\"
    assert toml_escape('"') == '\\"'
    assert toml_escape("\n") == "\\n"
    assert toml_escape("\r") == "\\r"
    assert toml_escape("\t") == "\\t"
    assert toml_escape('a\\"b\nc\rd\te') == 'a\\\\\\"b\\nc\\rd\\te'


def test_toml_val_string_with_newline():
    """config._toml_val must escape newlines (latent bug fix)."""
    from biome_fm.config import _toml_val
    assert _toml_val("line1\nline2") == '"line1\\nline2"'


def test_toml_val_string_with_tab():
    from biome_fm.config import _toml_val
    assert _toml_val("key\tval") == '"key\\tval"'


def test_toml_value_string_newline():
    """merger._toml_value must escape newlines (latent bug fix)."""
    from biome_fm.cli.merger import _toml_value
    assert _toml_value("a\nb") == '"a\\nb"'


def test_toml_value_list_with_special_chars():
    from biome_fm.cli.merger import _toml_value
    assert _toml_value(["a\tb", 'c"d']) == '["a\\tb", "c\\"d"]'


def test_bookmark_save_reload_special_path(tmp_path):
    """Bookmark round-trip: path with quote survives TOML save/load."""
    from biome_fm.models.bookmark_store import BookmarkStore
    # POSIX allows quotes in filenames; this is the minimal special-char test
    special = tmp_path / 'dir"quoted"name'
    store = BookmarkStore(tmp_path / "bm.toml")
    store.add(path=special)
    store2 = BookmarkStore(tmp_path / "bm.toml")
    assert special in store2.all()
