from pathlib import Path
import pytest
from biome_fm.presenters.semantic_search import extract_keywords, search_by_keywords


def test_extract_keywords():
    assert extract_keywords("photos from vacation") == ["photos", "vacation"]


def test_empty_query_returns_empty():
    assert extract_keywords("") == []


def test_stopwords_removed():
    assert extract_keywords("the big file") == ["big", "file"]


def test_rank_results():
    paths = [
        Path("/home/user/vacation_photos.jpg"),
        Path("/home/user/document.pdf"),
        Path("/home/user/vacation.zip"),
    ]
    results = search_by_keywords(paths, "photos from vacation")
    # vacation_photos matches both "photos" and "vacation" → score 2, first
    assert results[0][0].name == "vacation_photos.jpg"
    assert results[0][1] == 2
    # vacation.zip matches only "vacation" → score 1
    assert results[1][0].name == "vacation.zip"
    # document.pdf matches nothing → excluded
    assert all(p.name != "document.pdf" for p, _ in results)
