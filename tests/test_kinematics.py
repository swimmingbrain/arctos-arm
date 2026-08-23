"""Tests for the kinematics with the arctos numbers from the default config."""

import math

import numpy as np
import pytest

from arctos import config
from arctos.kinematics import IkError, Kinematics


@pytest.fixture
def kin() -> Kinematics:
    s = config.load(config.DEFAULT_ROBOT)
    k = s.section("kinematics")
    return Kinematics(k["links"], k["tool"], k["tool_axis"])


def test_fk_zero_pose(kin: Kinematics) -> None:
    x, y, z = kin.position([0] * 6)
    assert abs(x) < 1e-6
    assert abs(y - (-0.4126)) < 0.002
    assert abs(z - 0.5686) < 0.002


def test_fk_base_rotation_moves_in_circle(kin: Kinematics) -> None:
    p0 = np.array(kin.position([0, 30, -20, 0, -60, 0]))
    p1 = np.array(kin.position([90, 30, -20, 0, -60, 0]))
    assert abs(np.hypot(*p0[:2]) - np.hypot(*p1[:2])) < 1e-6
    assert abs(p0[2] - p1[2]) < 1e-6


def test_ik_hits_target_and_points_down(kin: Kinematics) -> None:
    target = (0.10, -0.30, 0.05)
    degs = kin.ik(target, seed=[0, 40, -30, 0, -80, 0])
    got = np.array(kin.position(degs))
    assert np.linalg.norm(got - np.array(target)) < 0.005
    frame = kin.frame(degs)
    down = frame[:3, :3] @ np.array(kin.tool_axis)
    assert down[2] < -0.98
