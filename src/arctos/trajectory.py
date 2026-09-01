"""Follow a timed path, e.g. one planned by MoveIt.

Every point has joint angles (degrees, in the order of arm.names) and a time
from the start. The arm is commanded so that it reaches each point at its time.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from arctos.arm import Arm
from arctos.safety import Stopped

log = logging.getLogger(__name__)

MIN_DT = 0.02  # seconds, a step cannot be shorter than this


@dataclass
class Point:
    time: float  # seconds from the start of the path
    degs: list[float]  # joint angles in degrees, order as arm.names


def reorder(
    names_in: Sequence[str], values: Sequence[float], names_out: Sequence[str]
) -> list[float]:
    """Bring values from one joint order into another."""
    lookup = dict(zip(names_in, values, strict=True))
    missing = [n for n in names_out if n not in lookup]
    if missing:
        raise KeyError(f"joints missing in the path: {missing}")
    return [float(lookup[n]) for n in names_out]


def follow(
    arm: Arm,
    points: Sequence[Point],
    cancelled: Callable[[], bool] | None = None,
    on_point: Callable[[int, Point], None] | None = None,
) -> None:
    """Follow the path, blocks until the last point is reached.

    cancelled is polled while moving; when it returns True the arm is stopped
    and Stopped is raised.
    """
    if not points:
        return
    prev = arm.positions()
    prev_t = 0.0
    t0 = time.monotonic()
    log.info("path with %d points, %.1f s", len(points), points[-1].time)
    for i, p in enumerate(points):
        dt = p.time - prev_t
        arm.move(p.degs, duration=dt, wait=False, start=prev)
        while time.monotonic() - t0 < p.time:
            arm.safety.guard()
            if cancelled is not None and cancelled():
                arm.stop()
                raise Stopped("path cancelled")
            time.sleep(0.005)
        if on_point is not None:
            on_point(i, p)
        prev, prev_t = p.degs, p.time
    arm.wait(points[-1].degs, timeout=5.0)
