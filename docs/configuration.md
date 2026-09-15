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

### kinematics

The chain for ikpy. Each link is the translation from the previous joint and
the rotation axis, numbers taken from the URDF.

```yaml
kinematics:
  links:
    - {name: x, xyz: [0.0, 0.0, 0.1126], axis: [0, 0, 1]}
    - {name: y, xyz: [0.0, -0.020356, 0.175], axis: [1, 0, 0]}
    # ...
  tool: [0.0, -0.09, 0.0]   # tool center from the flange
  tool_axis: [0, -1, 0]     # direction the tool points to
```

`tool` and `tool_axis` are in the frame of the last joint. `arctos xyz` and
`kin.ik()` place the tool center at the given point with `tool_axis`
pointing straight down.

## poses.yaml

```yaml
home: [0, 0, 0, 0, 0, 0]
pick: [60, 40, -20, 0, -70, 0]
```

Joint angles in degrees, same order as the joints. `arctos teach name` adds
the current position, `arctos pose name` moves there.

## offsets.yaml

```yaml
x: -55.0
y: 0.0
```

The joint angle that corresponds to driver position 0, per joint. Created
by `arctos calibrate` and read on every start. Do not edit by hand, run
`calibrate` again instead. Add it to `.gitignore` if the offsets differ
between robots.

## Extra sections

Your own project can put more sections into the same file. The library only
reads the ones above and `robot.settings.section("name")` returns any other
section as a dict. Every `can_id` found anywhere in the file gets a fake
driver in the simulation, so an extra motor on the bus is simulated too.
