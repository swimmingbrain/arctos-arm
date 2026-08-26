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
