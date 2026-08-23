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
