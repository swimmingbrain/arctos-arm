from glob import glob

from setuptools import setup

package_name = "arctos_moveit_config"

setup(
    name=package_name,
    version="0.3.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*")),
        ("share/" + package_name + "/urdf", glob("urdf/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    description="MoveIt 2 configuration for the Arctos robot arm",
    license="MIT",
    entry_points={
        "console_scripts": [
            "moveit_demo = arctos_moveit_config.moveit_demo:main",
        ],
    },
)
