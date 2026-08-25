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


def test_missing_pose(cfg_dir: Path) -> None:
    with pytest.raises(KeyError):
        config.load(cfg_dir).pose("nope")


def test_missing_config(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        config.load(tmp_path)


def test_default_config_when_nothing_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(config.ENV_CONFIG, raising=False)
    s = config.load()
    assert s.source == config.DEFAULT_ROBOT
    assert s.joint_names == ["x", "y", "z", "a", "b", "c"]
    assert s.dir == tmp_path / "config"


def test_init_copies_default(tmp_path: Path) -> None:
    target = config.init(tmp_path / "cfg")
    assert target == tmp_path / "cfg" / config.ROBOT_FILE
    assert target.exists()
    assert (tmp_path / "cfg" / config.POSES_FILE).exists()
    with pytest.raises(FileExistsError):
        config.init(tmp_path / "cfg")
    config.init(tmp_path / "cfg", force=True)
    assert config.load(tmp_path / "cfg").pose("home") == [0.0] * 6
