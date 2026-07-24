"""TDD: Macro Store — F457."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# MacroStore
# ---------------------------------------------------------------------------

def test_macro_store_roundtrip(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("test", ["a", "b"])
    assert store.load_macro("test") == ["a", "b"]


def test_macro_store_delete(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("test", ["a"])
    store.delete("test")
    assert store.load_macro("test") is None


def test_macro_store_list(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("alpha", ["x"])
    store.save("beta", ["y"])
    names = store.list_macros()
    assert set(names) == {"alpha", "beta"}
