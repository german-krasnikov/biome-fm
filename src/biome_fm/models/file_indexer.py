"""Background file indexer using SQLite FTS5."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class FileIndexer(QObject):
    indexing_done = Signal()

    def __init__(self, db_path: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS files USING fts5(name, path)"
            )

    def index_dir(self, path: Path) -> None:
        """Index directory in background thread; emit indexing_done when done."""
        t = threading.Thread(target=self._do_index, args=(path,), daemon=True)
        t.start()

    def _do_index(self, path: Path) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM files WHERE path LIKE ?", (str(path) + "%",))
            rows = [
                (p.name, str(p))
                for p in path.rglob("*")
                if p.is_file()
            ]
            conn.executemany("INSERT INTO files(name, path) VALUES (?, ?)", rows)
        self.indexing_done.emit()

    def search(self, query: str) -> list[Path]:
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute(
                "SELECT path FROM files WHERE files MATCH ? ORDER BY rank",
                (query,),
            )
            return [Path(row[0]) for row in cur.fetchall()]
