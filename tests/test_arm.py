"""Tests for the arm: conversions, limits, moving in the simulation."""

import pytest

from arctos.arm import Arm, Joint
from arctos.motor import Motor
from arctos.robot import Robot
from arctos.safety import LimitError, Safety, Stopped


def make_arm(coupling: bool = True) -> Arm:
    bus = object()  # not needed for pure conversions
    joints = [
        Joint("x", Motor(bus, 1), ratio=10, invert=False),  # type: ignore[arg-type]
        Joint("b", Motor(bus, 5), ratio=2, invert=True),  # type: ignore[arg-type]
        Joint("c", Motor(bus, 6), ratio=2, invert=False),  # type: ignore[arg-type]
    ]
    m = [[-0.5, 0.5], [0.5, 0.5]] if coupling else None
    return Arm(joints, Safety(), coupling=m)


def test_to_motor_ratio_and_invert() -> None:
    arm = make_arm(coupling=False)
    assert arm.to_motor([3, 4, 5]) == [30, -8, 10]
    assert arm.to_joint([30, -8, 10]) == [3, 4, 5]
