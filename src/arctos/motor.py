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

    # --- read ---

    def ping(self) -> bool:
        """Does the driver answer?"""
        return (
            self.bus.request(self.can_id, mks.query_status(), timeout=0.2) is not None
        )

    def status(self) -> int:
        rx = self._ask(mks.query_status())
        return mks.parse_status(rx)

    def counts(self) -> int:
        """Accumulated encoder position."""
        return mks.parse_encoder(self._ask(mks.read_encoder()))

    def position(self) -> float:
        """Motor angle in degrees."""
        return mks.counts_to_deg(self.counts())

    def speed(self) -> int:
        return mks.parse_speed(self._ask(mks.read_speed()))

    def io(self) -> dict[str, bool]:
        return mks.parse_io(self._ask(mks.read_io()))

    # --- move ---

    def enable(self, on: bool = True) -> None:
        self._ask(mks.enable(on))

    def stop(self) -> None:
        """Emergency stop, does not wait for a reply."""
        try:
            self.bus.send(self.can_id, mks.stop())
        except CanError as e:
            log.error("%s stop not sent: %s", self.name, e)

    def move_to(
        self,
        deg: float,
        rpm: float | None = None,
        acc: int | None = None,
        wait: bool = True,
        tolerance: float = 1.0,
    ) -> None:
        """Move to an absolute motor angle."""
        rpm = self._rpm(rpm)
        rx = self._ask(mks.move_abs(mks.deg_to_counts(deg), rpm, self._acc(acc)))
        self._check_run(rx)
        if wait:
            self.wait_for(deg, tolerance, self._eta(deg, rpm))

    def move_by(
        self,
        delta_deg: float,
        rpm: float | None = None,
        acc: int | None = None,
        wait: bool = True,
        tolerance: float = 1.0,
    ) -> None:
        """Turn by a relative angle."""
        target = self.position() + delta_deg
        self.move_to(target, rpm, acc, wait, tolerance)

    def run(self, rpm: float, acc: int | None = None) -> None:
        """Run continuously, sign = direction, 0 = stop."""
        rpm = max(-self.max_rpm, min(self.max_rpm, rpm))
        self._ask(mks.speed_mode(rpm, self._acc(acc)))

    def wait_for(
        self, deg: float, tolerance: float = 1.0, timeout: float = 30.0
    ) -> None:
        """Block until the encoder is at the target."""
        deadline = time.monotonic() + timeout
        while True:
            pos = self.position()
            if abs(pos - deg) <= tolerance:
                return
            if time.monotonic() > deadline:
                raise MotorError(
                    f"{self.name} did not arrive: at {pos:.1f}, wanted {deg:.1f}"
                )
            time.sleep(0.02)

    # --- settings ---

    def home(self, timeout: float = 60.0) -> None:
        """Homing run to the limit switch, the parameters are stored in the driver."""
        rx = self._ask(mks.go_home())
        if mks.parse_status(rx) == 0:
            raise MotorError(f"{self.name} refused to home")
        deadline = time.monotonic() + timeout
        time.sleep(0.2)
        while self.status() in (2, 3, 4, 5):  # still moving, 5 = homing in progress
            if time.monotonic() > deadline:
                raise MotorError(f"{self.name} homing takes too long")
            time.sleep(0.1)

    def set_zero(self) -> None:
        """The current position becomes 0."""
        self._ask(mks.set_zero())

    def set_current(self, ma: int) -> None:
        self._ask(mks.set_current(ma))

    def set_work_mode(self, mode: int = mks.WORK_MODE_VFOC) -> None:
        self._ask(mks.set_work_mode(mode))

    # --- internal ---

    def _ask(self, data: list[int]) -> list[int]:
        rx = self.bus.request(self.can_id, data)
        if rx is None:
            raise MotorError(f"{self.name} (id {self.can_id}) does not answer")
        return rx

    def _rpm(self, rpm: float | None) -> float:
        value = self.max_rpm if rpm is None else abs(rpm)
        return max(1.0, min(float(self.max_rpm), value))

    def _acc(self, acc: int | None) -> int:
        return self.acc if acc is None else acc

    def _eta(self, deg: float, rpm: float) -> float:
        """Generous time estimate used as the wait timeout."""
        distance = abs(deg - self.position())
        seconds = distance / (rpm * 6.0)  # rpm * 6 = degrees per second
        return 3.0 + 2.0 * seconds

    @staticmethod
    def _check_run(rx: list[int]) -> None:
        status = mks.parse_status(rx)
        if status == mks.RUN_FAIL:
            raise MotorError("move refused (motor disabled or locked?)")
        if status == mks.RUN_END_LIMIT:
            log.warning("limit switch reached")
