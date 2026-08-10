"""Stop everything, check limits, read an emergency stop input.

The real emergency stop has to cut the motor power in hardware. This is only
the software side: a stop flag that aborts every motion loop, plus the stop
command that goes out to all motors.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

log = logging.getLogger(__name__)


class Stopped(Exception):
    """Motion aborted (stop button, emergency stop)."""


class LimitError(Exception):
    """Value outside the allowed range."""
