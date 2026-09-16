"""Tests for the simulation itself: gripper, id discovery."""

import time

from arctos import sim
from arctos.robot import Robot


def test_gripper_reaches_sim(sim_robot: Robot) -> None:
    sim_robot.gripper.settle = 0.05
    sim_robot.gripper.close()
    time.sleep(0.1)
    assert sim_robot.sim is not None
    assert sim_robot.sim.gripper.value == sim_robot.gripper.close_value
    sim_robot.gripper.open()
    time.sleep(0.1)
    assert sim_robot.sim.gripper.value == sim_robot.gripper.open_value
    assert sim_robot.gripper.is_open


def test_can_ids_walks_the_config() -> None:
    cfg = {
        "joints": [{"can_id": 1}, {"can_id": 2}],
        "gripper": {"can_id": 7},
        "extra": {"nested": [{"can_id": 12}], "can_id": "not a number"},
    }
    assert sim.can_ids(cfg) == [1, 2, 7, 12]


def test_simulation_skips_gripper_id(sim_robot: Robot) -> None:
    assert sim_robot.sim is not None
    assert sorted(sim_robot.sim.drivers) == [1, 2, 3, 4, 5, 6]
    assert sim_robot.sim.gripper.can_id == 7
