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


def test_coupling_roundtrip() -> None:
    arm = make_arm(coupling=True)
    motor = arm.to_motor([0, 20, 40])
    # motor_b = (c - b)/2 = 10, inverted and ratio 2 -> -20
    # motor_c = (b + c)/2 = 30, ratio 2 -> 60
    assert motor == [0, -20, 60]
    back = arm.to_joint(motor)
    assert [round(v, 9) for v in back] == [0, 20, 40]


def test_offset_roundtrip() -> None:
    arm = make_arm(coupling=True)
    arm["x"].offset = -55.0  # driver 0 = joint at -55 (home switch)
    assert arm.to_joint([0, 0, 0])[0] == -55.0
    assert arm.to_motor([-55.0, 0, 0])[0] == 0.0
    back = arm.to_joint(arm.to_motor([12.0, 20, 40]))
    assert [round(v, 9) for v in back] == [12.0, 20, 40]


def test_unknown_joint() -> None:
    arm = make_arm()
    with pytest.raises(KeyError):
        arm["q"]
    with pytest.raises(ValueError):
        arm._goal([0, 0, 0], [1, 2])


def test_sim_move_single_joint(sim_robot: Robot) -> None:
    arm = sim_robot.arm
    assert max(abs(p) for p in arm.positions()) < 0.01
    arm.move_joint("x", 30)
    assert abs(arm.position("x") - 30) <= arm.tolerance
    arm.jog("x", -10)
    assert abs(arm.position("x") - 20) <= arm.tolerance


def test_sim_move_all_joints(sim_robot: Robot) -> None:
    arm = sim_robot.arm
    target = [10, 20, -30, 40, -50, 60]
    arm.move(target)
    for got, want in zip(arm.positions(), target, strict=True):
        assert abs(got - want) <= arm.tolerance
    # moving b alone has to turn both wrist motors
    before = [j.motor.position() for j in arm.joints]
    arm.move({"b": 0})
    after = [j.motor.position() for j in arm.joints]
    assert before[4] != after[4] and before[5] != after[5]
    assert abs(arm.position("c") - 60) <= arm.tolerance


def test_sim_limits(sim_robot: Robot) -> None:
    with pytest.raises(LimitError):
        sim_robot.arm.move_joint("y", 200)
