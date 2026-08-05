"""Tests for the MKS protocol (bytes only, no bus)."""

import pytest

from arctos import mks


def test_crc_like_manual() -> None:
    # example from the manual: id 1, command f3 01 -> crc f5
    assert mks.crc(1, [0xF3, 0x01]) == 0xF5
    assert mks.frame(1, [0xF3, 0x01]) == [0xF3, 0x01, 0xF5]
    assert mks.check(1, [0xF3, 0x01, 0xF5])
    assert not mks.check(1, [0xF3, 0x01, 0x00])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, [0, 0, 0]),
        (1, [0, 0, 1]),
        (-1, [0xFF, 0xFF, 0xFF]),
        (-8388608, [0x80, 0, 0]),
    ],
)
def test_int24(value: int, expected: list[int]) -> None:
    assert mks.to_int24(value) == expected


def test_int48_roundtrip() -> None:
    for v in (0, 16384, -16384, 123456789, -987654321):
        data = list(v.to_bytes(6, "big", signed=True))
        assert mks.from_int48(data) == v
