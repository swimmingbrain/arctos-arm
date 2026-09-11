# ROS 2, MoveIt 2 and RViz

Three packages in `ros2/`:

| Package | Content |
|---|---|
| `arctos_description` | robot model (URDF as xacro, STL meshes, RViz config), taken from the official ros2_arctos, see ORIGIN.md |
| `arctos_driver` | the node `arm_node`: joint states, trajectory execution, gripper, a few services |
| `arctos_moveit_config` | SRDF, kinematics, joint limits, controllers, RViz, launch files, a MoveIt client example |

How it fits together: MoveIt plans a path (joint angles over time) and sends
it as a `FollowJointTrajectory` action to `arm_node`. The node executes it
point by point over CAN with this library (ratios, wrist differential,
limits, offsets) and publishes `/joint_states` so RViz shows the real arm.
The gripper hangs on a `GripperCommand` action. With `sim:=true` the virtual
drivers run and MoveIt with RViz works without a robot.

No ros2_control and no C++. The official ros2_arctos goes through
ros2_control with a C++ hardware interface; if you prefer that route the
description package is the same.
