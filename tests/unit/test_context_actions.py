"""Unit tests for ai.context_actions — builtin_actions()."""
from biome_fm.ai.context_actions import builtin_actions


def test_python_actions():
    actions = builtin_actions(".py")
    assert ("Run", "run") in actions


def test_unknown_ext():
    assert builtin_actions(".xyz") == []


def test_image_actions():
    actions = builtin_actions(".jpg")
    assert ("Open Preview", "preview") in actions


def test_case_insensitive():
    assert builtin_actions(".PY") == builtin_actions(".py")
