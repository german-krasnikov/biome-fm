from unittest.mock import patch
from pathlib import Path
from biome_fm.plastic._replication import (
    package_create, package_import, replication_pull, replication_push,
)


def test_replication_push_calls_cm(tmp_path):
    with patch("biome_fm.plastic._replication.run_cm", return_value="ok") as m:
        result = replication_push("srv", "repo", tmp_path)
    assert "replication" in m.call_args[0][0]
    assert result == "ok"


def test_replication_pull_calls_cm(tmp_path):
    with patch("biome_fm.plastic._replication.run_cm", return_value="ok") as m:
        result = replication_pull("srv", tmp_path)
    assert result == "ok"


# ── Package replication (#9) ──────────────────────────────────────────────────

def test_package_create_calls_cm(tmp_path):
    with patch("biome_fm.plastic._replication.run_cm", return_value="") as m:
        package_create("/out/pkg.rep", tmp_path)
    assert "package" in m.call_args[0][0]


def test_package_import_calls_cm(tmp_path):
    with patch("biome_fm.plastic._replication.run_cm", return_value="") as m:
        package_import("/out/pkg.rep", tmp_path)
    assert "import" in m.call_args[0][0]
