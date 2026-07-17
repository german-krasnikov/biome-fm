"""Pure unit tests for _fuzzy_match — no Qt needed."""
from biome_fm.models.directory_model import _fuzzy_match


def test_fuzzy_matches_subsequence():
    assert _fuzzy_match("htl", "hotel.txt")


def test_fuzzy_no_jumbled():
    # 't' at index 2, 'h' at index 0 — "thl" can't match because t < h order-wise
    # hotel: h(0) o(1) t(2) e(3) l(4) — pattern "thl": t found at 2, h needed after 2 — not found
    assert not _fuzzy_match("thl", "hotel.txt")


def test_exact_substring_still_works():
    assert _fuzzy_match("hot", "hotel.txt")


def test_empty_pattern_matches_anything():
    assert _fuzzy_match("", "hotel.txt")


def test_case_insensitive():
    assert _fuzzy_match("HTL", "hotel.txt")


def test_no_match():
    assert not _fuzzy_match("xyz", "hotel.txt")
