"""Gripper: an Arduino Nano with a servo that listens on its own CAN id.

One byte = servo position, no crc, no reply. According to the Arctos docs
0x63 (99) is open and 0x00 is closed; check on your gripper and put the
values into the config.
"""

from __future__ import annotations

import logging
import time

from arctos.can_bus import CanBus

log = logging.getLogger(__name__)


class Gripper:
    def __init__(
        self,
        bus: CanBus,
        can_id: int = 7,
        open_value: int = 99,
        close_value: int = 0,
        settle: float = 1.0,
    ) -> None:
        self.bus = bus
        self.can_id = can_id
        self.open_value = open_value
        self.close_value = close_value
        self.settle = settle
        self.value: int | None = None

    def set(self, value: int, wait: bool = True) -> None:
        """Send a servo position from 0 to 255."""
        value = max(0, min(255, int(value)))
        self.bus.send(self.can_id, [value], with_crc=False)
        self.value = value
        log.info("gripper -> %d", value)
        if wait:
            time.sleep(self.settle)

    def open(self, wait: bool = True) -> None:
        self.set(self.open_value, wait)

    def close(self, wait: bool = True) -> None:
        self.set(self.close_value, wait)

    @property
    def is_open(self) -> bool | None:
        if self.value is None:
            return None
        return self.value == self.open_value
