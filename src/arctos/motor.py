"""One MKS driver = one motor. Angles are motor degrees, before the gearbox."""

from __future__ import annotations

import logging
import time

from arctos import mks
from arctos.can_bus import CanBus, CanError

log = logging.getLogger(__name__)


class MotorError(Exception):
    """Motor does not answer or reports an error."""


class Motor:
    def __init__(
        self,
        bus: CanBus,
        can_id: int,
        name: str = "",
        acc: int = 60,
        max_rpm: int = 1500,
    ) -> None:
        self.bus = bus
        self.can_id = can_id
        self.name = name or f"motor{can_id}"
        self.acc = acc
        self.max_rpm = max_rpm

    def __repr__(self) -> str:
        return f"Motor({self.name}, id={self.can_id})"
