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
