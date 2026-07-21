"""Folder watch rules — auto-actions on file arrival."""
from __future__ import annotations

import fnmatch
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WatchRule:
    watch_dir: str   # absolute path
    pattern: str     # fnmatch glob, e.g. "*.pdf"
    command: str     # shell command; {file} replaced with matched path


class WatchRuleStore:
    """TOML persistence for watch rules."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (Path.home() / ".config" / "biome-fm" / "watch_rules.toml")
        self._rules: list[WatchRule] = []

    def load(self) -> None:
        if not self._path.exists():
            self._rules = []
            return
        import tomllib
        data = tomllib.loads(self._path.read_text(encoding="utf-8"))
        self._rules = [
            WatchRule(watch_dir=r["watch_dir"], pattern=r["pattern"], command=r["command"])
            for r in data.get("rules", [])
        ]

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for r in self._rules:
            lines.append("[[rules]]")
            lines.append(f'watch_dir = "{r.watch_dir}"')
            lines.append(f'pattern = "{r.pattern}"')
            lines.append(f'command = "{r.command}"')
            lines.append("")
        self._path.write_text("\n".join(lines), encoding="utf-8")

    def add(self, rule: WatchRule) -> None:
        self._rules.append(rule)

    def remove(self, idx: int) -> None:
        if 0 <= idx < len(self._rules):
            self._rules.pop(idx)

    def all(self) -> list[WatchRule]:
        return list(self._rules)


class WatchRuleEngine:
    """Snapshot-diff engine: detects new files, matches rules, runs commands."""

    def __init__(
        self,
        store: WatchRuleStore,
        on_fired: Callable[[WatchRule, Path], None] | None = None,
    ) -> None:
        self._store = store
        self._on_fired = on_fired
        self._snapshots: dict[str, set[Path]] = {}

    def check_dir(self, watch_dir: str) -> list[tuple[WatchRule, Path]]:
        """Check a directory for new files matching rules. Returns fired (rule, path) pairs."""
        dir_path = Path(watch_dir)
        if not dir_path.exists():
            return []
        try:
            curr = set(dir_path.iterdir())
        except OSError:
            return []
        prev = self._snapshots.get(watch_dir)  # None = no snapshot yet
        self._snapshots[watch_dir] = curr
        if prev is None:
            return []  # first snapshot — no diff
        new_files = curr - prev
        fired = []
        for f in new_files:
            for rule in self._store.all():
                if rule.watch_dir == watch_dir and fnmatch.fnmatch(f.name, rule.pattern):
                    cmd = rule.command.replace("{file}", str(f))
                    subprocess.Popen(cmd, shell=True, cwd=f.parent)
                    fired.append((rule, f))
                    if self._on_fired:
                        self._on_fired(rule, f)
        return fired

    def snapshot_dir(self, watch_dir: str) -> None:
        """Take initial snapshot without firing rules."""
        dir_path = Path(watch_dir)
        if dir_path.exists():
            try:
                self._snapshots[watch_dir] = set(dir_path.iterdir())
            except OSError:
                pass

    def unique_dirs(self) -> set[str]:
        return {r.watch_dir for r in self._store.all()}
