"""F301 — Cloud storage connection profiles. TOML-backed."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class CloudProfile:
    name: str
    scheme: str           # "s3", "ftp", "ftps", "webdav", "sftp", "rclone"
    host: str = ""
    port: int | None = None
    user: str = ""
    bucket: str = ""      # S3-style bucket / root path
    extra: dict[str, str] = field(default_factory=dict)


class CloudProfileStore:
    """TOML-backed CRUD store. Path: ~/.config/biome-fm/cloud_profiles.toml."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._profiles: dict[str, CloudProfile] = {}

    # ── Read ──────────────────────────────────────────────────────────────

    def load(self) -> None:
        if not self._path.exists():
            return
        data = tomllib.loads(self._path.read_text())
        for name, v in data.get("profiles", {}).items():
            self._profiles[name] = CloudProfile(
                name=name,
                scheme=v.get("scheme", ""),
                host=v.get("host", ""),
                port=int(v["port"]) if v.get("port") else None,
                user=v.get("user", ""),
                bucket=v.get("bucket", ""),
                extra={k: str(val) for k, val in v.get("extra", {}).items()},
            )

    # ── Write ─────────────────────────────────────────────────────────────

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for p in self._profiles.values():
            lines.append(f"[profiles.{p.name}]")
            lines.append(f'scheme = "{p.scheme}"')
            lines.append(f'host = "{p.host}"')
            if p.port is not None:
                lines.append(f"port = {p.port}")
            lines.append(f'user = "{p.user}"')
            lines.append(f'bucket = "{p.bucket}"')
            if p.extra:
                lines.append("[profiles." + p.name + ".extra]")
                for k, v in p.extra.items():
                    lines.append(f'{k} = "{v}"')
            lines.append("")
        self._path.write_text("\n".join(lines))

    # ── CRUD ──────────────────────────────────────────────────────────────

    def add(self, profile: CloudProfile) -> None:
        if not _NAME_RE.match(profile.name):
            raise ValueError(
                f"Profile name must match [a-zA-Z0-9_-]+, got: {profile.name!r}"
            )
        self._profiles[profile.name] = profile

    def get(self, name: str) -> CloudProfile | None:
        return self._profiles.get(name)

    def delete(self, name: str) -> None:
        self._profiles.pop(name, None)

    def list_all(self) -> list[CloudProfile]:
        return list(self._profiles.values())
