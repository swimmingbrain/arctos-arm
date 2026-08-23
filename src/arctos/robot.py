"""Build the robot from the config: bus, arm, gripper, kinematics, simulation.

with robot.build(sim=True) as r:
    r.arm.move_joint("x", 30)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from arctos import config
from arctos.arm import Arm, Joint
from arctos.can_bus import CanBus
from arctos.gripper import Gripper
from arctos.kinematics import Kinematics
from arctos.motor import Motor
from arctos.safety import Safety
from arctos.sim import Simulation

log = logging.getLogger(__name__)

R = TypeVar("R", bound="Robot")


@dataclass
class Robot:
    """Everything that hangs on the bus. Subclass it to add your own devices."""

    settings: config.Settings
    bus: CanBus
    arm: Arm
    gripper: Gripper
    safety: Safety
    kin: Kinematics
    sim: Simulation | None = None

    def __enter__(self: R) -> R:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self.bus.close()
        if self.sim is not None:
            self.sim.stop()

    def stop(self) -> None:
        """Stop everything, call clear() before moving again."""
        self.safety.request_stop("stop")

    def clear(self) -> None:
        self.safety.clear()
