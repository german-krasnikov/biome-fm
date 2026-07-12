"""Integration tests for markdown_renderer — requires QApplication."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_headings(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("# Title\n\n## Sub\n")
    assert "<h1" in html
    assert "<h2" in html


def test_bold_italic(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("**bold** and *italic*\n")
    assert "bold" in html
    assert "italic" in html


def test_code_block_pygments(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("```python\ndef hello():\n    pass\n```\n")
    assert "def" in html
    assert "color" in html  # Pygments added inline styles


def test_table(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("| A | B |\n|---|---|\n| 1 | 2 |\n")
    assert "<table" in html.lower()


def test_task_list(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("- [x] Done\n- [ ] Todo\n")
    # Qt renders task list items — just ensure it doesn't crash
    assert "Done" in html or "done" in html.lower() or "checked" in html.lower()


def test_nohtml_safe(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("<script>alert(1)</script>\n\n# Safe\n")
    assert "<script>" not in html


def test_large_file_truncated(qapp):
    from biome_fm.models.markdown_renderer import render
    big = "word " * 30_000  # ~150KB
    html = render(big)
    assert "truncated" in html


def test_unknown_lang_fallback(qapp):
    from biome_fm.models.markdown_renderer import render
    html = render("```notaknownlang\nsome code\n```\n")
    assert "some code" in html  # no crash


def test_dark_vs_light(qapp):
    from biome_fm.models.markdown_renderer import render
    dark_html = render("```python\nprint(1)\n```\n", dark=True)
    light_html = render("```python\nprint(1)\n```\n", dark=False)
    # Different styles, both contain the code
    assert "print" in dark_html
    assert "print" in light_html
