"""Shared test fixtures."""

import pytest


@pytest.fixture(scope="session")
def qapp_args():
    return ["biome-fm", "--test"]
