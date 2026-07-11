---
name: vfs-architecture
description: "VFS abstraction layer — fsspec, Protocol classes, adapters."
user-invocable: false
globs:
  - "src/biome_fm/models/vfs.py"
  - "src/biome_fm/plugins/**"
---

# VFS Architecture

## Protocol

```python
from typing import Protocol, Iterator
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class FileItem:
    name: str
    path: Path
    is_dir: bool
    size: int
    modified: float
    permissions: str = ""

class VFSProtocol(Protocol):
    def listdir(self, path: Path) -> list[FileItem]: ...
    def stat(self, path: Path) -> FileItem: ...
    def read_bytes(self, path: Path) -> bytes: ...
    def write_bytes(self, path: Path, data: bytes) -> None: ...
    def copy(self, src: Path, dst: Path) -> None: ...
    def move(self, src: Path, dst: Path) -> None: ...
    def delete(self, path: Path) -> None: ...
    def mkdir(self, path: Path) -> None: ...
    def exists(self, path: Path) -> bool: ...
```

## Local Implementation

```python
class LocalVFS:
    def listdir(self, path: Path) -> list[FileItem]:
        return [
            FileItem(
                name=entry.name,
                path=Path(entry.path),
                is_dir=entry.is_dir(),
                size=entry.stat().st_size if not entry.is_dir() else 0,
                modified=entry.stat().st_mtime,
            )
            for entry in os.scandir(path)
        ]
```

## fsspec Adapter

```python
import fsspec

class FsspecVFS:
    def __init__(self, protocol: str = "file", **kwargs):
        self._fs = fsspec.filesystem(protocol, **kwargs)

    def listdir(self, path: Path) -> list[FileItem]:
        entries = self._fs.ls(str(path), detail=True)
        return [self._to_file_item(e) for e in entries]
```

## Available fsspec Backends

| Protocol | URI | Use Case |
|----------|-----|----------|
| `file` | `/path/to/file` | Local filesystem |
| `sftp` | `sftp://host/path` | SSH/SFTP |
| `s3` | `s3://bucket/key` | AWS S3 |
| `zip` | `zip:///archive.zip` | ZIP archives |
| `tar` | `tar:///archive.tar` | TAR archives |
| `ftp` | `ftp://host/path` | FTP servers |
| `github` | `github://org:repo@branch` | GitHub repos |

## Testing VFS

```python
# Unit test with mock VFS
class MockVFS:
    def __init__(self, files: dict[str, bytes]):
        self._files = files

    def listdir(self, path):
        return [FileItem(name=k, ...) for k in self._files]

def test_presenter_uses_vfs():
    vfs = MockVFS({"a.txt": b"hello"})
    presenter = PanePresenter(MockView(), vfs)
    presenter.navigate(Path("/"))
    assert len(presenter.view.items) == 1
```
