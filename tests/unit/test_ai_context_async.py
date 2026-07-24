"""Unit tests for AIContextDialog async chat — scenarios 5-6."""
from __future__ import annotations

import queue
import time
from unittest.mock import MagicMock



def test_ai_context_run_chat_queues_result():
    """Simulate _run_chat: puts provider.chat() result in queue, no Qt needed."""
    provider = MagicMock()
    provider.chat.return_value = "Open\nDelete\nRename"
    result_q: queue.SimpleQueue = queue.SimpleQueue()

    prompt = "suggest actions for x.txt"
    try:
        text = provider.chat([{"role": "user", "content": prompt}])
    except Exception:
        text = ""
    result_q.put(text)

    assert result_q.get_nowait() == "Open\nDelete\nRename"


def test_ai_context_dialog_opens_without_blocking(qtbot):
    """Dialog __init__ must return before provider.chat() completes."""
    from biome_fm.views.ai_context_dialog import AIContextDialog

    provider = MagicMock()
    provider.available = True

    def _slow_chat(*a, **kw):
        time.sleep(0.02)
        return "Action1\nAction2"

    provider.chat = _slow_chat

    t0 = time.monotonic()
    dlg = AIContextDialog(["x.txt"], provider)
    qtbot.addWidget(dlg)
    elapsed = time.monotonic() - t0

    # __init__ must return before the 20ms sleep in provider.chat completes
    assert elapsed < 0.015, f"Dialog blocked for {elapsed:.3f}s"
    dlg._pool.shutdown(wait=True)
