"""Smoke test: live modules import cleanly. Dead ones must not exist."""
from __future__ import annotations

import importlib

import pytest

DEAD_PRESENTERS = [
    "biome_fm.presenters.column_state",
    "biome_fm.presenters.quick_view_state",
    "biome_fm.presenters.miller_state",
    "biome_fm.presenters.cross_marks",
    "biome_fm.presenters.hotlist",
    "biome_fm.presenters.macro_recorder",
    "biome_fm.presenters.copy_filter",
    "biome_fm.presenters.predictive_dest",
    "biome_fm.presenters.semantic_search",
    "biome_fm.presenters.ai_group_rename",
    "biome_fm.presenters.project_actions",
    "biome_fm.presenters.drive_list",
    "biome_fm.presenters.sync_conflict",
    "biome_fm.presenters.path_yank",
    "biome_fm.presenters.uri_parser",
]

DEAD_MODELS = [
    "biome_fm.models.file_indexer",
    "biome_fm.models.metadata_reader",
    "biome_fm.models.gitignore_filter",
    "biome_fm.models.filter_predicate",
    "biome_fm.models.cloud_connection_store",
    "biome_fm.models.watch_rules",
]

DEAD_VIEWS = [
    "biome_fm.views.upload_queue_panel",
    "biome_fm.views.disk_usage_widget",
    "biome_fm.views.fayt_bar",
    "biome_fm.views.op_log_panel",
]

DEAD_IPC = [
    "biome_fm.ipc.server",
    "biome_fm.ipc.client",
    "biome_fm.ipc.rest_server",
]

DEAD_GIT = [
    "biome_fm.git.conflict_ops",
    "biome_fm.git.virtual_pane",
]

DEAD_UTILS = [
    "biome_fm.utils.transfer_stats",
]

ALL_DEAD = DEAD_PRESENTERS + DEAD_MODELS + DEAD_VIEWS + DEAD_IPC + DEAD_GIT + DEAD_UTILS


@pytest.mark.parametrize("mod", ALL_DEAD)
def test_dead_module_not_importable(mod):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(mod)
