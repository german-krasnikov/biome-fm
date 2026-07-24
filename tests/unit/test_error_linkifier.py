"""Tests for _error_linkifier.linkify — pure Python, zero Qt."""
from biome_fm.views._error_linkifier import linkify


def test_linkify_python_traceback():
    html = linkify('  File "src/foo.py", line 42, in bar')
    assert 'href="biome-file:///src/foo.py?line=42"' in html


def test_linkify_grep():
    html = linkify('/home/user/proj/main.py:10: import os')
    assert 'biome-file:///home/user/proj/main.py?line=10' in html


def test_linkify_compiler():
    html = linkify('/src/main.c:25:3: error: expected ;')
    assert 'biome-file:///src/main.c?line=25' in html
    assert 'col' not in html


def test_linkify_plain():
    html = linkify('hello world')
    assert '<a' not in html


def test_linkify_xss():
    html = linkify('<script>alert(1)</script>')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


def test_linkify_relative_with_cwd():
    html = linkify('  File "models/vfs.py", line 5, in foo', cwd='/proj')
    assert 'biome-file:///proj/models/vfs.py?line=5' in html


def test_linkify_ampersand_in_path_href_escaped():
    html = linkify('/work/AT&T/main.py:10: error')
    assert 'href="biome-file:///work/AT&amp;T/main.py?line=10"' in html
