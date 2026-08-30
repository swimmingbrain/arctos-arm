# Bringing up a real arm

The order matters. Every step can be checked before the next one, and until
step 6 only one motor moves at a time.

## 0. Hardware

- MKS SERVO42D on the small axes, SERVO57D on the base and shoulder, all on
  one CAN bus at 500 kbit/s with a 120 ohm terminator at each end.
- A CAN adapter on the computer: a CANable v2 in slcan mode shows up as
  `/dev/ttyACM0` (or `COMx` on windows), a socketcan adapter as `can0`.
- The emergency stop cuts the motor supply. Software cannot replace that.

## 1. Driver settings

Set these on each driver, either on its display or with Arctos Studio:

- CAN id 1 to 6 in joint order (x, y, z, a, b, c), gripper board on 7
- bitrate 500 kbit/s
- work mode `SR_vFOC` (5), otherwise CAN motion commands are ignored
- limit switch enabled for homing; on the 42D with two switches enable the
  port remapping (EN and DIR pins become the second switch)

`arctos setup` writes the current and the work mode from `robot.yaml`
later on, but the CAN id and bitrate have to be set by hand first.
