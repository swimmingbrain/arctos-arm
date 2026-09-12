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

## Install

ROS 2 Humble (Ubuntu 22.04, JetPack 6) or Jazzy (Ubuntu 24.04). The packages
are pure Python and work on both, replace `humble` with `jazzy` below.

```bash
sudo apt install ros-humble-desktop ros-dev-tools
sudo apt install ros-humble-moveit ros-humble-xacro ros-humble-joint-state-publisher-gui \
    ros-humble-moveit-configs-utils ros-humble-control-msgs python3-colcon-common-extensions
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

The nodes run with the system python because `rclpy` lives there, so the
library has to be installed there as well:

```bash
cd ~/arctos-arm
uv pip install --system -e .          # ubuntu 24.04: add --break-system-packages
python3 -c "import arctos, can, ikpy; print('ok')"
```

## Workspace

```bash
mkdir -p ~/ros2_ws/src
ln -s ~/arctos-arm/ros2/arctos_description ~/ros2_ws/src/
ln -s ~/arctos-arm/ros2/arctos_driver ~/ros2_ws/src/
ln -s ~/arctos-arm/ros2/arctos_moveit_config ~/ros2_ws/src/
cd ~/ros2_ws
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

With `--symlink-install` a change in a python file only needs a restart of
the node. New files or changes to `setup.py` need another `colcon build`.

## Launch

Only look at the model and move the joints with sliders, no robot:

```bash
ros2 launch arctos_description view_robot.launch.py
```

MoveIt with RViz in the simulation:

```bash
ros2 launch arctos_moveit_config moveit.launch.py sim:=true
```

In the MotionPlanning panel drag the marker or pick `home` under Goal State,
then Plan & Execute. Start with a velocity scaling of 0.2.

On the robot the same without `sim:=true`. Bring the arm up first as in
[commissioning.md](commissioning.md). Headless (Jetson without a screen):
`rviz:=false` and start RViz on another computer in the same network with
the same `ROS_DOMAIN_ID`.

Only the driver node, without MoveIt:

```bash
ros2 launch arctos_driver arm.launch.py sim:=true
```

## Interfaces of arm_node

| Name | Type | Direction |
|---|---|---|
| `/joint_states` | sensor_msgs/JointState | out, X_joint .. C_joint plus gripper jaws |
| `/arm_controller/follow_joint_trajectory` | control_msgs/action/FollowJointTrajectory | in, from MoveIt |
| `/gripper_controller/gripper_cmd` | control_msgs/action/GripperCommand | in, from MoveIt |
| `/arctos/joint_cmd` | sensor_msgs/JointState | in, target angles in rad |
| `/arctos/stop`, `/arctos/home`, `/arctos/gripper_open`, `/arctos/gripper_close` | std_srvs/Trigger | services |

Parameters: `sim` (bool), `config` (path to robot.yaml or its folder), `rate`
(Hz for joint_states, default 10).

Without MoveIt:

```bash
ros2 topic pub --once /arctos/joint_cmd sensor_msgs/msg/JointState "{name: [Y_joint], position: [0.5]}"
ros2 service call /arctos/stop std_srvs/srv/Trigger
ros2 service call /arctos/gripper_open std_srvs/srv/Trigger
ros2 topic echo /joint_states
```
