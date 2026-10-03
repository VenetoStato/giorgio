"""Sim implementations of every HAL device, backed by :class:`SimEngine` (giorgio_v5 physics)."""
from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np

from ...types import (ActionHandle, ArmStatus, BaseStatus, BatteryStatus, CoffeeStatus, DockStatus, GripperStatus,
                      Pose2D, RelayStatus, ScanFrame)
from ..interfaces import (ArmDriver, BaseDriver, BatteryDriver, CameraDriver, CoffeeModuleDriver, DockDriver, FaceDriver,
                          GripperDriver, SafetyRelayDriver, SafetyScannerDriver, Trajectory)
from .engine import FACE_CODE_OF, FACE_CODES, LegacySkillAction, NavigateAction, SimEngine


class _SimDevice:
    backend = "sim"

    def __init__(self, engine: SimEngine, name: str):
        self.e, self.name = engine, name


class SimBase(_SimDevice, BaseDriver):
    def status(self) -> BaseStatus:
        g = self.e.g
        nav = self.e.base_action is not None and isinstance(self.e.base_action, NavigateAction)
        return BaseStatus(pose=self.e.base_pose(), v=float(g["drive"]["v"]), w=float(g["drive"]["w"]),
                          navigating=nav or g["mission"]["state"].startswith("drive"), speed_scale=self.e.k_base)

    def navigate_to(self, goal: Pose2D) -> ActionHandle:
        return self.e.start_base_action(NavigateAction(self.e, goal, ActionHandle(f"navigate({goal.x:.1f},{goal.y:.1f})")))

    def stop(self) -> None:
        self.e.cancel_base_action("stop requested")

    def set_speed_scale(self, k: float) -> None:
        self.e.k_base_cmd = float(np.clip(k, 0.0, 1.0))


class SimDock(_SimDevice, DockDriver):
    def dock(self, dock_id: str = "home") -> ActionHandle:
        bat = self.e.g["BAT"]
        return self.e.start_base_action(LegacySkillAction(
            self.e, {"skill": "ricarica"}, ActionHandle("dock"),
            success=lambda: (bool(bat["charging"]), "contacts closed, charging" if bat["charging"] else "docking failed"),
            timeout_s=120.0))

    def undock(self) -> ActionHandle:
        chg = self.e.g["CHG"]
        stage = Pose2D(float(chg[0] - 0.9 * math.cos(chg[2])), float(chg[1] - 0.9 * math.sin(chg[2])), float(chg[2] + math.pi))
        return self.e.start_base_action(NavigateAction(self.e, stage, ActionHandle("undock")))

    def status(self) -> DockStatus:
        g = self.e.g
        gap, ly, dth = g["dock_error"]()
        return DockStatus(docked=bool(g["docked_at_charger"]()), contacts_closed=bool(g["BAT"]["charging"]),
                          error_mm=(round(float(1000 * gap), 1), round(float(1000 * ly), 1), round(float(math.degrees(dth)), 2)))


class SimArm(_SimDevice, ArmDriver):
    def __init__(self, engine: SimEngine, side: str):
        super().__init__(engine, f"arm_{side}")
        self.side = side

    @property
    def _a(self):
        return self.e.g["arms"][self.side]

    def status(self) -> ArmStatus:
        a = self._a
        return ArmStatus(side=self.side, q=[round(float(x), 4) for x in a.q], busy=bool(a.busy or a.queue),
                         speed_scale=self.e.k_arm, holding=a.held)

    def execute(self, traj: Trajectory) -> ActionHandle:
        a = self._a
        h = ActionHandle(f"arm_{self.side}.execute")
        if a.busy or a.queue:
            h.fail("arm busy"); return h
        a.start(list(traj.payload))
        h._cancel_cb = lambda _h: self.stop()
        return self.e.watch(h, lambda: None if (a.busy or a.queue) else (True, "trajectory complete"))

    def stop(self) -> None:
        a = self._a
        a.segs, a.queue = [], []

    def set_speed_scale(self, k: float) -> None:
        self.e.k_arm_cmd = float(np.clip(k, 0.0, 1.0))


class SimGripper(_SimDevice, GripperDriver):
    OPEN = {"right": -0.785, "left": 0.785}

    def __init__(self, engine: SimEngine, side: str, kind: str):
        super().__init__(engine, f"gripper_{side}")
        self.side, self.kind = side, kind

    def status(self) -> GripperStatus:
        a = self.e.g["arms"][self.side]
        return GripperStatus(side=self.side, kind=self.kind, opening=round(abs(float(a.grip)) / 0.785, 3), holding=a.held is not None)

    def command(self, opening: float, effort: float = 0.5) -> ActionHandle:
        a = self.e.g["arms"][self.side]
        h = ActionHandle(f"gripper_{self.side}")
        if self.kind != "parallel":
            h.fail(f"{self.kind} hand: scripted grasp not available in sim (use a learned policy, see rl_mani/)"); return h
        if a.busy or a.queue:
            h.fail("arm busy (gripper commands are part of the planned trajectory)"); return h
        a.start([self.e.g["Seg"]("grip", dur=0.3, grip=float(np.clip(opening, 0, 1)) * self.OPEN[self.side])])
        return self.e.watch(h, lambda: None if a.busy else (True, "ok"))


