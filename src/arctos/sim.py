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

    def _tick(self) -> None:
        """Advance the position the way the motor is currently turning."""
        now = time.monotonic()
        dt = (now - self._t) * self.speedup
        self._t = now
        if self.free_run:
            self.counts += self.free_run * mks.ENCODER_PER_TURN / 60.0 * dt
            return
        step = self.rpm * mks.ENCODER_PER_TURN / 60.0 * dt
        diff = self.target - self.counts
        if abs(diff) <= step:
            self.counts = self.target
        else:
            self.counts += step if diff > 0 else -step

    def _moving(self) -> bool:
        return bool(self.free_run) or abs(self.target - self.counts) > 0.5

    def _handle(self, d: list[int]) -> list[int] | None:  # noqa: PLR0911
        cmd = d[0]
        if cmd == mks.READ_ENCODER:
            return [cmd, *int(round(self.counts)).to_bytes(6, "big", signed=True)]
        if cmd == mks.READ_SPEED:
            rpm = self.free_run or (self.rpm if self._moving() else 0)
            return [cmd, *int(rpm).to_bytes(2, "big", signed=True)]
        if cmd == mks.READ_IO:
            b = (1 if self.inputs["in_1"] else 0) | (2 if self.inputs["in_2"] else 0)
            return [cmd, b]
        if cmd == mks.QUERY_STATUS:
            if self.homing and not self._moving():
                self.homing = False
            return [cmd, 5 if self.homing else (4 if self._moving() else 1)]
        if cmd == mks.ENABLE:
            self.enabled = bool(d[1])
            return [cmd, 1]
        if cmd == mks.STOP:
            self.target = self.counts
            self.free_run = 0.0
            return [cmd, 1]
        if cmd in (mks.MOVE_ABS, mks.MOVE_REL):
            if not self.enabled:
                return [cmd, mks.RUN_FAIL]
            rpm = (d[1] << 8) | d[2]
            pos = int.from_bytes(bytes(d[4:7]), "big", signed=True)
            self.rpm = float(rpm)
            self.free_run = 0.0
            self.target = float(pos) if cmd == mks.MOVE_ABS else self.counts + pos
            return [cmd, mks.RUN_STARTING]
        if cmd == mks.SPEED_MODE:
            rpm = ((d[1] & 0x0F) << 8) | d[2]
            self.free_run = -float(rpm) if d[1] & 0x80 else float(rpm)
            self.target = self.counts
            return [cmd, 1]
        if cmd == mks.SET_ZERO:
            self.counts = 0.0
            self.target = 0.0
            return [cmd, 1]
        if cmd == mks.GO_HOME:
            self.target = 0.0
            self.rpm = 200.0
            self.homing = True
            return [cmd, 1]
        if cmd in (
            mks.SET_CURRENT,
            mks.SET_WORK_MODE,
            mks.SET_HOME_PARAMS,
            mks.SET_LIMIT_REMAP,
            mks.SET_MICROSTEP,
        ):
            return [cmd, 1]
        return None


class FakeGripper(threading.Thread):
    """The gripper board never answers, it only remembers the last position."""

    def __init__(self, can_id: int = 7, channel: str = SIM_CHANNEL) -> None:
        super().__init__(daemon=True, name="fake-gripper")
        self.can_id = can_id
        self.value = 0
        self._bus = can.Bus(interface="virtual", channel=channel)
        self._quit = threading.Event()

    def stop(self) -> None:
        self._quit.set()

    def run(self) -> None:
        while not self._quit.is_set():
            msg = self._bus.recv(timeout=0.05)
            if msg is not None and msg.arbitration_id == self.can_id and len(msg.data):
                self.value = msg.data[0]
                log.info("sim gripper: %d", self.value)
        self._bus.shutdown()
