"""Real-robot backend (ROS 2 Humble/Jazzy on Jetson AGX Orin). STUBS - see drivers.py and README roadmap."""
from __future__ import annotations

from typing import Any, Optional

from ...config import RobotConfig
from ...types import Detection, Pose2D
from ..interfaces import HardwareSet, MotionPlanner, Perception, Trajectory, WorldModel
from .drivers import (AmazingHand, CanBms, CoffeeMcu, Hub75Face, NanoScan3, NavDock, NotBroughtUp, OpenArm,
                      OpenArmGripper, OrbbecCamera, OrcaHand, PnozRelay, RosBridge, TracerBase, UvcCamera)


class MoveItPlanner(MotionPlanner):
    """MoveIt 2 via ``pymoveit2`` / MoveGroup action ``/move_action`` with the openarm_bimanual_moveit_config
    (groups right_arm / left_arm). Pick: grasp pose from Perception -> pre-grasp (+12 cm) -> Cartesian approach
    (``/compute_cartesian_path``) -> close -> retreat. Collision scene from the Gemini depth (octomap)."""

    def plan_pick(self, side: str, target: Detection, surface: str = "bench") -> Optional[Trajectory]:
        raise NotBroughtUp("MoveItPlanner.plan_pick")

    def plan_place(self, side: str, where: dict[str, Any]) -> Optional[Trajectory]:
        raise NotBroughtUp("MoveItPlanner.plan_place")

    def plan_to_point(self, side: str, xyz_robot, duration_s: float | None = None) -> Optional[Trajectory]:
        raise NotBroughtUp("MoveItPlanner.plan_to_point")

    def plan_home(self, side: str) -> Optional[Trajectory]:
        raise NotBroughtUp("MoveItPlanner.plan_home")


class RealPerception(Perception):
    """Port of v5's Vision (HSV + depth back-projection) onto Gemini point clouds; later a learned detector
    (e.g. Isaac ROS / YOLO TensorRT). Person detection comes from the scanners + Gemini, never from the 360 cam alone."""

    def detect(self, what: str) -> list[Detection]:
        raise NotBroughtUp("RealPerception.detect")


class MapWorld(WorldModel):
    """Named poses from the YAML (in the Nav2 map frame); people by name from a small CRM/desk table."""

    def __init__(self, cfg: RobotConfig):
        self.cfg = cfg

    def resolve(self, target: str) -> Optional[Pose2D]:
        loc = self.cfg.locations.get(target.upper())
        if loc:
            return Pose2D(*loc)
        p = self.cfg.people.get(target.capitalize())
        return Pose2D(p[0], p[1], 0.0) if p else None

    def known_targets(self) -> list[str]:
        return list(self.cfg.locations) + list(self.cfg.people)

    def person_names(self) -> list[str]:
        return list(self.cfg.people)


def build_real_hal(cfg: RobotConfig) -> HardwareSet:
    r = cfg.real
    ros = RosBridge(r)
    hands = cfg.hands.split("+")
    hand_cls = {"gripper": OpenArmGripper, "orca": OrcaHand, "amazing": AmazingHand}

    def hand(side: str, kind: str):
        return hand_cls.get(kind, OpenArmGripper)(f"gripper_{side}", r.get("grippers", {}), ros, side)

    cams = {}
    for name, c in r.get("cameras", {}).items():
        cams[name] = (OrbbecCamera if c.get("driver") == "orbbec_camera" else UvcCamera)(name, c, ros)
    return HardwareSet(
        backend="real",
        base=TracerBase("tracer", r.get("base", {}), ros),
        dock=NavDock("dock", r.get("dock", {}), ros),
        arms={s: OpenArm(f"arm_{s}", r.get("arms", {}), ros, s) for s in ("right", "left")},
        grippers={"right": hand("right", hands[0]), "left": hand("left", hands[-1])},
        scanners={n: NanoScan3(n, c, ros) for n, c in r.get("scanners", {}).items()},
        relay=PnozRelay("pnoz", r.get("relay", {}), ros),
        cameras=cams,
        battery=CanBms("bms", r.get("battery", {}), ros),
        face=Hub75Face("face", r.get("face", {}), ros),
        coffee=CoffeeMcu("coffee", r.get("coffee", {}), ros) if cfg.has("coffee") else None,
        planner=MoveItPlanner(),
        perception=RealPerception(),
        world=MapWorld(cfg),
        engine=None,
    )
