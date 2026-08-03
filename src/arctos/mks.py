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
