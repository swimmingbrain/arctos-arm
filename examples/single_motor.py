"""Talk to one driver without the rest of the library.

python examples/single_motor.py            # id 1 on /dev/ttyACM0
python examples/single_motor.py --sim      # a virtual driver
"""

import sys

from arctos.can_bus import CanBus
from arctos.motor import Motor
from arctos.sim import FakeDriver

CAN_ID = 1


def main() -> None:
    if "--sim" in sys.argv:
        fake = FakeDriver(CAN_ID, speedup=10.0)
        fake.start()
        bus = CanBus(interface="virtual", channel="arctos-sim")
    else:
        bus = CanBus(interface="slcan", channel="/dev/ttyACM0", bitrate=500000)

    with bus:
        m = Motor(bus, CAN_ID, "test", acc=60)
        print("answers:", m.ping())
        print("position:", m.position(), "deg")
        m.move_to(90, rpm=200)
        print("position:", m.position(), "deg")
        m.move_by(-90, rpm=200)
        print("position:", m.position(), "deg")
        print("inputs:", m.io())


if __name__ == "__main__":
    main()
