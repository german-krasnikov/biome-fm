"""Unit tests for encoding detection — Qt-free."""
from biome_fm.utils.encoding import decode_smart, detect_encoding


def test_utf8_detected():
    data = "hello world".encode("utf-8")
    enc = detect_encoding(data)
    assert enc.lower().replace("-", "") in ("utf8", "ascii")


def test_no_chardet_fallback(monkeypatch):
    """Without chardet, defaults to utf-8."""
    import sys
    monkeypatch.setitem(sys.modules, "chardet", None)
    text, enc = decode_smart(b"hello world")
    assert text == "hello world"
    assert enc.lower() in ("utf-8", "ascii", "utf8")


def test_ascii_stays_utf8():
    text, enc = decode_smart(b"plain ascii text")
    assert text == "plain ascii text"
