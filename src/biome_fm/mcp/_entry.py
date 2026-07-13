"""MCP server entry point — stdio transport."""
from pathlib import Path


def main(allowed_roots: list[Path] | None = None) -> int:
    from biome_fm.mcp.server import create_server
    create_server(allowed_roots).run()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(allowed_roots=[Path.home()]))
