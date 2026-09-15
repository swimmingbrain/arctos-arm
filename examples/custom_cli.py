"""Build your own command line on top of the arctos commands.

All the generic commands (status, move, home, teach, ...) are added with one
call, then you add the commands of your project next to them.

python examples/custom_cli.py --sim status
python examples/custom_cli.py --sim wave
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from arctos import cli, robot

app = typer.Typer(help="my robot cell", no_args_is_help=True)
opts = cli.Options()


@app.callback()
def main(
    config: Path | None = typer.Option(None, "--config", "-c"),
    sim: bool = typer.Option(False, "--sim"),
) -> None:
    opts.config, opts.sim = config, sim
    cli.configure_logging(logging.INFO)


def connect() -> robot.Robot:
    return robot.build(opts.config, sim=opts.sim, speedup=20.0 if opts.sim else 1.0)


cli.add_commands(app, connect)


@app.command()
def wave(times: int = 3) -> None:
    """Wave with the wrist."""
    with connect() as r:
        for _ in range(times):
            r.arm.move({"b": 30})
            r.arm.move({"b": -30})
        r.arm.move({"b": 0})


if __name__ == "__main__":
    app()
