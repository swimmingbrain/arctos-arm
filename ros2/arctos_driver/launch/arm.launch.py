# only the driver node, without moveit and rviz:
#   ros2 launch arctos_driver arm.launch.py sim:=true
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("sim", default_value="false"),
            DeclareLaunchArgument("config", default_value=""),
            Node(
                package="arctos_driver",
                executable="arm_node",
                name="arctos_arm",
                output="screen",
                parameters=[
                    {
                        "sim": ParameterValue(LaunchConfiguration("sim"), value_type=bool),
                        "config": ParameterValue(LaunchConfiguration("config"), value_type=str),
                    }
                ],
            ),
        ]
    )
