"""Tests for _extract_shell_blocks() shell block detector."""
from biome_fm.presenters.ai_presenter import _extract_shell_blocks


def test_single_bash_block():
    assert _extract_shell_blocks("```bash\nls -la\n```") == ["ls -la"]


def test_multiple_blocks():
    text = "```bash\nls\n```\nsome text\n```bash\nrm foo\n```"
    assert _extract_shell_blocks(text) == ["ls", "rm foo"]


def test_sh_block():
    assert _extract_shell_blocks("```sh\necho hi\n```") == ["echo hi"]


def test_python_block_ignored():
    assert _extract_shell_blocks("```python\nprint('hi')\n```") == []


def test_no_blocks():
    assert _extract_shell_blocks("plain text no blocks") == []
