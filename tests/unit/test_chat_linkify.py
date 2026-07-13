"""Unit tests for path linkify helpers — pure Python, no Qt."""
from __future__ import annotations

from biome_fm.views._linkify import _PATH_RE, _linkify_html


def test_path_re_absolute():
    m = _PATH_RE.search("/Users/german/Work/file.py")
    assert m is not None
    assert m.group(0) == "/Users/german/Work/file.py"


def test_path_re_home():
    m = _PATH_RE.search("~/Documents/notes.md")
    assert m is not None
    assert m.group(0) == "~/Documents/notes.md"


def test_path_re_relative():
    m = _PATH_RE.search("src/biome_fm/app.py")
    assert m is not None
    assert m.group(0) == "src/biome_fm/app.py"


def test_path_re_no_url():
    # https://example.com/path must NOT yield a match containing the domain or scheme
    matches = _PATH_RE.findall("https://example.com/path")
    assert all("example.com" not in m for m in matches)
    assert all("https" not in m for m in matches)


def test_linkify_skips_code():
    fragment = "<code>/path/to/file</code>"
    result = _linkify_html(fragment)
    assert 'href="biome:' not in result
    assert "/path/to/file" in result


def test_path_re_no_false_positives():
    for word in ("and/or", "I/O", "TCP/IP", "n/a", "read/write"):
        assert _PATH_RE.search(word) is None, f"False positive: {word}"


def test_linkify_plain_text():
    fragment = "see /Users/german/Work/file.py here"
    result = _linkify_html(fragment)
    assert 'href="biome:/Users/german/Work/file.py"' in result
