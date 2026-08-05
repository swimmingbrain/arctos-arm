"""Tests for the MKS protocol (bytes only, no bus)."""

import pytest

from arctos import mks


def test_crc_like_manual() -> None:
    # example from the manual: id 1, command f3 01 -> crc f5
    assert mks.crc(1, [0xF3, 0x01]) == 0xF5
    assert mks.frame(1, [0xF3, 0x01]) == [0xF3, 0x01, 0xF5]
    assert mks.check(1, [0xF3, 0x01, 0xF5])
    assert not mks.check(1, [0xF3, 0x01, 0x00])
