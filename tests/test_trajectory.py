"""Following paths in the simulation."""

import time

import pytest

from arctos import trajectory
from arctos.robot import Robot
from arctos.safety import Stopped


def test_reorder() -> None:
    out = trajectory.reorder(["b", "a"], [2.0, 1.0], ["a", "b"])
    assert out == [1.0, 2.0]
    with pytest.raises(KeyError):
        trajectory.reorder(["a"], [1.0], ["a", "b"])


def ramp(n: int, seconds: float) -> list[trajectory.Point]:
    return [
        trajectory.Point(
            time=seconds * i / n,
            degs=[20 * i / n, 10 * i / n, 0, 0, -30 * i / n, 0],
        )
        for i in range(1, n + 1)
    ]


def test_follow_arrives_on_time(sim_robot: Robot) -> None:
    arm = sim_robot.arm
    seen: list[int] = []
    t0 = time.monotonic()
    trajectory.follow(arm, ramp(5, 1.0), on_point=lambda i, p: seen.append(i))
    elapsed = time.monotonic() - t0
    assert seen == [0, 1, 2, 3, 4]
    assert 0.9 <= elapsed <= 4.0
    for got, want in zip(arm.positions(), [20, 10, 0, 0, -30, 0], strict=True):
        assert abs(got - want) <= arm.tolerance
