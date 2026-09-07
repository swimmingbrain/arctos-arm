from glob import glob

from setuptools import setup

package_name = "arctos_driver"

setup(
    name=package_name,
    version="0.3.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    description="ROS 2 driver node for the Arctos robot arm",
    license="MIT",
    entry_points={
        "console_scripts": [
            "arm_node = arctos_driver.arm_node:main",
        ],
    },
)
