"""ROS 2 node around the arctos library. This is where MoveIt moves the arm.

out:      /joint_states                             joint angles in rad, names as in the urdf
in:       /arctos/joint_cmd                         sensor_msgs/JointState, target angles in rad
actions:  /arm_controller/follow_joint_trajectory   control_msgs/FollowJointTrajectory (moveit)
          /gripper_controller/gripper_cmd           control_msgs/GripperCommand (moveit)
services: /arctos/stop, /arctos/home,
          /arctos/gripper_open, /arctos/gripper_close   std_srvs/Trigger

start:    ros2 run arctos_driver arm_node --ros-args -p sim:=true

Subclass ArmNode and override build_robot() and busy() to hang your own
devices and motions on the same node.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Callable

import rclpy
from control_msgs.action import FollowJointTrajectory, GripperCommand
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectoryPoint

from arctos import robot as robot_mod
from arctos import trajectory
from arctos.robot import Robot
from arctos.safety import Stopped

# names as in the arctos urdf (arctos_description), so rviz and moveit know the model
ROS_NAMES = {
    "x": "X_joint",
    "y": "Y_joint",
    "z": "Z_joint",
    "a": "A_joint",
    "b": "B_joint",
    "c": "C_joint",
}
SHORT_NAMES = {v: k for k, v in ROS_NAMES.items()}
JAWS = ["Left_jaw_joint", "Right_jaw_joint"]
JAW_OPEN = 0.015  # meters, as in the urdf
