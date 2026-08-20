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


class Kinematics:
    def __init__(
        self,
        links: Sequence[dict[str, Any]],
        tool: Sequence[float] = (0.0, 0.0, 0.0),
        tool_axis: Sequence[float] = (0.0, -1.0, 0.0),
        bounds_deg: Sequence[tuple[float, float]] | None = None,
        max_error: float = 0.005,
    ) -> None:
        self.names = [str(link["name"]) for link in links]
        self.tool_axis = np.array(tool_axis, dtype=float)
        self.max_error = max_error
        chain_links: list[Any] = [OriginLink()]
        for i, link in enumerate(links):
            lo, hi = (-180.0, 180.0)
            if bounds_deg and i < len(bounds_deg):
                lo, hi = bounds_deg[i]
            chain_links.append(
                URDFLink(
                    name=str(link["name"]),
                    origin_translation=np.array(link["xyz"], dtype=float),
                    origin_orientation=np.zeros(3),
                    rotation=np.array(link["axis"], dtype=float),
                    bounds=(math.radians(lo), math.radians(hi)),
                    use_symbolic_matrix=False,
                )
            )
        chain_links.append(
            URDFLink(
                name="tool",
                origin_translation=np.array(tool, dtype=float),
                origin_orientation=np.zeros(3),
                joint_type="fixed",
                use_symbolic_matrix=False,
            )
        )
        mask = [False] + [True] * len(links) + [False]
        self.chain = Chain(chain_links, active_links_mask=mask, name="arctos")
