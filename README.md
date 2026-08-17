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
