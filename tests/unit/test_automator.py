"""F324 — Open in Biome FM: Automator Quick Action generator."""
import sys


def test_generate_quick_action_returns_script():
    from biome_fm.cli.automator import generate_quick_action
    script = generate_quick_action()
    assert isinstance(script, str)
    assert len(script) > 0
    # Should reference biome-fm to open the selected folder
    assert "biome" in script.lower() or "biome-fm" in script.lower()


def test_install_noop_non_darwin(monkeypatch):
    """install_quick_action does nothing on non-macOS platforms."""
    monkeypatch.setattr(sys, "platform", "linux")
    from biome_fm.cli import automator
    # Reload to pick up the monkeypatched platform check
    import importlib
    importlib.reload(automator)

    # Should not raise, should not write any files
    automator.install_quick_action()  # no exception = pass
