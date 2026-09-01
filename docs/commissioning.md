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

## 2. Bus check

```bash
arctos init                 # once, then edit config/robot.yaml: can.channel
arctos scan
```

All six joints have to answer. If nothing answers: wrong port, wrong bitrate,
missing terminator, or the drivers are in a mode without CAN.

## 3. Currents

```bash
arctos setup
```

Writes `current` and `driver.work_mode` from the config into every driver.
The default currents are low on purpose. More current means more torque and
more heat; the 42D takes up to 3000 mA, the 57D up to 5200 mA.

## 4. One motor at a time

```bash
arctos motor 1 90 --rpm 100      # motor degrees, no gearbox, no limits
arctos motor 1 0 --rpm 100
```

Watch the direction. If the joint turns the wrong way, set `invert: true`
for that joint in `robot.yaml`. Do this for ids 1 to 6.

## 5. Joints

```bash
arctos move x 20
arctos move -- x -20
arctos move b 20
```

`move` uses the ratio, the direction and the limits from the config. On the
wrist both motors have to turn for `b` and for `c`. If the wrong joint moves,
swap the signs in `coupling.matrix`.

## 6. Limits

Check `min` and `max` of every joint on the robot and make them tighter if
something touches. The limits are checked in software before every move.

## 7. Homing and the zero pose

```bash
arctos home                       # every joint drives to its switch, one after the other
```

Then bring the arm into the zero pose by hand or with `move` (upper arm
vertical, forearm horizontal, tool pointing forward, all wrist joints
centered) and run

```bash
arctos calibrate
```

This stores the difference between the switch position and the zero pose in
`offsets.yaml`. From now on `arctos home` after every power up is enough,
the angles are right afterwards.

## 8. Poses and kinematics

```bash
arctos enable false               # release the motors, move the arm by hand
arctos teach pick                 # store the position
arctos enable true
arctos status                     # tool position from the kinematics
arctos xyz 0.1 -0.3 0.05          # move the tool to a point
```

If `status` shows a tool position that does not match reality, the
`kinematics.links` numbers or an `invert` flag are wrong. Compare with the
URDF in `ros2/arctos_description`.
