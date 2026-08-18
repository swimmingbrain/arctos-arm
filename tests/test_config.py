"""Tests for loading and saving the configuration."""

from pathlib import Path

import pytest

from arctos import config


def test_load_from_dir(cfg_dir: Path) -> None:
    s = config.load(cfg_dir)
    assert s.joint_names == ["x", "y", "z", "a", "b", "c"]
    assert s.section("can")["bitrate"] == 500000
    assert s.pose("home") == [0, 0, 0, 0, 0, 0]
    assert s.section("nothing") == {}
    assert s.source == cfg_dir / config.ROBOT_FILE
