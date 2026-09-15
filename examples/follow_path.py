"""Follow a small timed path, the same way the ROS 2 node executes MoveIt plans.

python examples/follow_path.py --sim
"""

import sys

from arctos import robot, trajectory


def main() -> None:
    sim = "--sim" in sys.argv
    points = [
        trajectory.Point(time=1.0, degs=[10, 10, -10, 0, -20, 0]),
        trajectory.Point(time=2.0, degs=[20, 20, -20, 0, -40, 0]),
        trajectory.Point(time=3.5, degs=[0, 0, 0, 0, 0, 0]),
    ]
    with robot.build(sim=sim) as r:
        trajectory.follow(
            r.arm,
            points,
            on_point=lambda i, p: print(f"point {i} at {p.time:.1f} s: {p.degs}"),
        )
        print("done:", [round(d, 1) for d in r.arm.positions()])


if __name__ == "__main__":
    main()
