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

    # --- poses ---

    def pose(self, name: str) -> list[float]:
        return self.settings.pose(name)

    def goto(self, name: str, speed: float | None = None) -> None:
        """Move to a taught pose."""
        self.arm.move(self.pose(name), speed)

    def teach(self, name: str) -> list[float]:
        """Store the current position under this name."""
        degs = self.arm.positions()
        self.settings.save_pose(name, degs)
        log.info("pose %s saved: %s", name, [round(d, 1) for d in degs])
        return degs

    # --- setup ---

    def apply_motor_settings(self) -> None:
        """Write current and work mode from the config into the drivers."""
        mode = int(self.settings.section("driver").get("work_mode", 5))
        for j, raw in zip(self.arm.joints, self.settings.robot["joints"], strict=True):
            if "current" in raw:
                j.motor.set_current(int(raw["current"]))
            j.motor.set_work_mode(mode)
            log.info("%s: current %s mA, mode %d", j.name, raw.get("current"), mode)

    def calibrate(self, pose_name: str | None = None) -> dict[str, float]:
        """Current position = zero pose (or the named pose), saved to offsets.yaml."""
        pose = self.pose(pose_name) if pose_name else None
        offsets = self.arm.calibrate(pose)
        self.settings.save_offsets(offsets)
        log.info("offsets saved: %s", offsets)
        return offsets
