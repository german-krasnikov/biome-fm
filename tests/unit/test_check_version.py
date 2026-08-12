"""Unit tests for scripts/check_version.py — pure Python, no Qt."""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "check_version.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_version", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_version"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def version_tree(tmp_path: Path):
    """All three required files, consistent at 0.34.0."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "0.34.0"\n', encoding="utf-8"
    )
    (tmp_path / "__init__.py").write_text(
        '__version__ = "0.34.0"\n', encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "## [v0.34.0] — 2025-01-01\n\n- initial\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def patched(version_tree, monkeypatch):
    mod = _load_module()
    monkeypatch.setattr(mod, "PYPROJECT", version_tree / "pyproject.toml")
    monkeypatch.setattr(mod, "INIT_PY", version_tree / "__init__.py")
    monkeypatch.setattr(mod, "CHANGELOG", version_tree / "CHANGELOG.md")
    return mod, version_tree


class TestReadPyprojectVersion:
    def setup_method(self):
        self.mod = _load_module()

    def test_read_pyproject_version_ok(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
        assert self.mod._read_pyproject_version(p) == "1.0.0"

    def test_read_pyproject_version_missing_exits(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "x"\n', encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._read_pyproject_version(p)


class TestCheckInit:
    def setup_method(self):
        self.mod = _load_module()

    def test_check_init_ok(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text('__version__ = "0.34.0"\n', encoding="utf-8")
        self.mod._check_init(f, "0.34.0")  # must not raise

    def test_check_init_missing_version_attr_exits(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text("# no version\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._check_init(f, "0.34.0")

    def test_check_init_dynamic_not_literal_exits(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text('__version__ = version("biome-fm")\n', encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._check_init(f, "0.34.0")

    def test_check_init_version_mismatch_exits(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text('__version__ = "9.9.9"\n', encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._check_init(f, "0.34.0")


class TestCheckChangelog:
    def setup_method(self):
        self.mod = _load_module()

    def test_check_changelog_ok(self, tmp_path):
        f = tmp_path / "CHANGELOG.md"
        f.write_text("## [v0.34.0] — 2025-01-01\n\n- initial\n", encoding="utf-8")
        self.mod._check_changelog(f, "0.34.0")  # must not raise

    def test_check_changelog_missing_entry_exits(self, tmp_path):
        f = tmp_path / "CHANGELOG.md"
        f.write_text("## [v0.33.0] — 2024-12-01\n\n- old\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._check_changelog(f, "0.34.0")

    def test_check_changelog_wrong_format_exits(self, tmp_path):
        f = tmp_path / "CHANGELOG.md"
        # Single # and no brackets — wrong heading level/bracket style
        f.write_text("# v0.34.0\n\n- initial\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            self.mod._check_changelog(f, "0.34.0")


class TestMain:
    def test_main_all_consistent_exits_zero(self, patched):
        mod, _ = patched
        mod.main()  # must not raise

    def test_main_missing_pyproject_exits(self, patched):
        mod, tree = patched
        (tree / "pyproject.toml").unlink()
        with pytest.raises(SystemExit):
            mod.main()

    def test_main_missing_init_exits(self, patched):
        mod, tree = patched
        (tree / "__init__.py").unlink()
        with pytest.raises(SystemExit):
            mod.main()

    def test_main_missing_changelog_exits(self, patched):
        mod, tree = patched
        (tree / "CHANGELOG.md").unlink()
        with pytest.raises(SystemExit):
            mod.main()

    def test_main_invalid_semver_exits(self, patched):
        mod, tree = patched
        (tree / "pyproject.toml").write_text(
            '[project]\nversion = "bad"\n', encoding="utf-8"
        )
        with pytest.raises(SystemExit):
            mod.main()

    def test_main_init_version_mismatch_exits(self, patched):
        mod, tree = patched
        (tree / "__init__.py").write_text(
            '__version__ = "0.1.0"\n', encoding="utf-8"
        )
        with pytest.raises(SystemExit):
            mod.main()

    def test_main_changelog_missing_entry_exits(self, patched):
        mod, tree = patched
        (tree / "CHANGELOG.md").write_text(
            "## [v0.1.0] — 2024-01-01\n\n- old\n", encoding="utf-8"
        )
        with pytest.raises(SystemExit):
            mod.main()
