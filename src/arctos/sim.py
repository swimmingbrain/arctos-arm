"""Virtual MKS drivers so that everything runs without a robot (arctos --sim ...).

Every fake driver hangs on the virtual bus, answers like a real MKS and moves
its position with the commanded speed. The gripper just swallows its byte.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import can

from arctos import mks
from arctos.can_bus import SIM_CHANNEL

log = logging.getLogger(__name__)


class FakeDriver(threading.Thread):
    """One simulated MKS driver."""

    def __init__(
        self, can_id: int, channel: str = SIM_CHANNEL, speedup: float = 1.0
    ) -> None:
        super().__init__(daemon=True, name=f"fake-mks-{can_id}")
        self.can_id = can_id
        self.speedup = speedup  # > 1 runs faster than real time, for tests
        self.counts = 0.0
        self.target = 0.0
        self.rpm = 0.0
        self.free_run = 0.0  # rpm in speed mode
        self.enabled = True
        self.homing = False
        self.inputs = {"in_1": False, "in_2": False}
        self._bus = can.Bus(interface="virtual", channel=channel)
        self._quit = threading.Event()
        self._t = time.monotonic()

    def stop(self) -> None:
        self._quit.set()

    def run(self) -> None:
        while not self._quit.is_set():
            msg = self._bus.recv(timeout=0.01)
            self._tick()
            if msg is None or msg.arbitration_id != self.can_id:
                continue
            data = list(msg.data)
            if not mks.check(self.can_id, data):
                continue
            reply = self._handle(data[:-1])
            if reply is not None:
                self._bus.send(
                    can.Message(
                        arbitration_id=self.can_id,
                        data=mks.frame(self.can_id, reply),
                        is_extended_id=False,
                    )
                )
        self._bus.shutdown()
