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

    # --- forward ---

    def frame(self, degs: Sequence[float]) -> np.ndarray:
        """4x4 matrix of the tool for joint angles in degrees."""
        return np.asarray(self.chain.forward_kinematics(self._full(degs)))

    def position(self, degs: Sequence[float]) -> Vec3:
        p = self.frame(degs)[:3, 3]
        return (float(p[0]), float(p[1]), float(p[2]))

    def yaw(self, degs: Sequence[float]) -> float:
        """Rotation of the tool around the vertical, in degrees."""
        r = self.frame(degs)[:3, :3]
        side = r @ self._side_axis()
        return math.degrees(math.atan2(side[1], side[0]))

    # --- inverse ---

    def ik(
        self,
        xyz: Sequence[float],
        yaw: float | None = None,
        seed: Sequence[float] | None = None,
        down: bool = True,
    ) -> list[float]:
        """Joint angles (degrees) for a tool position, tool pointing down."""
        start = self._full(seed) if seed is not None else None
        kwargs: dict[str, Any] = {}
        if down:
            idx = int(np.argmax(np.abs(self.tool_axis)))
            sign = 1.0 if self.tool_axis[idx] > 0 else -1.0
            kwargs["orientation_mode"] = "XYZ"[idx]
            kwargs["target_orientation"] = [0.0, 0.0, -sign]
        result = self.chain.inverse_kinematics(
            target_position=list(xyz), initial_position=start, **kwargs
        )
        degs = [math.degrees(float(v)) for v in result[1 : 1 + len(self.names)]]
        err = float(np.linalg.norm(np.array(self.position(degs)) - np.array(xyz)))
        if err > self.max_error:
            raise IkError(
                f"position {list(xyz)} not reachable, error {err * 1000:.1f} mm"
            )
        if yaw is not None and down:
            degs = self._turn_to_yaw(degs, yaw)
        return [round(d, 3) for d in degs]

    # --- internal ---

    def _full(self, degs: Sequence[float] | None) -> list[float]:
        """Pad joint angles to the whole chain (origin and tool included)."""
        if degs is None:
            return [0.0] * (len(self.names) + 2)
        return [0.0, *[math.radians(d) for d in degs], 0.0]

    def _side_axis(self) -> np.ndarray:
        """An axis perpendicular to the tool so that a rotation can be measured."""
        idx = int(np.argmax(np.abs(self.tool_axis)))
        side = np.zeros(3)
        side[(idx + 1) % 3] = 1.0
        return side

    def _turn_to_yaw(self, degs: list[float], yaw: float) -> list[float]:
        """Turn the last joint so that the tool has the wanted rotation."""
        delta = _wrap(yaw - self.yaw(degs))
        for sign in (1.0, -1.0):
            trial = list(degs)
            trial[-1] = degs[-1] + sign * delta
            if abs(_wrap(self.yaw(trial) - yaw)) < 1.0:
                return trial
        log.warning(
            "rotation %.0f deg not reachable, staying at %.0f", yaw, self.yaw(degs)
        )
        return degs


def _wrap(deg: float) -> float:
    return (deg + 180.0) % 360.0 - 180.0
