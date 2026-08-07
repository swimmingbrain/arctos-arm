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
