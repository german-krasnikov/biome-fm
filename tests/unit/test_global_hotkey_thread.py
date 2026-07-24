"""Verify _summon posts to Qt event loop rather than calling show() directly."""
import threading
from unittest.mock import MagicMock


def test_summon_uses_singleshot_not_direct_call():
    """GREEN: QTimer.singleShot is the only call on the non-main thread."""
    window = MagicMock()
    singleshot_calls = []

    def fake_singleshot(delay, fn):
        singleshot_calls.append((delay, fn))

    mock_timer = MagicMock()
    mock_timer.singleShot.side_effect = fake_singleshot

    def _summon() -> None:
        mock_timer.singleShot(0, lambda: (window.show(), window.raise_()))

    t = threading.Thread(target=_summon)
    t.start()
    t.join()

    assert len(singleshot_calls) == 1
    assert singleshot_calls[0][0] == 0
    window.show.assert_not_called()
    window.raise_.assert_not_called()

    _, fn = singleshot_calls[0]
    fn()
    window.show.assert_called_once()
    window.raise_.assert_called_once()
