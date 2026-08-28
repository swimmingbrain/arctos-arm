"""Tests for the command line, everything in the simulation."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from arctos import __version__
from arctos.cli import app

runner = CliRunner()


def run(cfg_dir: Path, *args: str) -> str:
    result = runner.invoke(
        app, ["--sim", "--speedup", "200", "--config", str(cfg_dir), *args]
    )
    assert result.exit_code == 0, result.output
    return result.output


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "status" in result.output and "calibrate" in result.output


def test_status_and_scan(cfg_dir: Path) -> None:
    out = run(cfg_dir, "status")
    assert "x=" in out and "tool:" in out
    out = run(cfg_dir, "scan")
    assert out.count(": ok") == 6


def test_move_and_joints(cfg_dir: Path) -> None:
    out = run(cfg_dir, "move", "x", "25")
    assert "x=  25.0" in out
    out = run(cfg_dir, "joints", "0", "10", "-10", "0", "-20", "0")
    assert "y=  10.0" in out and "b= -20.0" in out
    out = run(cfg_dir, "jog", "x", "--", "-5")
    assert "x=  -5.0" in out


def test_teach_and_pose(cfg_dir: Path) -> None:
    run(cfg_dir, "move", "x", "12")
    run(cfg_dir, "teach", "test")
    out = run(cfg_dir, "poses")
    assert "home" in out and "test" in out
    out = run(cfg_dir, "pose", "home")
    assert "x=   0.0" in out


def test_calibrate(cfg_dir: Path) -> None:
    run(cfg_dir, "move", "x", "12")
    out = run(cfg_dir, "calibrate")
    assert "offsets saved" in out
    assert (cfg_dir / "offsets.yaml").exists()


def test_gripper_and_stop(cfg_dir: Path) -> None:
    out = run(cfg_dir, "gripper", "open")
    assert "gripper: 99" in out
    out = run(cfg_dir, "stop")
    assert "stop sent" in out


def test_ik_and_xyz(cfg_dir: Path) -> None:
    out = run(cfg_dir, "ik", "0.1", "--", "-0.3", "0.05")
    assert out.count("=") == 6
    out = run(cfg_dir, "xyz", "0.1", "--", "-0.3", "0.05")
    assert "x=" in out
