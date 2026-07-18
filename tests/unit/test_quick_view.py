from biome_fm.presenters.quick_view_state import QuickViewState


def test_initial_state_inactive():
    assert QuickViewState().active is False


def test_toggle_enters_quick_view():
    s = QuickViewState()
    s.toggle((300, 300))
    assert s.active is True


def test_toggle_exits_quick_view():
    s = QuickViewState()
    s.toggle((300, 300))
    s.toggle((600, 0))
    assert s.active is False


def test_saved_sizes_restored():
    s = QuickViewState()
    s.toggle((300, 300))
    restored = s.toggle((600, 0))
    assert restored == (300, 300)
