"""CAN protocol of the MKS SERVO42D / SERVO57D closed loop stepper drivers.

This module only builds and parses bytes. Sending happens in can_bus.py.
Reference: "MKS SERVO42&57D CAN User Manual" (github.com/makerbase-motor).

A frame is [command, data..., crc] with crc = (can_id + sum(bytes)) & 0xFF.
"""

from __future__ import annotations

ENCODER_PER_TURN = 16384  # 0x4000 encoder counts per motor revolution

# read commands
READ_ENCODER_CARRY = 0x30
READ_ENCODER = 0x31  # accumulated position, int48
READ_SPEED = 0x32  # rpm, int16
READ_IO = 0x34  # inputs IN_1, IN_2 and outputs
READ_ANGLE_ERROR = 0x39
READ_ENABLED = 0x3A
READ_HOME_STATUS = 0x3B
RELEASE_PROTECTION = 0x3D
READ_PROTECTION = 0x3E

# settings
CALIBRATE = 0x80
SET_WORK_MODE = 0x82  # 0 cr_open, 1 cr_close, 2 cr_vfoc, 3 sr_open, 4 sr_close, 5 sr_vfoc
SET_CURRENT = 0x83  # mA, uint16
SET_MICROSTEP = 0x84
SET_DIRECTION = 0x86
SET_CAN_ID = 0x8B
SET_RESPOND = 0x8C
SET_HOME_PARAMS = 0x90
GO_HOME = 0x91
SET_ZERO = 0x92
SET_LIMIT_REMAP = 0x9E  # second limit switch on the 42D (EN and DIR pins)

# motion
QUERY_STATUS = 0xF1  # 0 error, 1 stopped, 2 accelerating, 3 decelerating, 4 full speed, 5 homing
ENABLE = 0xF3
MOVE_REL = 0xF4  # relative, in encoder counts
MOVE_ABS = 0xF5  # absolute, in encoder counts
SPEED_MODE = 0xF6
STOP = 0xF7  # emergency stop

# status byte in the reply to a motion command
RUN_FAIL = 0
RUN_STARTING = 1
RUN_COMPLETE = 2
RUN_END_LIMIT = 3

WORK_MODE_VFOC = 2  # cr_vfoc: factory default, pulse/direction, CAN motion commands are ignored
WORK_MODE_SR_VFOC = 5  # sr_vfoc: serial (CAN) control, this is what the library needs
MAX_SPEED = 3000
MAX_ACC = 255


def crc(can_id: int, data: list[int]) -> int:
    """Checksum as defined in the manual."""
    return (can_id + sum(data)) & 0xFF


def frame(can_id: int, data: list[int]) -> list[int]:
    """Append the checksum."""
    return [*data, crc(can_id, data)]


def check(can_id: int, data: list[int]) -> bool:
    """Is the checksum of a reply correct?"""
    return len(data) >= 2 and crc(can_id, data[:-1]) == data[-1]


def to_int24(value: int) -> list[int]:
    """Signed 24 bit number, most significant byte first."""
    v = value & 0xFFFFFF
    return [(v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]


def to_uint16(value: int) -> list[int]:
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"value {value} does not fit in 16 bit")
    return [(value >> 8) & 0xFF, value & 0xFF]


def from_int48(data: list[int]) -> int:
    """Six bytes to a signed integer."""
    return int.from_bytes(bytes(data[:6]), "big", signed=True)


def deg_to_counts(deg: float) -> int:
    return round(deg * ENCODER_PER_TURN / 360.0)


def counts_to_deg(counts: int) -> float:
    return counts * 360.0 / ENCODER_PER_TURN


def clamp_speed(rpm: float) -> int:
    return max(0, min(MAX_SPEED, round(abs(rpm))))


def clamp_acc(acc: int) -> int:
    return max(0, min(MAX_ACC, int(acc)))


# --- build commands (without crc, frame() appends it) ---


def enable(on: bool = True) -> list[int]:
    return [ENABLE, 1 if on else 0]


def stop() -> list[int]:
    return [STOP]


def move_abs(counts: int, rpm: float, acc: int) -> list[int]:
    """Move to an absolute encoder position."""
    return [MOVE_ABS, *to_uint16(clamp_speed(rpm)), clamp_acc(acc), *to_int24(counts)]


def move_rel(counts: int, rpm: float, acc: int) -> list[int]:
    """Move by a number of encoder counts."""
    return [MOVE_REL, *to_uint16(clamp_speed(rpm)), clamp_acc(acc), *to_int24(counts)]


def speed_mode(rpm: float, acc: int) -> list[int]:
    """Run continuously, sign = direction, 0 = stop."""
    speed = clamp_speed(rpm)
    direction = 0x80 if rpm < 0 else 0x00
    return [SPEED_MODE, direction | ((speed >> 8) & 0x0F), speed & 0xFF, clamp_acc(acc)]


def read_encoder() -> list[int]:
    return [READ_ENCODER]


def read_speed() -> list[int]:
    return [READ_SPEED]


def read_io() -> list[int]:
    return [READ_IO]


def query_status() -> list[int]:
    return [QUERY_STATUS]


def go_home() -> list[int]:
    return [GO_HOME]


def set_zero() -> list[int]:
    return [SET_ZERO]


def set_current(ma: int) -> list[int]:
    return [SET_CURRENT, *to_uint16(ma)]


def set_work_mode(mode: int) -> list[int]:
    return [SET_WORK_MODE, mode]


def set_home_params(
    trigger_high: bool, ccw: bool, rpm: int, end_limit: bool, no_limit: bool
) -> list[int]:
    return [
        SET_HOME_PARAMS,
        1 if trigger_high else 0,
        1 if ccw else 0,
        *to_uint16(rpm),
        1 if end_limit else 0,
        1 if no_limit else 0,
    ]


def set_limit_remap(on: bool) -> list[int]:
    return [SET_LIMIT_REMAP, 1 if on else 0]


# --- parse replies ---


def parse_encoder(data: list[int]) -> int:
    """Reply to 0x31: [0x31, 6 bytes position, crc] -> encoder counts."""
    if len(data) < 7 or data[0] != READ_ENCODER:
        raise ValueError(f"not an encoder reply: {data}")
    return from_int48(data[1:7])


def parse_speed(data: list[int]) -> int:
    """Reply to 0x32 -> rpm."""
    if len(data) < 3 or data[0] != READ_SPEED:
        raise ValueError(f"not a speed reply: {data}")
    return int.from_bytes(bytes(data[1:3]), "big", signed=True)


def parse_io(data: list[int]) -> dict[str, bool]:
    """Reply to 0x34 -> state of the pins."""
    if len(data) < 2 or data[0] != READ_IO:
        raise ValueError(f"not an io reply: {data}")
    b = data[1]
    return {
        "in_1": bool(b & 0x01),
        "in_2": bool(b & 0x02),
        "out_1": bool(b & 0x04),
        "out_2": bool(b & 0x08),
    }


def parse_status(data: list[int]) -> int:
    """The second byte is the status in almost every reply."""
    if len(data) < 2:
        raise ValueError(f"reply too short: {data}")
    return data[1]
