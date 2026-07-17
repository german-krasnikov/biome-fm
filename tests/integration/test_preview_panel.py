"""Integration tests for PreviewPanel — requires Qt (offscreen)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.preview.provider import ContentKind, PreviewResult
from biome_fm.views.preview_panel import PreviewPanel


def test_show_html_result(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    result = PreviewResult(kind=ContentKind.HTML, data="<p>hello</p>")
    panel.show_result(result)
    assert panel._text_view == panel._stack.currentWidget()


def test_show_text_result(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    result = PreviewResult(kind=ContentKind.TEXT, data="plain text")
    panel.show_result(result)
    assert panel._text_view == panel._stack.currentWidget()


def test_show_error_result(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    result = PreviewResult(kind=ContentKind.ERROR, data="something went wrong")
    panel.show_result(result)
    assert panel._text_view == panel._stack.currentWidget()


def test_set_busy(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.set_busy(True)
    assert panel._stack.currentWidget() == panel._busy_label


def test_is_panel_visible_false_by_default(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    assert not panel.is_panel_visible()


def test_set_visible_shows(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.set_visible(True)
    assert panel.isVisible()


def test_set_visible_hides(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.set_visible(False)
    qtbot.wait(250)  # wait for animation
    assert not panel.isVisible()


def test_show_markdown_result(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    result = PreviewResult(kind=ContentKind.MARKDOWN, data="# Hello\n\nworld")
    panel.show_result(result)
    assert panel._text_view == panel._stack.currentWidget()


def test_show_image_result(qtbot):
    """IMAGE result should set img_label as current widget."""
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    # Create minimal valid PNG (1x1 white pixel)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    result = PreviewResult(kind=ContentKind.IMAGE, data=png_bytes)
    panel.show_result(result)
    assert panel._stack.currentWidget() == panel._img_widget
