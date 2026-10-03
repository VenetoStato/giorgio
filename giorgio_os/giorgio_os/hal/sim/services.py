"""Sim services: motion planning (v5 IK + clash-aware planner), perception (v5 Gemini vision), world model."""
from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np

from ...config import RobotConfig
from ...types import Detection, Pose2D
from ...types import ActionHandle
from ..interfaces import Choreographies, MotionPlanner, Perception, Trajectory, WorldModel
from .engine import LegacySkillAction, SimEngine

TRAY_DROP = 0.060 - 0.016 - 0.020         # release inside the flared tray pocket (same as v5 plan_load)


class SimMotionPlanner(MotionPlanner):
    def __init__(self, engine: SimEngine):
        self.e = engine

    def _arm(self, side: str):
        return self.e.g["arms"][side]

    def _nearest_part(self, xy) -> str:
        g = self.e.g
        return min(g["PARTS"] + ["cup"], key=lambda p: float(np.linalg.norm(self.e.d.body(p).xpos[:2] - np.asarray(xy))))

    def plan_pick(self, side: str, target: Detection, surface: str = "bench") -> Optional[Trajectory]:
        g, a = self.e.g, self._arm(side)
        part = target.ref or self._nearest_part(target.xy)
        z_base = {"bench": g["BENCH_Z"], "tray": g["BUF_Z"]}.get(surface, g["BENCH_Z"])
        segs, q = a.pick(np.asarray(target.xy, float), part, a.q, z_base)
        return Trajectory(side, segs, q, sum(s.dur for s in segs), {"part": part, "surface": surface})

    def plan_place(self, side: str, where: dict[str, Any]) -> Optional[Trajectory]:
        g, a = self.e.g, self._arm(side)
        part = a.held
        if part is None:
            return None
        kind = where.get("kind", "bench")
        if kind == "tray":
            xy = g["buffer_xy"](side, int(where["slot"]))
            segs, q = a.place(xy, part, a.q, g["BUF_Z"], "loaded", drop=TRAY_DROP)
        elif kind == "hole":
            a.target = np.asarray(where.get("true_xy", where["xy"]), float)
            segs, q = a.place(np.asarray(where["xy"], float), part, a.q, g["BENCH_Z"], "inserted", drop=g["FIX_H"] + 0.012)
        else:   # free bench spot; 'cup_on_grid' is v5's generic "released, hand empty" event
            segs, q = a.place(np.asarray(where["xy"], float), part, a.q, g["BENCH_Z"], "cup_on_grid", drop=0.002)
        return Trajectory(side, segs, q, sum(s.dur for s in segs), {"part": part, "kind": kind})

    def plan_to_point(self, side: str, xyz_robot, duration_s: float | None = None) -> Optional[Trajectory]:
        g, a = self.e.g, self._arm(side)
        q = a.solve(a.robot_pt(*xyz_robot), a.q)
        if duration_s is not None:
            segs = [g["Seg"]("joint", a.q.copy(), q, duration_s)]
        else:
            mv = a.jmove(a.q, q)
            segs = mv if isinstance(mv, list) else [mv]
        return Trajectory(side, segs, q, sum(s.dur for s in segs))

    def plan_home(self, side: str) -> Optional[Trajectory]:
        g, a = self.e.g, self._arm(side)
        mv = a.jmove(a.q, g["Q_HOME"][side])
        segs = mv if isinstance(mv, list) else [mv]
        return Trajectory(side, segs, g["Q_HOME"][side], sum(s.dur for s in segs))


