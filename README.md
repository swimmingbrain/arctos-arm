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
