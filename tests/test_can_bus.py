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
