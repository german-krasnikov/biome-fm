"""F227 — Smart Folders (search bookmarks) tests."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.bookmark_node import BookmarkNode, parse_search_uri


def test_search_bookmark_roundtrip() -> None:
    node = BookmarkNode(
        kind="search",
        path=Path("search://name=*.py&content=TODO"),
        name="Find TODOs",
    )
    assert node.kind == "search"
    params = parse_search_uri(str(node.path))
    assert params["name"] == "*.py"
    assert params["content"] == "TODO"


def test_search_uri_parsing() -> None:
    uri = "search://name=*.txt&content=FIXME"
    params = parse_search_uri(uri)
    assert params["name"] == "*.txt"
    assert params["content"] == "FIXME"


# ── SearchCoordinator.request_search_from_template ────────────────────────────

from unittest.mock import ANY, MagicMock, patch  # noqa: E402

from biome_fm.models.search_template_store import SearchTemplate  # noqa: E402
from biome_fm.presenters.search_coordinator import SearchCoordinator  # noqa: E402


class _FakeVFS:
    pass


class _FakeCoord:
    def toggle(self, *a) -> None:
        pass


class _FakeManager:
    active_pane_id = "left"


class _FakePanel:
    def __init__(self) -> None:
        self.last_query: str | None = None

    def on_search_started(self, q: str) -> None:
        self.last_query = q

    def add_results(self, r: list) -> None:
        pass

    def on_finished(self, n: int) -> None:
        pass

    def on_cancelled(self) -> None:
        pass


class _FakeTabs:
    current_path = Path("/tmp")


def _make_sc(panel=None):
    return SearchCoordinator(
        _FakeVFS(), _FakeCoord(), _FakeManager(),
        panel or _FakePanel(),
        lambda: _FakeTabs(),
    )


def _mock_presenter():
    inst = MagicMock()
    inst.is_cancelled = False
    return MagicMock(return_value=inst), inst


def test_request_search_from_template_puts_sentinel():
    """Template search puts None sentinel on success."""
    sc = _make_sc()
    cls, _ = _mock_presenter()
    with patch("biome_fm.presenters.search_presenter.SearchPresenter", cls):
        sc.request_search_from_template(SearchTemplate("py files", "*.py", "wildcard"))
    assert sc._queue.get(timeout=2) is None


def test_template_pattern_forwarded():
    """pattern/mode/max_results are forwarded to SearchPresenter.search."""
    from biome_fm.presenters.search_presenter import SearchScope
    sc = _make_sc()
    cls, inst = _mock_presenter()
    with patch("biome_fm.presenters.search_presenter.SearchPresenter", cls):
        sc.request_search_from_template(SearchTemplate("todos", "TODO", "content", max_results=50))
    sc._queue.get(timeout=2)
    inst.search.assert_called_once_with(
        "TODO", mode="content", max_results=50, on_match=ANY, scope=SearchScope.SUBTREE
    )


def test_cancels_previous_on_new_template():
    """Second call cancels the previous presenter and clears the flag."""
    sc = _make_sc()
    cls, inst = _mock_presenter()
    with patch("biome_fm.presenters.search_presenter.SearchPresenter", cls):
        sc.request_search_from_template(SearchTemplate("a", "*.log", "wildcard"))
        sc._queue.get(timeout=2)
        sc.request_search_from_template(SearchTemplate("b", "*.py", "wildcard"))
        sc._queue.get(timeout=2)
    assert not sc._cancel_flag.is_set()
    inst.cancel.assert_called()


def test_panel_notified_with_pattern():
    """panel.on_search_started receives the template pattern."""
    panel = _FakePanel()
    sc = _make_sc(panel)
    cls, _ = _mock_presenter()
    with patch("biome_fm.presenters.search_presenter.SearchPresenter", cls):
        sc.request_search_from_template(SearchTemplate("logs", "*.log", "wildcard"))
    sc._queue.get(timeout=2)
    assert panel.last_query == "*.log"
