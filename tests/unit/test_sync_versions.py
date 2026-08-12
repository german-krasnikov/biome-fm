"""Unit tests for scripts/sync_versions.py — pure Python, no Qt."""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "sync_versions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_versions", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sync_versions"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_files(tmp_path, *, pyproject_ver="1.2.3", init_ver="1.2.3"):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'[project]\nversion = "{pyproject_ver}"\n', encoding="utf-8")
    init = tmp_path / "__init__.py"
    init.write_text(f'"""Biome FM."""\n\n__version__ = "{init_ver}"\n', encoding="utf-8")
    return pyproject, init


class TestReaders:
    def setup_method(self):
        self.mod = _load_module()

    def test_read_pyproject_version_ok(self, tmp_path):
        pyproject, _ = _make_files(tmp_path, pyproject_ver="0.9.0")
        assert self.mod._read_pyproject_version(pyproject) == "0.9.0"

    def test_read_pyproject_version_missing_field_exits(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "x"\n', encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            self.mod._read_pyproject_version(p)
        assert exc.value.code == 1

    def test_read_init_version_ok(self, tmp_path):
        _, init = _make_files(tmp_path, init_ver="2.0.0")
        assert self.mod._read_init_version(init) == "2.0.0"

    def test_read_init_version_missing_returns_placeholder(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text("# no version here\n", encoding="utf-8")
        assert self.mod._read_init_version(f) == "?"


class TestUpdaters:
    def setup_method(self):
        self.mod = _load_module()

    def test_update_pyproject_replaces_version(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
        result = self.mod._update_pyproject(p, "2.0.0")
        assert 'version = "2.0.0"' in result
        assert result.count('version = "2.0.0"') == 1

    def test_update_pyproject_raises_when_no_version_field(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "x"\n', encoding="utf-8")
        with pytest.raises(ValueError):
            self.mod._update_pyproject(p, "1.0.0")

    def test_update_init_replaces_existing_static_version(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
        result = self.mod._update_init(f, "0.2.0")
        assert '__version__ = "0.2.0"' in result

    def test_update_init_injects_version_when_dynamic_pattern(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text(
            '"""Biome FM."""\nfrom importlib.metadata import version\n'
            '__version__ = version("biome-fm")\n',
            encoding="utf-8",
        )
        result = self.mod._update_init(f, "0.5.0")
        assert '__version__ = "0.5.0"' in result

    def test_update_init_preserves_existing_docstring(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text(
            '"""My module."""\nfrom importlib.metadata import version\n'
            '__version__ = version("biome-fm")\n',
            encoding="utf-8",
        )
        result = self.mod._update_init(f, "0.5.0")
        assert result.startswith('"""My module."""')


class TestValidate:
    def setup_method(self):
        self.mod = _load_module()

    @pytest.mark.parametrize("v", ["0.1.0", "1.2.3", "10.20.30"])
    def test_validate_accepts_valid_semver(self, v):
        self.mod._validate(v)  # must not raise

    @pytest.mark.parametrize("v", ["1.2", "v1.2.3", "1.2.3.4", "abc", ""])
    def test_validate_rejects_nonsemver(self, v):
        with pytest.raises(SystemExit) as exc:
            self.mod._validate(v)
        assert exc.value.code == 1


class TestAtomicWrite:
    def setup_method(self):
        self.mod = _load_module()

    def test_atomic_write_creates_file_with_correct_content(self, tmp_path):
        f = tmp_path / "out.txt"
        self.mod._atomic_write(f, "hello")
        assert f.read_text() == "hello"

    def test_atomic_write_leaves_no_tmp_file(self, tmp_path):
        f = tmp_path / "out.txt"
        self.mod._atomic_write(f, "hello")
        # path.with_suffix(".tmp") → out.tmp
        assert not (tmp_path / "out.tmp").exists()


class TestCheckMode:
    def setup_method(self):
        self.mod = _load_module()

    def test_check_passes_when_versions_match(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="1.2.3")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        self.mod._check()  # must not raise or exit

    def test_check_exits_on_version_mismatch(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="9.9.9")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        with pytest.raises(SystemExit) as exc:
            self.mod._check()
        assert exc.value.code == 1

    def test_check_exits_on_invalid_semver_in_pyproject(self, tmp_path, monkeypatch):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "bad-ver"\n', encoding="utf-8")
        init = tmp_path / "__init__.py"
        init.write_text('__version__ = "bad-ver"\n', encoding="utf-8")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        with pytest.raises(SystemExit):
            self.mod._check()


class TestSyncMode:
    def setup_method(self):
        self.mod = _load_module()

    def test_sync_updates_init_only_when_not_canonical(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="0.0.1")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        self.mod._sync("1.2.3", update_canonical=False)
        assert '__version__ = "1.2.3"' in init.read_text()
        assert 'version = "1.2.3"' in pyproject.read_text()  # unchanged

    def test_sync_updates_both_when_canonical(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="1.2.3")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        self.mod._sync("2.0.0", update_canonical=True)
        assert 'version = "2.0.0"' in pyproject.read_text()
        assert '__version__ = "2.0.0"' in init.read_text()

    def test_sync_exits_if_target_file_missing(self, tmp_path, monkeypatch):
        pyproject, _ = _make_files(tmp_path)
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", tmp_path / "nonexistent.py")
        with pytest.raises(SystemExit) as exc:
            self.mod._sync("1.2.3", update_canonical=False)
        assert exc.value.code == 1

    def test_sync_rollback_on_second_write_failure(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="1.2.3")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        original = pyproject.read_bytes()

        call_count = [0]
        real_atomic = self.mod._atomic_write

        def failing_write(path, content):
            call_count[0] += 1
            if call_count[0] == 2:
                raise OSError("disk full")
            real_atomic(path, content)

        monkeypatch.setattr(self.mod, "_atomic_write", failing_write)
        with pytest.raises(SystemExit):
            self.mod._sync("2.0.0", update_canonical=True)
        assert pyproject.read_bytes() == original


class TestMain:
    def setup_method(self):
        self.mod = _load_module()

    def test_main_no_args_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["sync_versions.py"])
        with pytest.raises(SystemExit) as exc:
            self.mod.main()
        assert exc.value.code == 1

    def test_main_too_many_args_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["sync_versions.py", "1.2.3", "extra"])
        with pytest.raises(SystemExit):
            self.mod.main()

    def test_main_invalid_semver_arg_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["sync_versions.py", "not-semver"])
        with pytest.raises(SystemExit):
            self.mod.main()

    def test_main_check_mode(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="1.2.3")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        monkeypatch.setattr(sys, "argv", ["sync_versions.py", "--check"])
        self.mod.main()  # must not raise

    def test_main_sync_mode(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="0.0.1")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        monkeypatch.setattr(sys, "argv", ["sync_versions.py", "--sync"])
        self.mod.main()
        assert '__version__ = "1.2.3"' in init.read_text()

    def test_main_bump_mode(self, tmp_path, monkeypatch):
        pyproject, init = _make_files(tmp_path, pyproject_ver="1.2.3", init_ver="1.2.3")
        monkeypatch.setattr(self.mod, "PYPROJECT", pyproject)
        monkeypatch.setattr(self.mod, "INIT_PY", init)
        monkeypatch.setattr(sys, "argv", ["sync_versions.py", "3.0.0"])
        self.mod.main()
        assert 'version = "3.0.0"' in pyproject.read_text()
        assert '__version__ = "3.0.0"' in init.read_text()
