"""GiorgioRuntime: wires HAL + safety supervisor + energy manager + mission manager + agent.

One control tick (50 Hz) runs, in this fixed order:

  1. safety supervisor  (scanners + relay  -> speed scales applied to drivers)   <- never skipped
  2. software-stop handling (cancel tasks if the operator pressed STOP)
  3. energy manager     (auto-charge / abort-and-charge)
  4. mission manager    (ticks the running skill)
  5. hw.advance(dt)     (sim: physics; real: no-op)

The runtime is single-threaded. The web server talks to it through ``SimServer`` (sim_server.py),
which serialises commands into the control thread.
"""
from __future__ import annotations

import logging
import math
import time
from collections import deque
from typing import Any, Callable, Optional

from .agent.agent import GiorgioAgent
from .config import RobotConfig, load_config
from .energy.manager import EnergyAction, EnergyManager
from .hal import build_hal
from .hal.interfaces import HardwareSet
from .mission.manager import ManagerState, SkillCall, Task, TaskManager
from .safety.supervisor import SafetySupervisor
from .skills import REGISTRY, SkillContext
from .types import Zone

log = logging.getLogger("giorgio.runtime")

CONTROL_DT = 0.02


class GiorgioRuntime:
    def __init__(self, config: str | RobotConfig = "barista", backend: str = "sim", **hal_overrides: Any):
        self.cfg = config if isinstance(config, RobotConfig) else load_config(config)
        self.backend = backend
        self.hw: HardwareSet = build_hal(self.cfg, backend, **hal_overrides)
        self.events: deque[dict[str, Any]] = deque(maxlen=300)
        self._t0 = time.monotonic()
        self.safety = SafetySupervisor(self.cfg.safety)
        self.energy = EnergyManager(self.cfg.energy)
        self.ctx = SkillContext(self.hw, self.cfg, self.now, self._emit)
        self.mission = TaskManager(self.ctx, guard=self._energy_guard)
        people = getattr(self.hw.world, "person_names", lambda: list(self.cfg.people))()
        skills = {n: s.description for n, s in REGISTRY.items() if s.available(self.cfg, self.hw)[0]}
        self.agent = GiorgioAgent(self.cfg.agent, people, skills)
        self.decision = self.safety.last
        self.say_text, self.say_t = "", -10.0
        self.ticks = 0
        self._emit("system", f"Giorgio up: configuration '{self.cfg.title}', backend {backend}")

    # ------------------------------------------------------------------ time & events
    def now(self) -> float:
        if self.hw.engine is not None:
            return self.hw.engine.time
        return time.monotonic() - self._t0

    def _emit(self, kind: str, text: str) -> None:
        if kind == "say":
            self.say_text, self.say_t = text, self.now()
        self.events.append({"t": round(self.now(), 2), "kind": kind, "text": text})
        log.info("[%s] %s", kind, text)

    # ------------------------------------------------------------------ control loop
    def tick(self) -> None:
        now = self.now()
        self.decision = self.safety.step(now, self.hw)
        self.hw.face.show_safety(int(self.decision.zone))
        if self.safety.software_stop_active and self.mission.state != ManagerState.STOPPED:
            self.mission.software_stop("operator")
            self.hw.base.stop()
            for a in self.hw.arms.values():
                a.stop()
            self._emit("safety", "SOFTWARE STOP: tasks cancelled, motion halted (not a safety function)")
        bat = self.hw.battery.status()
        if self.mission.state != ManagerState.STOPPED:
            ed = self.energy.update(bat, self.mission.idle, self.mission.has_pending("dock_charge"))
            if ed.action == EnergyAction.CHARGE:
                self._emit("energy", f"{ed.reason}: going to charge")
                self.mission.submit("Auto-charge", [SkillCall("dock_charge")], source="energy", priority=10)
            elif ed.action == EnergyAction.ABORT_AND_CHARGE:
                self._emit("energy", f"{ed.reason}: aborting current task to charge")
                self.mission.abort_current(ed.reason)
                self.mission.submit("Emergency charge", [SkillCall("dock_charge")], source="energy", priority=100)
        self.mission.tick()
        if self.hw.engine is not None:
            for t, kind, text in self.hw.engine.events:
                if kind == "say":
                    self.say_text, self.say_t = text, self.now()
                self.events.append({"t": round(t, 2), "kind": kind, "text": text})
            self.hw.engine.events.clear()
        self.hw.advance(CONTROL_DT)
        self.ticks += 1

    def run_for(self, seconds: float) -> None:
        n = int(round(seconds / CONTROL_DT))
        for _ in range(n):
            self.tick()

    def run_until(self, pred: Callable[[], bool], timeout_s: float) -> bool:
        t_end = self.now() + timeout_s
        while self.now() < t_end:
            if pred():
                return True
            self.tick()
        return pred()

    def _energy_guard(self, skill: str) -> tuple[bool, str]:
        return self.energy.guard(skill, self.hw.battery.status())

    # ------------------------------------------------------------------ commands (operator / API)
    def submit(self, skill: str, args: Optional[dict[str, Any]] = None, title: str | None = None, source: str = "operator") -> Task:
        call = SkillCall(skill, dict(args or {}))
        return self.mission.submit(title or call.label(), [call], source=source)

    def chat(self, text: str) -> dict[str, Any]:
        self.hw.face.set_expression("thinking", hold_s=1.2)
        reply = self.agent.handle(text, self.snapshot_light)
        task = None
        if reply.stop:
            self.software_stop("voice/chat command")
        elif reply.plan:
            task = self.mission.submit(text[:60], reply.plan, source=f"agent:{reply.engine}")
            if task.status.value == "failed":
                reply.say = f"I can't do that here: {task.message}"
                self.agent.chat[-1]["text"] = reply.say
        if reply.say:
            self._emit("say", reply.say)
        return {"say": reply.say, "engine": reply.engine, "latency_ms": round(reply.latency_ms, 2),
                "plan": [c.label() for c in reply.plan], "task": task.to_dict() if task else None}

    def software_stop(self, reason: str = "operator") -> None:
        self.safety.request_software_stop(reason)

    def reset(self) -> dict[str, Any]:
        if hasattr(self.hw.relay, "press_reset"):      # sim: the blue reset button on the PNOZ
            self.hw.relay.press_reset()
        self.decision = self.safety.step(self.now(), self.hw)
        ok = self.safety.reset_software_stop()
        if ok:
            self.mission.resume()
            self._emit("safety", "software stop released")
        return {"ok": ok, "reason": "" if ok else "protective condition still active - clear the area first"}

    # ------------------------------------------------------------------ status
    def snapshot_light(self) -> dict[str, Any]:
        b = self.hw.battery.status()
        return {"battery": {"soc": b.soc, "charging": b.charging}, "safety": {"zone": self.decision.zone.name},
                "mission": {"current": self.mission.current.title if self.mission.current else None}}

    def _scan_points(self) -> list[list[float]]:
        pts: list[list[float]] = []
        for s in self.hw.scanners.values():
            try:
                f = s.read()
            except NotImplementedError:
                continue
            for i in range(0, len(f.ranges), 3):
                r = f.ranges[i]
                if r >= 7.9:
                    continue
                a = f.yaw + f.angle_min + i * f.angle_inc
                pts.append([round(f.origin_xy[0] + r * math.cos(a), 2), round(f.origin_xy[1] + r * math.sin(a), 2)])
        return pts

    def snapshot(self) -> dict[str, Any]:
        hw = self.hw
        b = hw.battery.status()
        base = hw.base.status()
        frames = [s.read() for s in hw.scanners.values()]
        radii = next((f.field_radii for f in frames if f.field_radii), None) or (self.cfg.safety.protective_distance_m, 0.0)
        relay = hw.relay.status()
        mode = self.mission.state.value
        if self.mission.state == ManagerState.STOPPED:
            mode = "software stop"
        elif self.decision.zone == Zone.PROTECTIVE and self.mission.current is not None:
            mode = "hold (safety)"
        elif b.charging:
            mode = "charging" if self.mission.idle else mode
        out = {
            "t": round(self.now(), 2), "backend": self.backend,
            "config": {"name": self.cfg.name, "title": self.cfg.title, "hands": self.cfg.hands, "modules": self.cfg.modules},
            "mode": mode,
            "base": {"x": round(base.pose.x, 3), "y": round(base.pose.y, 3), "theta": round(base.pose.theta, 3),
                     "v": round(base.v, 3), "w": round(base.w, 3), "navigating": base.navigating, "speed_scale": round(base.speed_scale, 2)},
            "battery": {"soc": round(b.soc, 4), "voltage": b.voltage, "current": b.current, "power": b.power,
                        "charging": b.charging, "capacity_wh": b.capacity_wh,
                        "autonomy_h": round(self.energy.autonomy_h(b), 1)},
            "safety": {**self.decision.to_dict(), "field_case": frames[0].field_case if frames else "?",
                       "protective_r": round(radii[0], 2), "warning_r": round(radii[1], 2),
                       "iso13855_s_m": round(self.cfg.safety.protective_distance_m, 2),
                       "stops": self.safety.stops, "slowdowns": self.safety.slowdowns,
                       "relay": {"estop_ok": relay.estop_ok, "scanners_ok": relay.scanners_ok, "drives_enabled": relay.drives_enabled,
                                 "arm_power": relay.arm_power, "reset_required": relay.reset_required},
                       "scan": self._scan_points()},
            "arms": {s: a.status().__dict__ for s, a in hw.arms.items()},
            "grippers": {s: g.status().__dict__ for s, g in hw.grippers.items()},
            "dock": hw.dock.status().__dict__,
            "face": hw.face.state(),
            "coffee": hw.coffee.status().__dict__ if hw.coffee else None,
            "say": self.say_text if self.now() - self.say_t < 6.0 else "",
            "mission": self.mission.snapshot(),
            "chat": self.agent.chat[-20:],
            "events": list(self.events)[-60:],
            "skills": [{"name": n, "description": s.description, "params": s.params,
                        "available": s.available(self.cfg, hw)[0], "why": s.available(self.cfg, hw)[1]}
                       for n, s in REGISTRY.items()],
            "cameras": list(hw.cameras),
            "llm_enabled": self.agent.llm.available,
        }
        if hw.engine is not None:
            g = hw.engine.g
            out["sim"] = {"people": [[round(float(p.pos[0]), 2), round(float(p.pos[1]), 2)] for p in g["people"] if p.active],
                          "onboard": hw.engine.onboard_count(), "inserted": int(g["stats"]["inserted"]),
                          "hw_estop": hw.engine.hw_estop}
        return out

    def close(self) -> None:
        if self.hw.engine is not None:
            self.hw.engine.close()
