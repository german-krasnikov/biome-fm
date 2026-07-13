"""MCP CLI dispatcher — routes argv to handlers without touching Qt."""

from __future__ import annotations

import sys

UNHANDLED = object()

_COMMANDS = {"version", "configure", "doctor", "uninstall", "mcp"}


def dispatch(argv: list[str]) -> int | object:
    """Route known subcommands; return UNHANDLED for anything else."""
    if not argv or argv[0] not in _COMMANDS:
        return UNHANDLED
    cmd = argv[0]
    if cmd == "version":
        return _version()
    if cmd == "configure":
        return _configure(argv[1:])
    if cmd == "doctor":
        return _doctor()
    if cmd == "uninstall":
        return _uninstall(argv[1:])
    if cmd == "mcp":
        return _serve()
    return UNHANDLED  # unreachable but satisfies type checker


def _version() -> int:
    from biome_fm import __version__
    print(__version__)
    return 0


def _configure(argv: list[str]) -> int:
    from . import clients, merger
    from .resolver import build_server_entry

    entry = build_server_entry()
    keys: list[str] = []

    for arg in argv:
        if arg.startswith("--client="):
            key = arg[9:]
            if key not in clients.CLIENT_REGISTRY:
                print(f"Unknown client: {key}", file=sys.stderr)
                return 1
            keys.append(key)  # accumulate, last flag no longer wins

    if not keys:
        keys = clients.detect_installed()

    if not keys:
        print("No supported MCP clients detected.", file=sys.stderr)
        return 1

    failures = 0
    for key in keys:
        info = clients.CLIENT_REGISTRY[key]
        try:
            if info.is_toml:
                merger.merge_toml_mcp(info.config_path, entry)
            else:
                merger.merge_mcp_config(info, entry)
            print(f"Configured {info.name}")
        except Exception as exc:
            print(f"Failed to configure {info.name}: {exc}", file=sys.stderr)
            failures += 1

    return 1 if failures == len(keys) else 0


def _doctor() -> int:
    import json
    import tomllib

    from . import clients

    found = False
    for key, info in clients.CLIENT_REGISTRY.items():
        if not info.config_path.exists():
            continue
        try:
            raw = info.config_path.read_text(encoding="utf-8")
            if info.is_toml:
                data = tomllib.loads(raw)
            else:
                data = json.loads(raw)
            section = data.get(info.root_key, {})
            status = "[OK]" if clients.SERVER_NAME in section else "[--]"
            print(f"{status} {info.name}")
            if clients.SERVER_NAME in section:
                found = True
        except Exception:
            print(f"[ERR] {info.name}: could not read config")

    if not found:
        print(f"{clients.SERVER_NAME} not configured in any client.")
    return 0


def _uninstall(argv: list[str]) -> int:
    from . import clients, merger

    keys = list(clients.CLIENT_REGISTRY.keys())
    for arg in argv:
        if arg.startswith("--client="):
            keys = [arg[9:]]

    for key in keys:
        info = clients.CLIENT_REGISTRY.get(key)
        if info is None:
            continue
        removed = (
            merger.remove_toml_mcp_entry(info.config_path)
            if info.is_toml
            else merger.remove_mcp_entry(info)
        )
        if removed:
            print(f"Removed from {info.name}")

    return 0


def _serve() -> int:
    from biome_fm.mcp._entry import main as mcp_main  # lazy — optional dep
    return mcp_main()
