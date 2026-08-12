"""The whole arm: joints, gear ratios, wrist coupling, limits, coordinated moves.

Joint angles are always degrees in the direction of the URDF (see kinematics.py).
Everything on the motor side (ratio, direction, differential) happens here.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from arctos.motor import Motor, MotorError
from arctos.safety import Safety

log = logging.getLogger(__name__)


@dataclass
class Joint:
    name: str
    motor: Motor
    ratio: float = 1.0  # motor revolutions per joint revolution
    invert: bool = False
    min_deg: float = -180.0
    max_deg: float = 180.0
    speed: float = 30.0  # degrees per second at the joint
    acc: int = 60
    offset: float = 0.0  # joint angle when the driver reports 0 (after homing)


class Arm:
    def __init__(
        self,
        joints: Sequence[Joint],
        safety: Safety | None = None,
        coupling: Sequence[Sequence[float]] | None = None,
        tolerance: float = 0.5,
        max_rpm: float = 1500.0,
        min_rpm: float = 5.0,
    ) -> None:
        self.joints = list(joints)
        self.names = [j.name for j in self.joints]
        self.safety = safety or Safety()
        self.coupling = [list(row) for row in coupling] if coupling else None
        self.tolerance = tolerance
        self.max_rpm = max_rpm
        self.min_rpm = min_rpm
        for j in self.joints:
            j.motor.acc = j.acc
        self.safety.on_stop.append(self.stop)

    def __getitem__(self, name: str) -> Joint:
        for j in self.joints:
            if j.name == name:
                return j
        raise KeyError(f"no joint '{name}', known: {self.names}")

    def index(self, name: str) -> int:
        return self.names.index(name)

    # --- joint <-> motor conversion ---

    def to_motor(self, joint_degs: Sequence[float]) -> list[float]:
        """Joint angles -> motor angles (offset, coupling, ratio, direction)."""
        degs = [d - j.offset for j, d in zip(self.joints, joint_degs, strict=True)]
        if self.coupling and len(degs) >= 2:
            m = self.coupling
            b, c = degs[-2], degs[-1]
            degs[-2] = m[0][0] * b + m[0][1] * c
            degs[-1] = m[1][0] * b + m[1][1] * c
        return [
            (-d if j.invert else d) * j.ratio
            for j, d in zip(self.joints, degs, strict=True)
        ]

    def to_joint(self, motor_degs: Sequence[float]) -> list[float]:
        """Motor angles -> joint angles, inverse of to_motor."""
        degs = [
            (-m if j.invert else m) / j.ratio
            for j, m in zip(self.joints, motor_degs, strict=True)
        ]
        if self.coupling and len(degs) >= 2:
            m = self.coupling
            det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
            mb, mc = degs[-2], degs[-1]
            degs[-2] = (m[1][1] * mb - m[0][1] * mc) / det
            degs[-1] = (-m[1][0] * mb + m[0][0] * mc) / det
        return [d + j.offset for j, d in zip(self.joints, degs, strict=True)]

    # --- read ---

    def positions(self) -> list[float]:
        """All joint angles in degrees."""
        return self.to_joint([j.motor.position() for j in self.joints])

    def position(self, name: str) -> float:
        return self.positions()[self.index(name)]

    def ping(self) -> dict[str, bool]:
        return {j.name: j.motor.ping() for j in self.joints}

    # --- move ---

    def enable(self, on: bool = True) -> None:
        for j in self.joints:
            j.motor.enable(on)

    def stop(self) -> None:
        """Emergency stop to all motors."""
        for j in self.joints:
            j.motor.stop()

    def move(
        self,
        target: Sequence[float] | Mapping[str, float],
        speed: float | None = None,
        wait: bool = True,
    ) -> None:
        """Move joints so that all of them arrive at the same time.

        target: list with every angle, or a dict {name: angle} for some joints.
        speed: degrees per second for all joints, default is the per-joint value.
        """
        self.safety.guard()
        now = self.positions()
        goal = self._goal(now, target)
        for j, g in zip(self.joints, goal, strict=True):
            self.safety.check_range(j.name, g, j.min_deg, j.max_deg)

        motor_now = self.to_motor(now)
        motor_goal = self.to_motor(goal)
        seconds = self._duration(now, goal, motor_now, motor_goal, speed)
        if seconds <= 0:
            return
        for j, a, b in zip(self.joints, motor_now, motor_goal, strict=True):
            dist = abs(b - a)
            if dist < 1e-6:
                continue
            rpm = min(self.max_rpm, dist / seconds / 6.0)
            j.motor.move_to(b, rpm, wait=False)
        log.info("moving to %s in about %.1f s", [round(g, 1) for g in goal], seconds)
        if wait:
            self.wait(goal, timeout=3.0 + 2.0 * seconds)
