"""Shared fixtures: a simulated robot with its own copy of the config."""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from arctos import config, robot

POSES = {"home": [0, 0, 0, 0, 0, 0], "pick": [60, 40, -20, 0, -70, 0]}


@pytest.fixture
def cfg_dir(tmp_path: Path) -> Path:
    shutil.copy(config.DEFAULT_ROBOT, tmp_path / config.ROBOT_FILE)
    config.write_yaml(tmp_path / config.POSES_FILE, POSES)
    return tmp_path
