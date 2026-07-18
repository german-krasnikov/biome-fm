"""Unit tests for transfer speed/ETA helpers — pure Python, no Qt."""
import pytest
from biome_fm.utils.transfer_stats import TransferStats, format_speed, format_eta


def test_format_speed_human_readable():
    assert format_speed(2_000_000_000) == "2.0 GB/s"
    assert format_speed(1_200_000) == "1.2 MB/s"
    assert format_speed(456_000) == "456.0 KB/s"
    assert format_speed(500) == "500.0 B/s"


def test_format_eta_seconds():
    assert format_eta(0.5) == "< 1s"
    assert format_eta(45) == "45s"
    assert format_eta(83) == "1m 23s"
    assert format_eta(135) == "2m 15s"
    assert format_eta(3661) == "1h 1m"


def test_eta_from_speed_and_remaining():
    stats = TransferStats()
    stats.update(t=0.0, bytes_done=0, bytes_total=10_000)
    stats.update(t=1.0, bytes_done=1_000, bytes_total=10_000)
    # 9000 bytes left at 1000 B/s = 9s
    assert stats.eta_seconds() == pytest.approx(9.0, rel=0.1)


def test_speed_calculation_bytes_per_second():
    stats = TransferStats()
    stats.update(t=0.0, bytes_done=0, bytes_total=10_000)
    stats.update(t=2.0, bytes_done=2_000, bytes_total=10_000)
    # instant = 1000 B/s; first sample seeds EWMA to that value
    assert stats.speed_bps() == pytest.approx(1_000.0, rel=0.01)


def test_speed_smoothing_ewma():
    stats = TransferStats()
    stats.update(t=0.0, bytes_done=0, bytes_total=10_000)
    stats.update(t=1.0, bytes_done=1_000, bytes_total=10_000)  # 1000 B/s
    stats.update(t=2.0, bytes_done=3_000, bytes_total=10_000)  # instant 2000 B/s
    # EWMA: 0.3 * 2000 + 0.7 * 1000 = 1300
    assert stats.speed_bps() == pytest.approx(1_300.0, rel=0.01)


def test_zero_speed_shows_unknown_eta():
    stats = TransferStats()
    stats.update(t=0.0, bytes_done=0, bytes_total=10_000)
    # no second sample → speed=0 → eta=None, not ZeroDivisionError
    assert stats.eta_seconds() is None
    assert stats.speed_bps() == 0.0


def test_eta_when_complete():
    stats = TransferStats()
    stats.update(t=0.0, bytes_done=0, bytes_total=10_000)
    stats.update(t=1.0, bytes_done=10_000, bytes_total=10_000)
    assert stats.eta_seconds() == pytest.approx(0.0, abs=0.01)
