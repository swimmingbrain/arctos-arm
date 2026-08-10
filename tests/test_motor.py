"""Tests for a single motor against the simulated driver."""

import time
from collections.abc import Iterator

import pytest

from arctos.can_bus import CanBus
from arctos.motor import Motor, MotorError
from arctos.sim import FakeDriver


@pytest.fixture
def motor() -> Iterator[Motor]:
    driver = FakeDriver(2, channel="test-motor", speedup=200.0)
    driver.start()
    bus = CanBus(interface="virtual", channel="test-motor", timeout=0.3).open()
    try:
        yield Motor(bus, 2, "test", acc=60, max_rpm=1500)
    finally:
        bus.close()
        driver.stop()
        driver.join(timeout=1.0)


def test_ping_and_position(motor: Motor) -> None:
    assert motor.ping()
    assert not Motor(motor.bus, 11).ping()
    assert abs(motor.position()) < 0.01
    assert motor.status() == 1


def test_move_to_and_by(motor: Motor) -> None:
    motor.move_to(90, rpm=300)
    assert abs(motor.position() - 90) <= 1.0
    motor.move_by(-30, rpm=300)
    assert abs(motor.position() - 60) <= 1.0


def test_move_refused_when_disabled(motor: Motor) -> None:
    motor.enable(False)
    with pytest.raises(MotorError):
        motor.move_to(10)
    motor.enable(True)
    motor.move_to(10, rpm=300)


def test_speed_mode_and_stop(motor: Motor) -> None:
    motor.run(120)
    time.sleep(0.05)
    assert motor.position() > 0
    motor.stop()
    time.sleep(0.05)
    a = motor.position()
    time.sleep(0.05)
    assert abs(motor.position() - a) < 0.5


def test_home_and_zero(motor: Motor) -> None:
    motor.move_to(45, rpm=300)
    motor.home()
    assert abs(motor.position()) < 1.0
    motor.move_to(20, rpm=300)
    motor.set_zero()
    assert abs(motor.position()) < 0.01
