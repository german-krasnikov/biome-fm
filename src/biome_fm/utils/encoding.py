"""Encoding detection — chardet if available, UTF-8 fallback."""
from __future__ import annotations


def detect_encoding(data: bytes) -> str:
    try:
        import chardet
        if chardet is None:
            raise ImportError
        result = chardet.detect(data)
        return result.get("encoding") or "utf-8"
    except (ImportError, AttributeError):
        return "utf-8"


def decode_smart(data: bytes) -> tuple[str, str]:
    """Return (text, encoding_name). Never raises."""
    enc = detect_encoding(data)
    try:
        return data.decode(enc, errors="replace"), enc
    except (LookupError, UnicodeDecodeError):
        return data.decode("utf-8", errors="replace"), "utf-8"