class SimPerception(Perception):
    """Runs v5's real image pipeline on the simulated Gemini 336L (colour + depth -> 3D)."""

    def __init__(self, engine: SimEngine):
        self.e = engine

    def detect(self, what: str) -> list[Detection]:
        g = self.e.g
        v = g["vision"]
        out: list[Detection] = []
        if what in ("bottle", "bottles", "part"):
            for dt in v.find_bottles():
                ref = min(g["PARTS"], key=lambda p: float(np.linalg.norm(self.e.d.body(p).xpos[:2] - dt["xy"])))
                out.append(Detection("bottle", (float(dt["xy"][0]), float(dt["xy"][1])), g["BENCH_Z"] + g["PH"], 1.0,
                                     tuple(int(b) for b in dt["box"]), ref))
        elif what in ("hole", "holes"):
            for dt in v.find_holes():
                out.append(Detection("hole", (float(dt["xy"][0]), float(dt["xy"][1])), g["BENCH_Z"] + g["FIX_H"], 1.0,
                                     tuple(int(b) for b in dt["box"])))
        elif what == "tray_slot":                     # free pockets on the onboard tray (wrist-camera check on the robot)
            for side in ("right", "left"):
                for k in range(len(g["BUFFER_SLOTS"])):
                    xy = g["buffer_xy"](side, k)
                    if not any(np.linalg.norm(self.e.d.body(p).xpos[:2] - xy) < 0.03 for p in g["PARTS"]):
                        out.append(Detection("tray_slot", (float(xy[0]), float(xy[1])), g["BUF_Z"], 1.0, None, f"{side}:{k}"))
        elif what == "tray_item":
            for side in ("right", "left"):
                for k in range(len(g["BUFFER_SLOTS"])):
                    xy = g["buffer_xy"](side, k)
                    near = [p for p in g["PARTS"] if np.linalg.norm(self.e.d.body(p).xpos[:2] - xy) < 0.03]
                    if near:
                        pp = self.e.d.body(near[0]).xpos
                        out.append(Detection("bottle", (float(pp[0]), float(pp[1])), g["BUF_Z"], 1.0, None, near[0]))
        elif what == "person":
            for p in g["people"]:
                if p.active:
                    out.append(Detection("person", (float(p.pos[0]), float(p.pos[1])), 1.7, 1.0))
        return out

    def overlay(self) -> Optional[np.ndarray]:
        return self.e.g["vision"].render_overlay()


class SimWorld(WorldModel):
    def __init__(self, engine: SimEngine, cfg: RobotConfig):
        self.e, self.cfg = engine, cfg

    def resolve(self, target: str) -> Optional[Pose2D]:
        g = self.e.g
        t = target.strip()
        alias = {"charger": "C", "dock": "C", "charging station": "C", "kitting": "A", "load": "A", "insertion": "B", "unload": "B"}
        t = alias.get(t.lower(), t)
        if t.upper() in self.cfg.locations:
            x, y, th = self.cfg.locations[t.upper()]
            return Pose2D(x, y, th)
        name = next((n for n in g["PEOPLE_NAMED"] if n.lower() == t.lower()), None)
        if name is not None:
            p = g["pose_near"](name)
            return None if p is None else Pose2D(float(p[0]), float(p[1]), float(p[2]))
        try:
            x, y, *th = [float(s) for s in t.replace(",", " ").split()]
            return Pose2D(x, y, th[0] if th else 0.0)
        except ValueError:
            return None

    def known_targets(self) -> list[str]:
        return list(self.cfg.locations) + list(self.e.g["PEOPLE_NAMED"])

    def person_names(self) -> list[str]:
        return list(self.e.g["PEOPLE_NAMED"])


def heading_to(a: Pose2D, b: Pose2D) -> float:
    return math.atan2(b.y - a.y, b.x - a.x)


class SimChoreographies(Choreographies):
    """v5's proven routines, run unchanged inside the engine's base-action slot."""

    def __init__(self, engine: SimEngine):
        self.e = engine

    def available(self) -> list[str]:
        return ["load_tray", "unload_tray", "make_coffee", "hand_over"]

    def run(self, name: str, **args: Any) -> ActionHandle:
        e, g = self.e, self.e.g
        h = ActionHandle(name)
        if name == "load_tray":
            def ok():
                n = e.onboard_count() + sum(1 for a in g["arms"].values() if a.held)
                return n > 0, f"{n} bottles on board"
            return e.start_base_action(LegacySkillAction(e, {"skill": "carica"}, h, ok, timeout_s=240))
        if name == "unload_tray":
            n0 = g["stats"]["inserted"]

            def ok():
                n = g["stats"]["inserted"] - n0
                return n > 0, f"{n} bottles inserted, {g['stats']['lost']} lost"
            return e.start_base_action(LegacySkillAction(e, {"skill": "scarica_e_inserisci"}, h, ok, timeout_s=240))
        if name == "make_coffee":
            def ok():
                held = g["arms"]["right"].held == "cup"
                return held, "coffee ready in the right gripper" if held else "cup not in gripper"
            return e.start_base_action(LegacySkillAction(e, {"skill": "fai_caffe"}, h, ok, timeout_s=180))
        if name == "hand_over":
            g["AG"]["cup_done"] = False

            def ok():
                return bool(g["AG"].get("cup_done")), "cup handed over" if g["AG"].get("cup_done") else "hand-over not completed"
            return e.start_base_action(LegacySkillAction(e, {"skill": "porta_caffe", "target": args.get("person", "Marco")}, h, ok,
                                                         timeout_s=180))
        h.fail(f"unknown choreography {name}")
        return h
