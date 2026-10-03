"""MuJoCo simulation backend (wraps ~/giorgio_sim/giorgio_v5.py)."""
from __future__ import annotations

from typing import Any

from ...config import RobotConfig
from ..interfaces import HardwareSet
from .drivers import (SimArm, SimBase, SimBattery, SimCamera, SimCoffee, SimDock, SimFace, SimGripper, SimRelay,
                      SimScanner)
from .engine import SimEngine
from .services import SimChoreographies, SimMotionPlanner, SimPerception, SimWorld

HAND_KIND = {"gripper": "parallel", "orca": "orca", "amazing": "amazing", "leap": "leap", "inspire": "inspire"}


def build_sim_hal(cfg: RobotConfig, **overrides: Any) -> HardwareSet:
    opts = {"soc": 0.85, "humans": True, "seed": 3, "look": "gb"}
    opts.update({k: v for k, v in cfg.sim.items() if k in opts})
    opts.update(overrides)
    e = SimEngine(hands=cfg.hands, **opts)
    hands = cfg.hands.split("+")
    kinds = {"right": HAND_KIND.get(hands[0], hands[0]), "left": HAND_KIND.get(hands[-1], hands[-1])}
    cams = {"chase": SimCamera(e, "chase", "chase"), "top": SimCamera(e, "top", "top"), "gemini": SimCamera(e, "gemini", "gemini")}
    names = e.camera_names()
    for s in ("right", "left"):
        if f"camera_wrist_{s}" in names:
            cams[f"wrist_{s}"] = SimCamera(e, f"wrist_{s}", f"camera_wrist_{s}")
    pano = [n for n in names if n.startswith("pano_")]
    if cfg.has("cam360") and pano:
        cams["pano"] = SimCamera(e, "pano", pano[0])
    return HardwareSet(
        backend="sim",
        base=SimBase(e, "tracer"),
        dock=SimDock(e, "dock"),
        arms={s: SimArm(e, s) for s in ("right", "left")},
        grippers={s: SimGripper(e, s, kinds[s]) for s in ("right", "left")},
        scanners={"front": SimScanner(e, 0, "front"), "rear": SimScanner(e, 1, "rear")},
        relay=SimRelay(e),
        cameras=cams,
        battery=SimBattery(e, "bms"),
        face=SimFace(e, "face"),
        coffee=SimCoffee(e) if cfg.has("coffee") else None,
        planner=SimMotionPlanner(e),
        perception=SimPerception(e),
        world=SimWorld(e, cfg),
        engine=e,
        choreo=SimChoreographies(e),
    )
