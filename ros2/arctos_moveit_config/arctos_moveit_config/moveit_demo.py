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