class SimScanner(_SimDevice, SafetyScannerDriver):
    def __init__(self, engine: SimEngine, index: int, name: str):
        super().__init__(engine, name)
        self.k = index

    def read(self) -> ScanFrame:
        g = self.e.g
        hits = g["state"]["hits"]
        fov, n = g["SCAN_FOV"], g["SCAN_N"]
        (ox, oy), yaw = g["SCANNERS"][self.k]
        if self.k >= len(hits):
            return ScanFrame(self.name, -1.0, -fov / 2, fov / (n - 1), [], False, False)
        o, pts, z = hits[self.k]
        rng = np.linalg.norm(pts[:, :2] - o[:2], axis=1)
        return ScanFrame(scanner=self.name, stamp=self.e.scan_stamp, angle_min=-fov / 2, angle_inc=fov / (n - 1),
                         ranges=[round(float(r), 3) for r in rng], protective=bool((z == 2).any()), warning=bool((z >= 1).any()),
                         field_case=str(g["FIELDS"]["mode"]), origin_xy=(float(ox), float(oy)), yaw=float(yaw),
                         min_range=float(rng.min()) if len(rng) else float("inf"),
                         field_radii=(float(g["FIELDS"]["prot"]), float(g["FIELDS"]["warn"])))

    def set_field_case(self, case: str) -> None:
        # in sim, v5's motion code switches cases itself (speed-dependent fields while driving, docking field,
        # learned contour when stationary) - the same thing the nanoScan3 does from its static control inputs.
        mapping = {"stationary": "fermo", "drive": "marcia", "docking": "aggancio", "service": "servizio"}
        self.e.g["FIELDS"]["mode"] = mapping.get(case, case)


class SimRelay(_SimDevice, SafetyRelayDriver):
    """Emulates the PNOZmulti program: E-stop (manual reset) AND scanner OSSDs (automatic restart)."""

    def __init__(self, engine: SimEngine):
        super().__init__(engine, "pnoz")
        self._latched = False

    def status(self) -> RelayStatus:
        hits = self.e.g["state"]["hits"]
        scanners_ok = not any(bool((z == 2).any()) for _, _, z in hits)
        estop_ok = not self.e.hw_estop
        if not estop_ok:
            self._latched = True
        return RelayStatus(estop_ok=estop_ok, scanners_ok=scanners_ok, drives_enabled=estop_ok and scanners_ok and not self._latched,
                           arm_power=estop_ok and not self._latched, reset_required=self._latched and estop_ok, stamp=self.e.time)

    def press_reset(self) -> None:          # the physical blue reset button (sim only)
        if not self.e.hw_estop:
            self._latched = False


class SimCamera(_SimDevice, CameraDriver):
    def __init__(self, engine: SimEngine, name: str, mj_camera: str):
        super().__init__(engine, name)
        self.mj_camera = mj_camera

    def frame(self, width: int = 640, height: int = 400) -> Optional[np.ndarray]:
        return self.e.render(self.mj_camera, width, height)


class SimBattery(_SimDevice, BatteryDriver):
    def status(self) -> BatteryStatus:
        bat = self.e.g["BAT"]
        soc = float(bat["E"] / bat["cap"])
        v = 16 * (3.05 + 0.25 * soc + 0.05 * math.tanh((soc - 0.95) * 30) + (0.1 if bat["charging"] else 0.0))   # 16S LFP
        p = float(bat["P"]) - (960.0 * 0.92 if bat["charging"] and soc < 0.995 else 0.0)
        return BatteryStatus(soc=soc, voltage=round(v, 2), current=round(p / v, 2), power=round(p, 1),
                             charging=bool(bat["charging"]), capacity_wh=float(bat["cap"]))


class SimFace(_SimDevice, FaceDriver):
    def show_safety(self, zone: int) -> None:
        self.e.display_zone = int(zone)       # v5 eyes, moustache and LED strip follow it

    def set_expression(self, expression: str, hold_s: float = 0.0) -> None:
        code = FACE_CODE_OF.get(expression, 0)
        self.e.face_override = (code, self.e.time + (hold_s if hold_s > 0 else 0.5))

    def state(self) -> dict[str, Any]:
        g = self.e.g
        code, gx, gy, blink, _ = g["FACE"]
        rgba = g["m"].geom_rgba[g["EYES"]["l"]]
        return {"expression": FACE_CODES.get(int(code), "neutral"), "gaze": [round(gx, 3), round(gy, 3)],
                "blink": round(float(blink), 3), "color": [int(255 * c) for c in rgba[:3]]}


class SimCoffee(_SimDevice, CoffeeModuleDriver):
    def __init__(self, engine: SimEngine):
        super().__init__(engine, "coffee")
        self._moving_until = -1.0

    def status(self) -> CoffeeStatus:
        g = self.e.g
        pos = float(self.e.d.ctrl[g["SHUTTLE"]])
        sh = "moving" if self.e.time < self._moving_until else ("in" if abs(pos) > 1e-3 else "out")
        return CoffeeStatus(shuttle=sh, brewing=bool(g["BAT"]["heater"]), cups_left=5, ready=not g["BAT"]["heater"])

    def shuttle(self, position: str) -> ActionHandle:
        g = self.e.g
        self.e.d.ctrl[g["SHUTTLE"]] = (g["COF_Y_IN"] - g["COF_Y_OUT"]) if position == "in" else 0.0
        self._moving_until = self.e.time + 2.2
        h = ActionHandle(f"shuttle_{position}")
        return self.e.watch(h, lambda: None if self.e.time < self._moving_until else (True, position))

    def brew(self) -> ActionHandle:
        g = self.e.g
        g["BAT"]["heater"] = True
        h = ActionHandle("brew")
        t_end = self.e.time + 8.0

        def check():
            if self.e.time < t_end:
                return None
            g["BAT"]["heater"] = False
            return (True, "espresso ready")
        return self.e.watch(h, check)
