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


def build(
    path: str | Path | None = None,
    sim: bool = False,
    speedup: float = 1.0,
) -> Robot:
    """Create everything and open the bus."""
    settings = config.load(path)
    cfg = settings.robot
    safety = Safety()

    simulation = None
    if sim:
        simulation = Simulation(cfg, speedup=speedup).start()
    bus = CanBus.from_config(settings.section("can"), sim=sim).open()

    motion = settings.section("motion")
    joints = []
    for raw in cfg.get("joints", []):
        motor = Motor(
            bus,
            int(raw["can_id"]),
            str(raw["name"]),
            acc=int(raw.get("acc", 60)),
            max_rpm=int(motion.get("max_rpm", 1500)),
        )
        joints.append(
            Joint(
                name=str(raw["name"]),
                motor=motor,
                ratio=float(raw.get("ratio", 1.0)),
                invert=bool(raw.get("invert", False)),
                offset=float(settings.offsets.get(str(raw["name"]), 0.0)),
                min_deg=float(raw.get("min", -180)),
                max_deg=float(raw.get("max", 180)),
                speed=float(raw.get("speed", 30)),
                acc=int(raw.get("acc", 60)),
            )
        )
    coupling_cfg = settings.section("coupling")
    coupling = (
        coupling_cfg.get("matrix") if coupling_cfg.get("enabled", False) else None
    )
    arm = Arm(
        joints,
        safety,
        coupling=coupling,
        tolerance=float(motion.get("tolerance", 0.5)),
        max_rpm=float(motion.get("max_rpm", 1500)),
        min_rpm=float(motion.get("min_rpm", 5)),
    )
