from biome_fm.views.pane_view import _match_positions


def test_subsequence_match():
    # p=0, y=11 (pane_view.py is 12 chars: p-a-n-e-_-v-i-e-w-.-p-y)
    assert _match_positions("py", "pane_view.py") == [0, 11]


def test_no_match():
    assert _match_positions("xyz", "abc") == []


def test_empty_pattern():
    assert _match_positions("", "foo") == []


def test_single_char():
    assert _match_positions("a", "bba") == [2]


def test_case_insensitive():
    assert _match_positions("PY", "pane_view.py") == [0, 11]
