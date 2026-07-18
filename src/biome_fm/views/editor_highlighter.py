"""PygmentsHighlighter — QSyntaxHighlighter backed by Pygments (F260)."""
from __future__ import annotations

from pygments import lex
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.token import Token
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat

_MAX_FILE_BYTES = 512 * 1024  # 50KB guard; skip highlighting for large files

# Map broad Pygments token categories → (fg_light, fg_dark)
_TOKEN_COLORS: dict[object, tuple[str, str]] = {
    Token.Keyword:           ("#0000FF", "#569CD6"),
    Token.Keyword.Constant:  ("#0000FF", "#569CD6"),
    Token.Name.Builtin:      ("#008080", "#4EC9B0"),
    Token.Name.Function:     ("#795E26", "#DCDCAA"),
    Token.Name.Class:        ("#267F99", "#4EC9B0"),
    Token.String:            ("#A31515", "#CE9178"),
    Token.String.Doc:        ("#A31515", "#CE9178"),
    Token.Number:            ("#098658", "#B5CEA8"),
    Token.Comment:           ("#008000", "#6A9955"),
    Token.Comment.Single:    ("#008000", "#6A9955"),
    Token.Comment.Multiline: ("#008000", "#6A9955"),
    Token.Operator:          ("#000000", "#D4D4D4"),
    Token.Punctuation:       ("#000000", "#D4D4D4"),
}


def _build_formats(dark: bool = True) -> dict[object, QTextCharFormat]:
    """Pure: returns QTextCharFormat per Pygments token type."""
    result: dict[object, QTextCharFormat] = {}
    for token, (light, dk) in _TOKEN_COLORS.items():
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(dk if dark else light))
        result[token] = fmt
    return result


class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document, filename: str, dark: bool = True) -> None:
        super().__init__(document)
        try:
            self._lexer = get_lexer_for_filename(filename, stripall=True)
        except Exception:
            self._lexer = TextLexer()
        self._formats = _build_formats(dark)
        # File size guard: disable if doc text too large
        self._enabled = document.characterCount() <= _MAX_FILE_BYTES

    def highlightBlock(self, text: str) -> None:
        if not self._enabled:
            return
        col = 0
        for ttype, value in lex(text, self._lexer):
            fmt = None
            # Walk up token hierarchy to find a matching format
            t = ttype
            while t is not None:
                if t in self._formats:
                    fmt = self._formats[t]
                    break
                t = t.parent if hasattr(t, "parent") else None
            if fmt is not None:
                self.setFormat(col, len(value), fmt)
            col += len(value)
