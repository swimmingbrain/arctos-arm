"""Stop everything, check limits, read an emergency stop input.

The real emergency stop has to cut the motor power in hardware. This is only
the software side: a stop flag that aborts every motion loop, plus the stop
command that goes out to all motors.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

log = logging.getLogger(__name__)


class Stopped(Exception):
    """Motion aborted (stop button, emergency stop)."""


class LimitError(Exception):
    """Value outside the allowed range."""


class Safety:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self.reason = ""
        self.on_stop: list[Callable[[], None]] = []  # e.g. arm.stop

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def request_stop(self, reason: str = "stop") -> None:
        """Stop everything, called from a UI, the CLI or the e-stop input."""
        self.reason = reason
        self._stop.set()
        log.warning("stop: %s", reason)
        for fn in self.on_stop:
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                log.error("stop action failed: %s", e)

    def clear(self) -> None:
        self._stop.clear()
        self.reason = ""

    def guard(self) -> None:
        """Call inside loops, raises Stopped once a stop was requested."""
        if self._stop.is_set():
            raise Stopped(self.reason or "stop")

    @staticmethod
    def check_range(name: str, value: float, low: float, high: float) -> None:
        if not low <= value <= high:
            raise LimitError(f"{name}: {value:.1f} is not within {low} to {high}")
