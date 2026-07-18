"""Transfer speed/ETA helpers — pure Python, no Qt."""
from __future__ import annotations

_ALPHA = 0.3  # EWMA smoothing factor


def format_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec >= 1_000_000_000:
        return f"{bytes_per_sec / 1_000_000_000:.1f} GB/s"
    if bytes_per_sec >= 1_000_000:
        return f"{bytes_per_sec / 1_000_000:.1f} MB/s"
    if bytes_per_sec >= 1_000:
        return f"{bytes_per_sec / 1_000:.1f} KB/s"
    return f"{bytes_per_sec:.1f} B/s"


def format_eta(seconds: float) -> str:
    if seconds < 1:
        return "< 1s"
    s = int(seconds)
    if s >= 3600:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    if s >= 60:
        return f"{s // 60}m {s % 60}s"
    return f"{s}s"


class TransferStats:
    """EWMA-smoothed speed tracker."""

    def __init__(self) -> None:
        self._speed: float = 0.0
        self._last_t: float | None = None
        self._last_bytes: int = 0
        self._remaining: int = 0

    def update(self, t: float, bytes_done: int, bytes_total: int) -> None:
        self._remaining = max(bytes_total - bytes_done, 0)
        if self._last_t is None:
            self._last_t = t
            self._last_bytes = bytes_done
            return
        dt = t - self._last_t
        if dt <= 0:
            return
        instant = (bytes_done - self._last_bytes) / dt
        self._speed = (
            instant if self._speed == 0.0
            else _ALPHA * instant + (1 - _ALPHA) * self._speed
        )
        self._last_t = t
        self._last_bytes = bytes_done

    def speed_bps(self) -> float:
        return self._speed

    def eta_seconds(self) -> float | None:
        if self._speed <= 0:
            return None
        return self._remaining / self._speed
