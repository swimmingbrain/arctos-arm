"""Forward and inverse kinematics with ikpy.

The chain is built from kinematics.links in the config (numbers from the
Arctos URDF). Angles in and out are degrees, lengths are meters, the origin
is the robot base.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink

log = logging.getLogger(__name__)

Vec3 = tuple[float, float, float]


class IkError(Exception):
    """No joint angles found for this position."""
