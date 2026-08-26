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


@app.command(name="config")
def show_config() -> None:
    """Show which configuration is in use."""
    with connect() as r:
        s = r.settings
        typer.echo(f"robot: {s.source}")
        typer.echo(f"poses and offsets: {s.dir}")
        for j in r.arm.joints:
            typer.echo(
                f"{j.name}: id {j.motor.can_id}, ratio {j.ratio}, "
                f"{j.min_deg} to {j.max_deg} deg, offset {j.offset}"
            )


# --- single motors and joints ---


@app.command()
def enable(on: bool = typer.Argument(True)) -> None:
    """Enable (true) or release (false) all motors."""
    with connect() as r:
        r.arm.enable(on)
        typer.echo("motors on" if on else "motors off")


@app.command()
def move(joint: str, deg: float, speed: float | None = None) -> None:
    """Move one joint to an angle, e.g. move y 30."""
    with connect() as r:
        r.arm.move_joint(joint, deg, speed)
        show(r.arm.names, r.arm.positions())


@app.command()
def jog(joint: str, delta: float, speed: float | None = None) -> None:
    """Turn one joint by a relative angle, e.g. jog x -5."""
    with connect() as r:
        r.arm.jog(joint, delta, speed)
        show(r.arm.names, r.arm.positions())


@app.command()
def joints(deg: list[float], speed: float | None = None) -> None:
    """Move all joints at once: joints x y z a b c."""
    with connect() as r:
        r.arm.move(deg, speed)
        show(r.arm.names, r.arm.positions())


@app.command()
def motor(can_id: int, deg: float, rpm: float = 100, acc: int = 60) -> None:
    """Drive one motor in motor degrees, without gearbox or limits (careful)."""
    from arctos.motor import Motor

    with connect() as r:
        m = Motor(r.bus, can_id, f"id{can_id}", acc=acc)
        m.move_to(deg, rpm)
        typer.echo(f"motor {can_id}: {m.position():.1f} deg")


@app.command()
def home(joint: list[str] | None = typer.Argument(None)) -> None:
    """Homing run, all joints or only the named ones."""
    with connect() as r:
        r.arm.home(joint or None)
        show(r.arm.names, r.arm.positions())


@app.command()
def zero(joint: list[str] | None = typer.Argument(None)) -> None:
    """Make the current position 0 inside the drivers."""
    with connect() as r:
        r.arm.set_zero(joint or None)
        typer.echo("zero set")


@app.command()
def calibrate(pose: str | None = None) -> None:
    """The current position is the zero pose (or the named pose), store offsets."""
    with connect() as r:
        offsets = r.calibrate(pose)
        typer.echo(f"offsets saved: {offsets}")
        show(r.arm.names, r.arm.positions())


@app.command()
def stop() -> None:
    """Emergency stop to all motors."""
    with connect() as r:
        r.arm.stop()
        typer.echo("stop sent")


@app.command()
def setup() -> None:
    """Write current and work mode from the config into the drivers."""
    with connect() as r:
        r.apply_motor_settings()
        typer.echo("drivers configured")


# --- gripper ---


@app.command()
def gripper(what: str) -> None:
    """Gripper: open, close or a number from 0 to 255."""
    with connect() as r:
        if what == "open":
            r.gripper.open()
        elif what == "close":
            r.gripper.close()
        else:
            r.gripper.set(int(what))
        typer.echo(f"gripper: {r.gripper.value}")


# --- poses and cartesian ---


@app.command()
def poses() -> None:
    """List the taught poses."""
    with connect() as r:
        for name, degs in r.settings.poses.items():
            typer.echo(f"{name:12s} {degs}")


@app.command()
def pose(name: str, speed: float | None = None) -> None:
    """Move to a taught pose, e.g. pose home."""
    with connect() as r:
        r.goto(name, speed)
        show(r.arm.names, r.arm.positions())


@app.command()
def teach(name: str) -> None:
    """Store the current position as a pose."""
    with connect() as r:
        degs = r.teach(name)
        show(r.arm.names, degs)
