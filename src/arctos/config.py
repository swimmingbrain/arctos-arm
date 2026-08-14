"""Read robot.yaml, poses.yaml and offsets.yaml.

Lookup order for the config folder: explicit path, then the environment
variable ARCTOS_CONFIG, then ./config in the current directory. When no
robot.yaml is found there, the default config shipped with the package is used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ENV_CONFIG = "ARCTOS_CONFIG"
ROBOT_FILE = "robot.yaml"
POSES_FILE = "poses.yaml"
OFFSETS_FILE = "offsets.yaml"  # written by "arctos calibrate", not by hand
DEFAULT_ROBOT = Path(__file__).resolve().parent / "data" / ROBOT_FILE


def config_dir(path: str | Path | None = None) -> Path:
    """Folder that holds the yaml files."""
    if path is not None:
        p = Path(path)
        return p if p.is_dir() else p.parent
    env = os.environ.get(ENV_CONFIG)
    if env:
        p = Path(env)
        return p if p.is_dir() else p.parent
    return Path.cwd() / "config"


@dataclass
class Settings:
    robot: dict[str, Any]
    poses: dict[str, list[float]] = field(default_factory=dict)
    offsets: dict[str, float] = field(default_factory=dict)
    dir: Path = field(default_factory=lambda: Path.cwd() / "config")
    source: Path = DEFAULT_ROBOT

    def section(self, name: str) -> dict[str, Any]:
        value = self.robot.get(name)
        return dict(value) if isinstance(value, dict) else {}

    @property
    def joint_names(self) -> list[str]:
        return [str(j["name"]) for j in self.robot.get("joints", [])]
