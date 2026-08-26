"""Command line: one command per task.

arctos --sim status
arctos move y 30
arctos joints 0 45 -30 0 -60 0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import typer

from arctos import __version__, config, robot
from arctos.robot import Robot

# so that negative numbers like -30 are not read as options
NUMBERS = {"ignore_unknown_options": True}
log = logging.getLogger(__name__)


@dataclass
class Options:
    config: Path | None = None
    sim: bool = False
    speedup: float = 1.0


opts = Options()


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def connect() -> Robot:
    return robot.build(opts.config, sim=opts.sim, speedup=opts.speedup)


def show(names: list[str], degs: list[float]) -> None:
    typer.echo("  ".join(f"{n}={d:7.2f}" for n, d in zip(names, degs, strict=True)))


app = typer.Typer(help="Control an Arctos robot arm over CAN.", no_args_is_help=True)


@app.callback()
def main(
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help="robot.yaml or its folder"
    ),
    sim: bool = typer.Option(False, "--sim", help="no robot, virtual motors"),
    speedup: float = typer.Option(1.0, help="run the simulation faster"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="show every can frame"),
) -> None:
    opts.config, opts.sim, opts.speedup = config_path, sim, speedup
    configure_logging(logging.DEBUG if verbose else logging.INFO)


# --- read ---


@app.command()
def status() -> None:
    """Show joint angles and tool position."""
    with connect() as r:
        degs = r.arm.positions()
        show(r.arm.names, degs)
        x, y, z = r.kin.position(degs)
        typer.echo(
            f"tool: x={x:.3f} y={y:.3f} z={z:.3f} m, yaw={r.kin.yaw(degs):.1f}"
        )


@app.command()
def scan() -> None:
    """Which motors answer on the bus?"""
    with connect() as r:
        for name, ok in r.arm.ping().items():
            typer.echo(f"{name}: {'ok' if ok else 'no reply'}")
