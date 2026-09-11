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

    def go_joints(self, degs: Sequence[float]) -> bool:
        """Joint goal in degrees, order x y z a b c."""
        c = Constraints()
        for name, deg in zip(ARM_JOINTS, degs, strict=True):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = math.radians(deg)
            jc.tolerance_above = jc.tolerance_below = 0.01
            jc.weight = 1.0
            c.joint_constraints.append(jc)
        return self._send(c)

    def go_pose(self, xyz: Sequence[float], orientation: Quaternion = DOWN) -> bool:
        """Flange to x y z (meters, world frame), tool pointing down."""
        c = Constraints()
        pc = PositionConstraint()
        pc.header.frame_id = FRAME
        pc.link_name = TIP
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [0.005]
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = map(float, xyz)
        pose.orientation.w = 1.0
        pc.constraint_region.primitives = [sphere]
        pc.constraint_region.primitive_poses = [pose]
        pc.weight = 1.0
        oc = OrientationConstraint()
        oc.header.frame_id = FRAME
        oc.link_name = TIP
        oc.orientation = orientation
        oc.absolute_x_axis_tolerance = 0.05
        oc.absolute_y_axis_tolerance = 0.05
        oc.absolute_z_axis_tolerance = 3.14  # rotation around the vertical does not matter
        oc.weight = 1.0
        c.position_constraints.append(pc)
        c.orientation_constraints.append(oc)
        return self._send(c)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] not in ("joints", "pose", "home"):
        print(__doc__)
        sys.exit(2)
    rclpy.init()
    node = MoveItClient()
    try:
        if args[0] == "home":
            ok = node.go_joints([0, 0, 0, 0, 0, 0])
        elif args[0] == "joints":
            ok = node.go_joints([float(v) for v in args[1:7]])
        else:
            ok = node.go_pose([float(v) for v in args[1:4]])
    finally:
        node.destroy_node()
        rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
