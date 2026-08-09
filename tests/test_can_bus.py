"""Tests for the bus wrapper, using a single fake driver on the virtual bus."""

from collections.abc import Iterator

import pytest

from arctos import mks
from arctos.can_bus import CanBus, CanError
from arctos.sim import FakeDriver


@pytest.fixture
def bus() -> Iterator[CanBus]:
    driver = FakeDriver(3, channel="test-bus")
    driver.start()
    b = CanBus(interface="virtual", channel="test-bus", timeout=0.3).open()
    try:
        yield b
    finally:
        b.close()
        driver.stop()
        driver.join(timeout=1.0)


def test_request_gets_reply(bus: CanBus) -> None:
    rx = bus.request(3, mks.query_status())
    assert rx is not None
    assert rx[0] == mks.QUERY_STATUS
    assert mks.check(3, rx)


def test_request_timeout_returns_none(bus: CanBus) -> None:
    assert bus.request(9, mks.query_status(), timeout=0.1) is None


def test_send_needs_open_bus() -> None:
    b = CanBus(interface="virtual", channel="closed")
    assert not b.is_open
    with pytest.raises(CanError):
        b.send(1, mks.stop())
    with pytest.raises(CanError):
        b.recv()


def test_open_twice_is_fine() -> None:
    with CanBus(interface="virtual", channel="twice") as b:
        assert b.open() is b
        assert b.is_open
    assert not b.is_open
