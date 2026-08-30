# arctos-arm

Python library, command line tool and ROS 2 packages for the
[Arctos](https://arctosrobotics.com) robot arm with MKS SERVO42D / SERVO57D
closed loop stepper drivers on a CAN bus.

It talks to the drivers directly over CAN, knows about gear ratios, the wrist
differential, joint limits and homing offsets, does forward and inverse
kinematics, and ships a simulation so that everything also runs on a laptop
without the robot.

## What is in here

| Module | Purpose |
|---|---|
| `arctos.mks` | CAN protocol of the MKS SERVO42D/57D drivers, bytes only |
| `arctos.can_bus` | send, receive, wait for a reply (python-can) |
| `arctos.motor` | one driver: move, read, home, stop |
| `arctos.arm` | six joints: ratios, wrist coupling, limits, coordinated moves |
| `arctos.gripper` | the CAN servo gripper |
| `arctos.safety` | stop flag, limit check |
| `arctos.sim` | virtual drivers on a virtual bus |
| `arctos.config` | robot.yaml, poses.yaml, offsets.yaml |
| `arctos.robot` | builds everything from the config |
| `arctos.cli` | the `arctos` command |

## Install

```bash
uv add git+https://github.com/swimmingbrain/arctos-arm
# or
pip install git+https://github.com/swimmingbrain/arctos-arm
```

For development clone the repository and run `uv sync --group dev`.

## Quick start

Nothing plugged in? Use the simulation:

```bash
arctos --sim status                 # joint angles and tool position
arctos --sim move y 30              # one joint to 30 degrees
arctos --sim joints 0 45 -30 0 -60 0
arctos --sim xyz 0.1 -0.3 0.05      # tool to x y z in meters, pointing down
```

On the real arm leave out `--sim`. First copy the default configuration and
put in your CAN port:

```bash
arctos init                          # writes config/robot.yaml and config/poses.yaml
arctos scan                          # which drivers answer
```

## Commands

Every command does one thing. `--sim` in front runs it without hardware,
`--config path` points to another robot.yaml.

```bash
arctos scan                        # which motors answer
arctos status                      # joint angles and tool position
arctos config                      # which config is in use, joints, offsets
arctos enable false                # release the motors (move by hand)
arctos move y 30                   # one joint to 30 degrees
arctos move -- y -30               # negative numbers need the --
arctos jog x 5                     # one joint by 5 degrees
arctos joints 0 45 -30 0 -60 0     # all joints, they arrive together
arctos motor 3 90 --rpm 200        # one driver in motor degrees (no gearbox, no limits)
arctos home                        # homing run of all joints, or: home x y
arctos zero                        # driver: current position is 0
arctos calibrate                   # software: current position is the zero pose
arctos stop                        # emergency stop to all drivers
arctos gripper open                # or close, or a number from 0 to 255
arctos teach pick                  # store the current position as a pose
arctos pose pick                   # move to a stored pose
arctos xyz 0.1 -0.3 0.05           # tool to x y z in meters, pointing down
arctos ik 0.1 -0.3 0.05            # only compute the joint angles
arctos setup                       # write current and work mode into the drivers
```

## From Python

```python
from arctos import robot

with robot.build(sim=True) as r:
    r.arm.move_joint("x", 30)
    r.arm.move([0, 40, -30, 0, -80, 0])
    r.gripper.close()
    print(r.arm.positions())
    print(r.kin.position(r.arm.positions()))
    degs = r.kin.ik((0.1, -0.3, 0.05), seed=r.arm.positions())
    r.arm.move(degs)
```

`robot.build()` reads the config, opens the bus and gives you `arm`, `gripper`,
`kin` (kinematics), `safety` and `settings`. With `sim=True` it also starts the
virtual drivers. Every object can be used on its own as well, for example a
single `Motor` on a `CanBus` if all you want is to spin one driver.

The commands of the CLI can be added to your own typer app, see
`examples/custom_cli.py`.
