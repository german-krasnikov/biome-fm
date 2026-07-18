"""GroupDelegate — draws group header bars in the file list."""
from __future__ import annotations

from biome_fm.models.directory_model import COL_NAME, GROUP_ROLE
from biome_fm.qt import QStyledItemDelegate, Qt


class GroupDelegate(QStyledItemDelegate):
    """Draws a thin colored header bar at the top of the first row in each group.

    Reads GROUP_ROLE from the proxy model index — no internal state needed.
    """

    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)
        if index.column() != COL_NAME:
            return
        group = index.data(GROUP_ROLE)
        if not group:
            return
        prev_group = index.sibling(index.row() - 1, 0).data(GROUP_ROLE) if index.row() > 0 else None
        if group == prev_group:
            return
        # Draw a bold separator line + group label above this cell
        painter.save()
        r = option.rect
        accent = option.palette.highlight().color()
        painter.setPen(accent)
        painter.drawLine(r.left(), r.top(), r.right(), r.top())
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() * 0.8)
        painter.setFont(font)
        painter.setPen(option.palette.text().color())
        painter.drawText(
            r.adjusted(2, 0, 0, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            group,
        )
        painter.restore()
