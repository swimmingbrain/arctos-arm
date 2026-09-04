# arctos_description

Robot model of the Arctos arm: URDF as xacro, STL meshes, RViz configuration.

Taken from the official ROS 2 package:

- Source: https://github.com/cr0Kz/ros2_arctos, the official ROS 2 package
  for the Arctos arm, branch dev, commit 228f6ae0 (2025-02-20)
- License: Apache License 2.0, see LICENSE in this folder. Upstream ships no
  NOTICE file and no per-file copyright headers.
- The STL meshes are the visualisation meshes of the Arctos robot arm designed
  by Arctos Robotics (https://arctosrobotics.com), exactly as published in
  ros2_arctos, byte for byte unchanged. The full CAD files that Arctos Robotics
  sells are not part of this repository.

Changes to the copied files (Apache License 2.0, section 4b):

- `urdf/arctos.xacro`: the include of `arctos_ros2_control.xacro` and the
  `arctos_ros2_control` macro call were removed, the motors are driven by
  `arctos_driver` instead of ros2_control. A comment at the top of the file
  says so.
- `config/`, `urdf/base_xyz/`, `urdf/arctos_ros2_control.xacro` and the
  test_single_motor files were not copied, they belong to the ros2_control route.
- This ORIGIN.md was added.

The joint names X_joint to C_joint and the link names are used the same way
in `arctos_moveit_config/config/arctos.srdf` and in `arctos_driver`. The
joint origins are also the `kinematics.links` numbers in the library's
robot.yaml, both have to match.

Look at the model without a robot:

```bash
ros2 launch arctos_description view_robot.launch.py
```
