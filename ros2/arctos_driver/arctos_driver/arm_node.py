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


class ArmNode(Node):
    def __init__(self, name: str = "arctos_arm") -> None:
        super().__init__(name)
        self.declare_parameter("config", "")
        self.declare_parameter("sim", False)
        cfg = str(self.get_parameter("config").value) or None
        sim = bool(self.get_parameter("sim").value)
        self.robot = self.build_robot(cfg, sim)
        self.names = [ROS_NAMES.get(n, n) for n in self.robot.arm.names]
        self._moving = threading.Lock()  # only one motion at a time
        self.group = ReentrantCallbackGroup()

        self.pub = self.create_publisher(JointState, "joint_states", 10)
        self.create_timer(0.1, self.publish, callback_group=self.group)
        self.create_subscription(
            JointState, "arctos/joint_cmd", self.on_cmd, 10, callback_group=self.group
        )
        self.create_service(Trigger, "arctos/stop", self.on_stop, callback_group=self.group)
        self.create_service(
            Trigger, "arctos/gripper_open", self.on_open, callback_group=self.group
        )
        self.create_service(
            Trigger, "arctos/gripper_close", self.on_close, callback_group=self.group
        )
        self._traj_server = ActionServer(
            self,
            FollowJointTrajectory,
            "arm_controller/follow_joint_trajectory",
            execute_callback=self.follow,
            goal_callback=self.accept_goal,
            cancel_callback=self.accept_cancel,
            callback_group=self.group,
        )
        self._grip_server = ActionServer(
            self,
            GripperCommand,
            "gripper_controller/gripper_cmd",
            execute_callback=self.grip,
            callback_group=self.group,
        )
        self.get_logger().info(f"arctos arm ready, sim={sim}, joints={self.names}")

    # --- hooks for subclasses ---

    def build_robot(self, config: str | None, sim: bool) -> Robot:
        """Create the robot object; override to return your own Robot."""
        return robot_mod.build(config, sim=sim)

    def busy(self) -> bool:
        """Is a motion running? Override when you run your own motions."""
        return self._moving.locked()

    # --- out ---

    def publish(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        try:
            degs = self.robot.arm.positions()
        except Exception as e:  # noqa: BLE001
            self.get_logger().warning(f"cannot read positions: {e}")
            return
        jaw = JAW_OPEN if self.robot.gripper.is_open else 0.0
        msg.name = self.names + JAWS
        msg.position = [math.radians(d) for d in degs] + [jaw, jaw]
        self.pub.publish(msg)
