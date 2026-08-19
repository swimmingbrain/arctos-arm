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


def test_load_from_file_and_env(cfg_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s = config.load(cfg_dir / config.ROBOT_FILE)
    assert s.dir == cfg_dir
    monkeypatch.setenv(config.ENV_CONFIG, str(cfg_dir))
    assert config.load().dir == cfg_dir


def test_save_pose_writes_yaml(cfg_dir: Path) -> None:
    s = config.load(cfg_dir)
    s.save_pose("test", [1.234, 2, 3, 4, 5, 6])
    again = config.load(cfg_dir)
    assert again.pose("test") == [1.23, 2, 3, 4, 5, 6]


def test_save_offsets(cfg_dir: Path) -> None:
    s = config.load(cfg_dir)
    assert s.offsets == {}
    s.save_offsets({"x": -55.123456, "y": 0})
    assert config.load(cfg_dir).offsets == {"x": -55.123, "y": 0.0}
