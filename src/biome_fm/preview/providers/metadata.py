"""Audio metadata preview provider (mutagen optional)."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_AUDIO_EXTS = frozenset({
    ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wav",
    ".opus", ".wma", ".aiff", ".ape", ".wv",
})


class MetadataPreviewProvider:
    priority = 7

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _AUDIO_EXTS

    def render(self, req: PreviewRequest) -> PreviewResult:
        rows: list[tuple[str, str]] = []
        try:
            import mutagen  # type: ignore[import]
            f = mutagen.File(req.path)
            if f is not None:
                for key in ("title", "artist", "album", "date", "tracknumber", "genre"):
                    val = f.tags.get(key) if f.tags else None
                    if val:
                        rows.append((key.capitalize(),
                                     str(val[0]) if isinstance(val, list) else str(val)))
                info = f.info
                if getattr(info, "length", None):
                    mins, secs = divmod(int(info.length), 60)
                    rows.append(("Duration", f"{mins}:{secs:02d}"))
                if getattr(info, "bitrate", None):
                    rows.append(("Bitrate", f"{info.bitrate // 1000} kbps"))
                if getattr(info, "sample_rate", None):
                    rows.append(("Sample Rate", f"{info.sample_rate} Hz"))
        except ImportError:
            pass
        except Exception:
            pass

        if not rows:
            try:
                st = os.stat(req.path)
                rows.append(("Size", f"{st.st_size:,} bytes"))
                rows.append(("Type", req.path.suffix.upper().lstrip(".")))
            except OSError:
                rows.append(("Error", "Cannot read file"))

        table_rows = "".join(
            f"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;'>{k}</td>"
            f"<td style='padding:4px 0;'>{v}</td></tr>"
            for k, v in rows
        )
        return PreviewResult(kind=ContentKind.HTML,
                             data=f"<table style='font-size:13px;'>{table_rows}</table>")
