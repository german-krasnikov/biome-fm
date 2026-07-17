"""TDD: Dev project detection via marker files."""
from __future__ import annotations

from pathlib import Path


def test_python_detected(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").touch()
    from biome_fm.models.project_detector import detect_project

    info = detect_project(tmp_path)
    assert info is not None
    assert info.type == "python"
    assert info.root == tmp_path
    assert info.name == tmp_path.name


def test_node_detected(tmp_path: Path) -> None:
    (tmp_path / "package.json").touch()
    from biome_fm.models.project_detector import detect_project

    info = detect_project(tmp_path)
    assert info is not None
    assert info.type == "node"


def test_no_project_returns_none(tmp_path: Path) -> None:
    from biome_fm.models.project_detector import detect_project

    assert detect_project(tmp_path) is None


def test_parent_search(tmp_path: Path) -> None:
    """Marker in parent dir should be detected from a child."""
    (tmp_path / "Cargo.toml").touch()
    child = tmp_path / "src"
    child.mkdir()
    from biome_fm.models.project_detector import detect_project

    info = detect_project(child)
    assert info is not None
    assert info.type == "rust"
    assert info.root == tmp_path
