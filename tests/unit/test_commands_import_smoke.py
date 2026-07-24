"""Smoke test: every live command module imports cleanly; dead ones do not."""
import importlib
import pytest

LIVE_COMMANDS = [
    "biome_fm.commands.archive_cmd",
    "biome_fm.commands.checksum_cmd",
    "biome_fm.commands.chmod_cmd",
    "biome_fm.commands.copy_cmd",
    "biome_fm.commands.delete_cmd",
    "biome_fm.commands.editor_rename_cmd",
    "biome_fm.commands.git_stage",
    "biome_fm.commands.mkdir_cmd",
    "biome_fm.commands.move_cmd",
    "biome_fm.commands.multi_rename_cmd",
    "biome_fm.commands.new_file_cmd",
    "biome_fm.commands.quarantine_cmd",
    "biome_fm.commands.remote_edit_cmd",
    "biome_fm.commands.rename_cmd",
    "biome_fm.commands.symlink_cmd",
    "biome_fm.commands.tag_cmd",
    "biome_fm.commands.trash_cmd",
]

DEAD_COMMANDS = [
    "biome_fm.commands.rsync_cmd",
    "biome_fm.commands.batch_exec_cmd",
    "biome_fm.commands.export_listing_cmd",
    "biome_fm.commands.replace_cmd",
    "biome_fm.commands.chown_cmd",
]


@pytest.mark.parametrize("mod", LIVE_COMMANDS)
def test_live_command_importable(mod):
    importlib.import_module(mod)  # must not raise


@pytest.mark.parametrize("mod", DEAD_COMMANDS)
def test_dead_command_not_importable(mod):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(mod)
