"""Image preview provider — reads raw bytes in background."""
from __future__ import annotations

import base64
import struct
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico", ".svg"}
_MAX_BYTES = 50 * 1024 * 1024  # 50MB

# Common EXIF tag IDs → display names
_EXIF_TAGS = {
    0x010F: "Make", 0x0110: "Model", 0x0132: "DateTime",
    0x013B: "Artist", 0x8769: None,  # ExifIFD pointer — skip
    0x8825: None,  # GPS pointer — skip
}


def _read_exif(path: Path) -> dict | None:
    """Return display-ready EXIF key-value pairs, or None. Never touches Qt."""
    if path.suffix.lower() not in {".jpg", ".jpeg"}:
        return None
    try:
        # Try piexif first (optional dep)
        import piexif  # type: ignore[import]
        data = piexif.load(str(path))
        result: dict[str, str] = {}
        for ifd_name in ("0th", "Exif", "GPS"):
            ifd = data.get(ifd_name, {})
            for tag, val in ifd.items():
                name = piexif.TAGS.get(ifd_name, {}).get(tag, {}).get("name")
                if name and isinstance(val, (str, bytes, int, float)):
                    display = val.decode(errors="replace") if isinstance(val, bytes) else str(val)
                    result[name] = display[:120]
        return result or None
    except Exception:
        pass

    # Fallback: minimal struct-based JPEG APP1 reader
    try:
        raw = path.read_bytes()
        if raw[:2] != b"\xff\xd8":
            return None
        i = 2
        while i < len(raw) - 4:
            marker = raw[i:i+2]
            seg_len = struct.unpack(">H", raw[i+2:i+4])[0]
            if marker == b"\xff\xe1":  # APP1
                app1 = raw[i+4:i+2+seg_len]
                if app1[:6] == b"Exif\x00\x00":
                    return _parse_ifd(app1[6:])
            i += 2 + seg_len
    except Exception:
        pass
    return None


def _parse_ifd(tiff: bytes) -> dict | None:
    """Parse minimal TIFF IFD for common tags. Returns None if unreadable."""
    try:
        endian = "<" if tiff[:2] == b"II" else ">"
        offset = struct.unpack(endian + "I", tiff[4:8])[0]
        count = struct.unpack(endian + "H", tiff[offset:offset+2])[0]
        result: dict[str, str] = {}
        for k in range(count):
            base = offset + 2 + k * 12
            tag, typ, cnt = struct.unpack(endian + "HHI", tiff[base:base+8])
            label = _EXIF_TAGS.get(tag)
            if label is None:
                continue
            val_off = struct.unpack(endian + "I", tiff[base+8:base+12])[0]
            if typ == 2:  # ASCII
                end = tiff.index(b"\x00", val_off) if b"\x00" in tiff[val_off:] else val_off + cnt
                result[label] = tiff[val_off:end].decode(errors="replace")
        return result or None
    except Exception:
        return None


def _exif_html(path: Path, raw: bytes, exif: dict) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    b64 = base64.b64encode(raw).decode()
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in exif.items())
    return (
        f'<img src="data:{mime};base64,{b64}" style="max-width:100%;max-height:60vh">'
        f"<table style='margin-top:8px;font-size:12px'>{rows}</table>"
    )


class ImagePreviewProvider:
    priority = 0

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _IMAGE_EXT

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            size = req.path.stat().st_size
            if size > _MAX_BYTES:
                return PreviewResult(
                    kind=ContentKind.ERROR,
                    data=f"Image too large ({size // 1024 // 1024} MB)",
                )
            raw = req.path.read_bytes()
            exif = _read_exif(req.path)
            if exif:
                return PreviewResult(
                    kind=ContentKind.HTML,
                    data=_exif_html(req.path, raw, exif),
                    title=req.path.name,
                )
            return PreviewResult(kind=ContentKind.IMAGE, data=raw, title=req.path.name)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
