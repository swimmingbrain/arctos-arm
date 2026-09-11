# arctos_moveit_config

MoveIt 2 for the Arctos arm without ros2_control: the planned trajectory goes
as an action to `arctos_driver`, which drives the motors over CAN.

```bash
ros2 launch arctos_moveit_config moveit.launch.py sim:=true    # moveit + rviz, virtual motors
ros2 launch arctos_moveit_config moveit.launch.py              # on the robot
ros2 launch arctos_moveit_config moveit.launch.py rviz:=false  # headless
```

Files:

```
urdf/arctos.urdf.xacro         includes the model from arctos_description
config/arctos.srdf             groups arm and gripper, named states home, open, closed
config/kinematics.yaml         kdl solver for the group arm
config/joint_limits.yaml       velocities for planning, matching robot.yaml
config/moveit_controllers.yaml how moveit talks to arm_node (the two actions)
config/moveit.rviz             rviz with the motion planning panel
launch/moveit.launch.py        model, driver node, move_group, rviz
arctos_moveit_config/moveit_demo.py   example client for your own scripts
```

More in [docs/ros2.md](../../docs/ros2.md).
