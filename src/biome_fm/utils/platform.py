"""Platform-specific utilities."""

import sys

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")


def get_modifier_name() -> str:
    return "Cmd" if IS_MAC else "Ctrl"
