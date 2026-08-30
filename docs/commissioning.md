# Bringing up a real arm

The order matters. Every step can be checked before the next one, and until
step 6 only one motor moves at a time.

## 0. Hardware

- MKS SERVO42D on the small axes, SERVO57D on the base and shoulder, all on
  one CAN bus at 500 kbit/s with a 120 ohm terminator at each end.
- A CAN adapter on the computer: a CANable v2 in slcan mode shows up as
  `/dev/ttyACM0` (or `COMx` on windows), a socketcan adapter as `can0`.
- The emergency stop cuts the motor supply. Software cannot replace that.
