"""Send and receive on the CAN bus (python-can).

Real hardware: a CANable v2 over slcan (USB serial, /dev/ttyACM0) or socketcan (can0).
Simulation: interface "virtual", the fake drivers from sim.py answer.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import can

from arctos import mks

log = logging.getLogger(__name__)

SIM_CHANNEL = "arctos-sim"


class CanError(Exception):
    """Something on the bus went wrong."""
