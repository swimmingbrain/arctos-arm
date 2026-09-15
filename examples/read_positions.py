"""Print the joint angles and the tool position once a second.

python examples/read_positions.py          # real robot, config from ./config
python examples/read_positions.py --sim    # virtual drivers
"""

import sys
import time

from arctos import robot


def main() -> None:
    sim = "--sim" in sys.argv
    with robot.build(sim=sim) as r:
        while True:
            degs = r.arm.positions()
            x, y, z = r.kin.position(degs)
            print(
                "  ".join(
                    f"{n}={d:7.2f}" for n, d in zip(r.arm.names, degs, strict=True)
                ),
                f"| tool x={x:.3f} y={y:.3f} z={z:.3f}",
            )
            time.sleep(1.0)


if __name__ == "__main__":
    main()
