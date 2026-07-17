from biome_fm.config import Config, load_config, save_config


def test_show_git_status_default():
    assert Config().show_git_status is True


def test_auto_preview_default():
    assert Config().auto_preview is True


def test_roundtrip(tmp_path):
    cfg = Config(show_git_status=False, auto_preview=False)
    p = tmp_path / "config.toml"
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.show_git_status is False
    assert loaded.auto_preview is False
