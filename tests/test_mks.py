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


def test_deg_counts() -> None:
    assert mks.deg_to_counts(360) == 16384
    assert mks.deg_to_counts(-90) == -4096
    assert mks.counts_to_deg(8192) == 180.0


def test_move_abs_layout() -> None:
    data = mks.move_abs(mks.deg_to_counts(90), 600, 50)
    assert data == [0xF5, 0x02, 0x58, 50, 0x00, 0x10, 0x00]
    assert len(mks.frame(3, data)) == 8


def test_speed_mode_direction_bit() -> None:
    fwd = mks.speed_mode(300, 10)
    back = mks.speed_mode(-300, 10)
    assert fwd == [0xF6, 0x01, 0x2C, 10]
    assert back == [0xF6, 0x81, 0x2C, 10]
    assert mks.speed_mode(9999, 300) == [0xF6, 0x0B, 0xB8, 255]
