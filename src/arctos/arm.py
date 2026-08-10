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
