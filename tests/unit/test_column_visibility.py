from biome_fm.presenters.column_state import ColumnState


def test_default_all_visible():
    s = ColumnState()
    assert s.visible_columns() == list(ColumnState.COLUMNS)


def test_hide_column():
    s = ColumnState()
    s.set_visible("Size", False)
    assert "Size" not in s.visible_columns()


def test_show_column():
    s = ColumnState()
    s.set_visible("Size", False)
    s.set_visible("Size", True)
    assert "Size" in s.visible_columns()


def test_name_always_visible():
    s = ColumnState()
    s.set_visible("Name", False)
    assert s.is_visible("Name")
    assert "Name" in s.visible_columns()


def test_toggle_column():
    s = ColumnState()
    s.toggle("Size")
    assert not s.is_visible("Size")
    s.toggle("Size")
    assert s.is_visible("Size")
