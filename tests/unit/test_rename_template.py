"""Tests for expand_template — TC-style multi-rename tokens."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.presenters.rename_template import expand_template


def _mock_path(name: str, mtime: float = 1_700_000_000.0) -> Path:
    p = MagicMock(spec=Path)
    p.name = name
    p.stem = Path(name).stem
    p.suffix = Path(name).suffix
    stat = MagicMock()
    stat.st_mtime = mtime
    p.stat.return_value = stat
    return p


def test_n_token():
    p = _mock_path("photo.jpg")
    assert expand_template("[N]", p, 0) == "photo"


def test_e_token():
    p = _mock_path("photo.jpg")
    assert expand_template("[E]", p, 0) == "jpg"


def test_c_token():
    p = _mock_path("photo.jpg")
    assert expand_template("[C]", p, 0) == "001"
    assert expand_template("[C]", p, 4) == "005"


def test_c_start_offset():
    p = _mock_path("photo.jpg")
    assert expand_template("[C:5]", p, 0) == "005"
    assert expand_template("[C:5]", p, 2) == "007"


def test_ymd_token():
    from datetime import datetime
    p = _mock_path("photo.jpg", mtime=datetime(2024, 3, 15).timestamp())
    assert expand_template("[YMD]", p, 0) == "2024-03-15"


def test_combined():
    p = _mock_path("photo.jpg")
    assert expand_template("[N]_[C].[E]", p, 0) == "photo_001.jpg"


def test_literal_text_preserved():
    p = _mock_path("photo.jpg")
    assert expand_template("prefix_[N]", p, 0) == "prefix_photo"
