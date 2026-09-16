# Changelog

## 0.1.0

- MKS SERVO42D/57D CAN protocol, bus wrapper, single motor control
- Arm with gear ratios, wrist differential, limits and coordinated moves
- Gripper, safety stop, virtual drivers for a simulation
- Forward and inverse kinematics from the URDF numbers
- Configuration files: robot.yaml, poses.yaml, offsets.yaml, a default config in the package
- `arctos` command line

## 0.2.0

- Timed trajectory following for MoveIt
- ROS 2 packages: `arctos_description`, `arctos_driver`, `arctos_moveit_config`
- Emergency stop input thread and a reader for Jetson GPIO pins

## 0.3.0

- `add_commands()` to reuse the CLI commands in other projects
- Examples, documentation for configuration, commissioning, the CAN protocol and ROS 2
- Continuous integration with ruff, mypy and pytest
- NOTICE file with the third-party material and a note that the project is not affiliated with Arctos Robotics
- Fixes: replies with a bad crc are ignored, move timeout when the encoder cannot be read, range check for 24 bit values
