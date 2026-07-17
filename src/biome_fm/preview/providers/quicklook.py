"""macOS Quick Look fallback preview provider."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult


class QuickLookProvider:
    priority = 990

    def can_handle(self, path: Path) -> bool:
        return sys.platform == "darwin" and path.is_file()

    def render(self, req: PreviewRequest) -> PreviewResult:
        tmp = Path(tempfile.mkdtemp())
        try:
            subprocess.run(
                ["qlmanage", "-t", "-s", "512", "-o", str(tmp), str(req.path)],
                capture_output=True,
                timeout=10,
            )
            pngs = list(tmp.glob("*.png"))
            if pngs:
                return PreviewResult(kind=ContentKind.IMAGE, data=pngs[0].read_bytes())
            return PreviewResult(kind=ContentKind.ERROR, data="qlmanage produced no thumbnail")
        except subprocess.TimeoutExpired:
            return PreviewResult(kind=ContentKind.ERROR, data="Quick Look timed out")
        except (FileNotFoundError, OSError) as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
