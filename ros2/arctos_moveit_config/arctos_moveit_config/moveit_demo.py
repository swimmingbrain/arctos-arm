"""Drive MoveIt from Python: plan and execute through the move_group action.

    ros2 run arctos_moveit_config moveit_demo joints 0 30 -20 0 -60 0   joint goal in degrees
    ros2 run arctos_moveit_config moveit_demo pose 0.10 -0.30 0.10       tool straight down over x y z (meters)
    ros2 run arctos_moveit_config moveit_demo home                       named state from the srdf

needs: ros2 launch arctos_moveit_config moveit.launch.py sim:=true
"""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence

import rclpy
from geometry_msgs.msg import Pose, Quaternion
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    Constraints,
    JointConstraint,
    MoveItErrorCodes,
    OrientationConstraint,
    PositionConstraint,
)
from rclpy.action import ActionClient
from rclpy.node import Node
from shape_msgs.msg import SolidPrimitive

ARM_JOINTS = ["X_joint", "Y_joint", "Z_joint", "A_joint", "B_joint", "C_joint"]
TIP = "Link_6_1"
FRAME = "world"
# tool points straight down: rotation of 90 degrees around x (the -y axis of the flange becomes -z)
DOWN = Quaternion(x=math.sqrt(0.5), y=0.0, z=0.0, w=math.sqrt(0.5))


class MoveItClient(Node):
    def __init__(self) -> None:
        super().__init__("arctos_moveit_demo")
        self.client = ActionClient(self, MoveGroup, "move_action")

    def _send(self, constraints: Constraints) -> bool:
        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("move_group not found, is moveit.launch.py running?")
            return False
        goal = MoveGroup.Goal()
        goal.request.group_name = "arm"
        goal.request.goal_constraints = [constraints]
        goal.request.allowed_planning_time = 5.0
        goal.request.num_planning_attempts = 5
        goal.request.max_velocity_scaling_factor = 0.3
        goal.request.max_acceleration_scaling_factor = 0.3
        goal.request.start_state.is_diff = True
        goal.planning_options.plan_only = False
        goal.planning_options.replan = False

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        handle = future.result()
        if handle is None or not handle.accepted:
            self.get_logger().error("goal rejected")
            return False
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        code = result_future.result().result.error_code.val
        if code != MoveItErrorCodes.SUCCESS:
            self.get_logger().error(f"moveit error {code}")
            return False
        self.get_logger().info("arrived")
        return True
