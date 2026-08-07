"""Send and receive on the CAN bus (python-can).

Real hardware: a CANable v2 over slcan (USB serial, /dev/ttyACM0) or socketcan (can0).
Simulation: interface "virtual", the fake drivers from sim.py answer.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import can

from arctos import mks

log = logging.getLogger(__name__)

SIM_CHANNEL = "arctos-sim"


class CanError(Exception):
    """Something on the bus went wrong."""


class CanBus:
    """One bus for all motors, created by robot.build()."""

    def __init__(
        self,
        interface: str = "slcan",
        channel: str = "/dev/ttyACM0",
        bitrate: int = 500000,
        timeout: float = 0.5,
        send_gap: float = 0.001,
    ) -> None:
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.timeout = timeout
        self.send_gap = send_gap
        self._bus: Any = None
        self._lock = threading.RLock()
        self._last_send = 0.0

    @classmethod
    def from_config(cls, cfg: dict[str, Any], sim: bool = False) -> CanBus:
        if sim:
            return cls(interface="virtual", channel=SIM_CHANNEL)
        return cls(
            interface=str(cfg.get("interface", "slcan")),
            channel=str(cfg.get("channel", "/dev/ttyACM0")),
            bitrate=int(cfg.get("bitrate", 500000)),
            timeout=float(cfg.get("timeout", 0.5)),
            send_gap=float(cfg.get("send_gap", 0.001)),
        )

    @property
    def is_open(self) -> bool:
        return self._bus is not None

    def open(self) -> CanBus:
        if self._bus is not None:
            return self
        kwargs: dict[str, Any] = {"interface": self.interface, "channel": self.channel}
        if self.interface != "virtual":
            kwargs["bitrate"] = self.bitrate
        try:
            self._bus = can.Bus(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise CanError(
                f"cannot open can {self.interface} {self.channel}: {e}"
            ) from e
        log.info("can open: %s %s", self.interface, self.channel)
        return self

    def close(self) -> None:
        if self._bus is None:
            return
        self._bus.shutdown()
        self._bus = None
        log.info("can closed")

    def __enter__(self) -> CanBus:
        return self.open()

    def __exit__(self, *exc: object) -> None:
        self.close()

    def send(self, can_id: int, data: list[int], with_crc: bool = True) -> None:
        """Send one frame, the crc is appended unless with_crc is False."""
        if self._bus is None:
            raise CanError("bus is not open")
        payload = mks.frame(can_id, data) if with_crc else list(data)
        msg = can.Message(arbitration_id=can_id, data=payload, is_extended_id=False)
        with self._lock:
            gap = self.send_gap - (time.monotonic() - self._last_send)
            if gap > 0:
                time.sleep(gap)
            self._bus.send(msg)
            self._last_send = time.monotonic()

    def recv(self, timeout: float | None = None) -> tuple[int, list[int]] | None:
        """Next frame or None on timeout."""
        if self._bus is None:
            raise CanError("bus is not open")
        msg = self._bus.recv(self.timeout if timeout is None else timeout)
        if msg is None:
            return None
        return int(msg.arbitration_id), list(msg.data)

    def flush(self) -> None:
        """Throw away old replies."""
        while self.recv(timeout=0.0) is not None:
            pass
