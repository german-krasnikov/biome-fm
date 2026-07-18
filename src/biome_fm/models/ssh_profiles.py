"""SSH connection profile store — no passwords ever stored."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SSHProfile:
    name: str
    host: str
    port: int = 22
    user: str = ""
    key_path: str = ""


class SSHProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._profiles: dict[str, SSHProfile] = {}

    def load(self) -> None:
        if not self._path.exists():
            return
        data = tomllib.loads(self._path.read_text())
        for name, vals in data.get("profiles", {}).items():
            self._profiles[name] = SSHProfile(
                name=name,
                host=vals.get("host", ""),
                port=int(vals.get("port", 22)),
                user=vals.get("user", ""),
                key_path=vals.get("key_path", ""),
            )

    def save(self) -> None:
        lines: list[str] = []
        for p in self._profiles.values():
            lines.append(f"[profiles.{p.name}]")
            lines.append(f'host = "{p.host}"')
            lines.append(f"port = {p.port}")
            lines.append(f'user = "{p.user}"')
            lines.append(f'key_path = "{p.key_path}"')
            lines.append("")
        self._path.write_text("\n".join(lines))

    def add(self, profile: SSHProfile) -> None:
        self._profiles[profile.name] = profile

    def get(self, name: str) -> SSHProfile:
        if name not in self._profiles:
            raise KeyError(name)
        return self._profiles[name]

    def delete(self, name: str) -> None:
        if name not in self._profiles:
            raise KeyError(name)
        del self._profiles[name]

    def list_all(self) -> list[SSHProfile]:
        return list(self._profiles.values())

    def import_ssh_config(self, ssh_config_path: Path) -> None:
        """Parse OpenSSH config Host entries; skip wildcards."""
        current: dict[str, str] = {}
        current_host: str | None = None

        def _flush() -> None:
            if current_host and "*" not in current_host:
                self._profiles[current_host] = SSHProfile(
                    name=current_host,
                    host=current.get("hostname", current_host),
                    port=int(current.get("port", 22)),
                    user=current.get("user", ""),
                    key_path=current.get("identityfile", ""),
                )

        for raw in ssh_config_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, _, val = line.partition(" ")
            key = key.lower()
            if key == "host":
                _flush()
                current_host = val.strip()
                current = {}
            elif current_host:
                current[key] = val.strip()

        _flush()
