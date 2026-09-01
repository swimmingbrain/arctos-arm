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
