# everything together: robot model, driver node, moveit (move_group) and rviz.
#   ros2 launch arctos_moveit_config moveit.launch.py sim:=true     without a robot
#   ros2 launch arctos_moveit_config moveit.launch.py               on the robot
#   ros2 launch arctos_moveit_config moveit.launch.py rviz:=false   headless
# your own driver node instead of arctos_driver/arm_node:
#   ros2 launch arctos_moveit_config moveit.launch.py driver_package:=my_pkg driver_executable:=my_node
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description() -> LaunchDescription:
    moveit_config = (
        MoveItConfigsBuilder("arctos", package_name="arctos_moveit_config")
        .robot_description(file_path="urdf/arctos.urdf.xacro")
        .robot_description_semantic(file_path="config/arctos.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .planning_scene_monitor(
            publish_robot_description=True, publish_robot_description_semantic=True
        )
        .to_moveit_configs()
    )
    share = get_package_share_directory("arctos_moveit_config")

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[moveit_config.robot_description],
    )
    driver = Node(
        package=LaunchConfiguration("driver_package"),
        executable=LaunchConfiguration("driver_executable"),
        name="arctos_arm",
        output="screen",
        parameters=[
            {
                "sim": ParameterValue(LaunchConfiguration("sim"), value_type=bool),
                "config": ParameterValue(LaunchConfiguration("config"), value_type=str),
            }
        ],
    )
