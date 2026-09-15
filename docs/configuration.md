# Configuration

Three yaml files, all in one folder:

| File | Content | Written by |
|---|---|---|
| `robot.yaml` | everything about the hardware | you |
| `poses.yaml` | taught joint poses, degrees | `arctos teach` |
| `offsets.yaml` | zero offset per joint, degrees | `arctos calibrate` |

The folder is found in this order: `--config` on the command line (a folder
or the robot.yaml itself), the environment variable `ARCTOS_CONFIG`, then
`./config`. If none of them has a robot.yaml, the default that ships inside the
package is used and poses/offsets are stored in `./config`. `arctos init`
copies that default so you can edit it.

## robot.yaml

### can

```yaml
can:
  interface: slcan          # slcan (CANable on USB) or socketcan
  channel: /dev/ttyACM0     # can0 for socketcan, COM5 on windows
  bitrate: 500000
  timeout: 0.5              # seconds to wait for a reply
  send_gap: 0.001           # pause between frames
```

Anything python-can supports works as `interface`. The simulation ignores
this section and opens a virtual bus.

### joints

One entry per joint, in order from the base to the tool. The names are free,
the default uses `x y z a b c` like the Arctos docs.

```yaml
joints:
  - name: x
    can_id: 1
    driver: 57d       # only a note for humans
    ratio: 13.5       # motor revolutions per joint revolution
    invert: false     # motor turns the wrong way
    min: -170         # joint limits in degrees
    max: 170
    speed: 30         # default speed in degrees per second
    acc: 60           # mks acceleration, 1 slow .. 255 fast, 0 instant
    current: 2000     # working current in mA, written by "arctos setup"
```

The ratios of the Arctos v2 are 13.5, 150, 150, 48, 67.82, 67.82. Whether a
motor needs `invert` can only be checked on the assembled robot, see
[commissioning](commissioning.md).

### coupling

The Arctos wrist is a differential: both motors move both of the last two
joints. The matrix maps joint angles to motor angles:

```yaml
coupling:
  enabled: true
  matrix: [[-0.5, 0.5], [0.5, 0.5]]   # [motor_b, motor_c] = matrix * [joint_b, joint_c]
```

Set `enabled: false` for a wrist without a differential. The matrix is
always applied to the last two joints in the list.

### motion, gripper

```yaml
motion:
  tolerance: 0.5     # degrees, from where a joint counts as arrived
  max_rpm: 1500      # never send more than this to a driver
  min_rpm: 5

gripper:
  can_id: 7
  open: 99           # servo value for open
  close: 0
  settle: 1.0        # seconds to wait after a command
```

When several joints move together, all of them arrive at the same time: the
slowest joint (distance divided by its `speed`) sets the duration, the other
motors get a lower rpm.
