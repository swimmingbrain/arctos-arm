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
        self.declare_parameter("rate", 10.0)
        cfg = str(self.get_parameter("config").value) or None
        sim = bool(self.get_parameter("sim").value)
        self.robot = self.build_robot(cfg, sim)
        self.names = [ROS_NAMES.get(n, n) for n in self.robot.arm.names]
        self._moving = threading.Lock()  # only one motion at a time
        self.group = ReentrantCallbackGroup()

        self.pub = self.create_publisher(JointState, "joint_states", 10)
        rate = float(self.get_parameter("rate").value)
        self.create_timer(1.0 / rate, self.publish, callback_group=self.group)
        self.create_subscription(
            JointState, "arctos/joint_cmd", self.on_cmd, 10, callback_group=self.group
        )
        self.create_service(Trigger, "arctos/stop", self.on_stop, callback_group=self.group)
        self.create_service(Trigger, "arctos/home", self.on_home, callback_group=self.group)
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

    # --- moveit: follow a path ---

    def accept_goal(self, _request: FollowJointTrajectory.Goal) -> GoalResponse:
        if self.busy():
            self.get_logger().warning("path rejected, a motion is already running")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def accept_cancel(self, _handle: ServerGoalHandle) -> CancelResponse:
        return CancelResponse.ACCEPT

    def follow(self, handle: ServerGoalHandle) -> FollowJointTrajectory.Result:
        result = FollowJointTrajectory.Result()
        traj = handle.request.trajectory
        try:
            names = [SHORT_NAMES.get(n, n) for n in traj.joint_names]
            points = [
                trajectory.Point(
                    time=p.time_from_start.sec + p.time_from_start.nanosec * 1e-9,
                    degs=trajectory.reorder(
                        names,
                        [math.degrees(v) for v in p.positions],
                        self.robot.arm.names,
                    ),
                )
                for p in traj.points
            ]
        except KeyError as e:
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            result.error_string = str(e)
            handle.abort()
            return result

        def feedback(_i: int, p: trajectory.Point) -> None:
            fb = FollowJointTrajectory.Feedback()
            fb.joint_names = self.names
            fb.desired = JointTrajectoryPoint()
            fb.desired.positions = [math.radians(d) for d in p.degs]
            handle.publish_feedback(fb)

        with self._moving:
            self.robot.clear()
            try:
                trajectory.follow(
                    self.robot.arm,
                    points,
                    cancelled=lambda: bool(handle.is_cancel_requested),
                    on_point=feedback,
                )
            except Stopped as e:
                result.error_string = str(e)
                if handle.is_cancel_requested:
                    handle.canceled()
                else:
                    result.error_code = (
                        FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                    )
                    handle.abort()
                return result
            except Exception as e:  # noqa: BLE001
                self.get_logger().error(f"path failed: {e}")
                self.robot.arm.stop()
                result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                result.error_string = str(e)
                handle.abort()
                return result
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        handle.succeed()
        return result

    def grip(self, handle: ServerGoalHandle) -> GripperCommand.Result:
        wanted = float(handle.request.command.position)
        if wanted > JAW_OPEN / 2:
            self.robot.gripper.open()
        else:
            self.robot.gripper.close()
        result = GripperCommand.Result()
        result.position = wanted
        result.reached_goal = True
        handle.succeed()
        return result

    # --- simple commands without moveit ---

    def on_cmd(self, msg: JointState) -> None:
        target = {
            SHORT_NAMES.get(n, n): math.degrees(p)
            for n, p in zip(msg.name, msg.position, strict=True)
        }
        self.run_in_background(lambda: self.robot.arm.move(target), f"joints {target}")

    def on_stop(self, _req: Trigger.Request, res: Trigger.Response) -> Trigger.Response:
        self.robot.stop()
        res.success, res.message = True, "stopped"
        return res

    def on_home(self, _req: Trigger.Request, res: Trigger.Response) -> Trigger.Response:
        ok = self.run_in_background(lambda: self.robot.goto("home"), "home")
        res.success, res.message = ok, "home" if ok else "busy"
        return res

    def on_open(self, _req: Trigger.Request, res: Trigger.Response) -> Trigger.Response:
        self.robot.gripper.open(wait=False)
        res.success, res.message = True, "open"
        return res

    def on_close(self, _req: Trigger.Request, res: Trigger.Response) -> Trigger.Response:
        self.robot.gripper.close(wait=False)
        res.success, res.message = True, "closed"
        return res

    # --- internal ---

    def run_in_background(self, fn: Callable[[], object], what: str) -> bool:
        """Run a motion in a thread so the node keeps answering."""
        if self.busy():
            self.get_logger().warning(f"{what}: something is already running")
            return False

        def job() -> None:
            with self._moving:
                self.robot.clear()
                try:
                    fn()
                except Exception as e:  # noqa: BLE001
                    self.get_logger().error(f"{what}: {e}")

        threading.Thread(target=job, daemon=True).start()
        return True

    def destroy_node(self) -> bool:
        self.robot.close()
        return bool(super().destroy_node())


def spin(node: Node) -> None:
    """Spin a node on a multi threaded executor until ctrl-c."""
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


def main() -> None:
    rclpy.init()
    try:
        spin(ArmNode())
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
