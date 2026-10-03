"""MuJoCo backend: an adapter around the existing monolithic simulation ``giorgio_v5.py``.

We do NOT rewrite the physics, the scene, the IK, the clash-aware planner, the people or the
v5 skills. ``giorgio_v5.py`` is a script (argparse + global state + a main loop at the bottom), so
it cannot be imported directly. Following the same technique already used by ``giorgio_sort.py``,
we execute its source *up to* the ``# ---- uscite`` (outputs / main loop) marker inside a private
module namespace, then drive it from here with our own control step.

What the adapter replaces from v5:
  * ``control_step``  -> :meth:`SimEngine._physics_step` (same order of operations, but the speed
    scaling comes from giorgio_os' SafetySupervisor instead of v5's inline logic, and the base/arm
    scalings are separate);
  * ``agent_step`` / ``auto_charge`` / ``system2`` (Claude CLI) -> giorgio_os mission manager,
    energy manager and agent. ``system2`` is replaced by a stub so the sim can never call out.
  * ``log`` / ``ag_say`` -> forwarded to giorgio_os logging / event bus.

Everything here must be called from ONE thread (MuJoCo EGL renderers are bound to it).
"""
from __future__ import annotations

import contextlib
import io
import logging
import math
import os
import sys
import types
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from ...types import ActionHandle, ActionState, Pose2D

log = logging.getLogger("giorgio.sim")

SIM_DIR = Path(os.environ.get("GIORGIO_SIM_DIR", Path(__file__).resolve().parents[4]))
V5_FILE = SIM_DIR / "giorgio_v5.py"
OUTPUT_MARKER = "# ---------------------------------------------------------------- uscite"

FACE_CODES = {0: "neutral", 1: "happy", 2: "coffee", 3: "stop", 4: "thinking", 5: "love", 6: "attentive", 7: "charging"}
FACE_CODE_OF = {v: k for k, v in FACE_CODES.items()}
FACE_CODE_OF["wave"] = 1


def load_v5_namespace(soc: float = 0.85, hands: str = "gripper", humans: bool = True, seed: int = 3,
                      look: str = "gb", quiet: bool = True) -> dict[str, Any]:
    """Execute giorgio_v5.py (minus its main loop) in a fresh namespace and return it."""
    os.environ.setdefault("MUJOCO_GL", "egl")
    src = V5_FILE.read_text()
    if OUTPUT_MARKER not in src:
        raise RuntimeError(f"{V5_FILE}: marker '{OUTPUT_MARKER}' not found - giorgio_v5.py layout changed")
    pre, post = src.split(OUTPUT_MARKER, 1)
    # the scene overlay (scanner rays, fields, planned path) lives after the marker: take just that function
    i0 = post.find("def draw(scn):")
    i1 = post.find("\ndef ", i0 + 10)
    if i0 >= 0:
        pre += "\n\n" + post[i0:i1 if i1 > 0 else None]
    argv = ["giorgio_v5.py", "--agent", "1e9:noop", "--soc", str(soc), "--hands", hands, "--seed", str(seed), "--look", look]
    if not humans:
        argv.append("--no_humans")
    mod = types.ModuleType("giorgio_v5_sim")
    mod.__file__ = str(V5_FILE)
    ns = mod.__dict__
    old_argv, old_path = sys.argv, list(sys.path)
    sys.argv = argv
    if str(SIM_DIR) not in sys.path:
        sys.path.insert(0, str(SIM_DIR))
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf) if quiet else contextlib.nullcontext():
            exec(compile(pre, str(V5_FILE), "exec"), ns)
    finally:
        sys.argv = old_argv
        sys.path[:] = old_path if str(SIM_DIR) in old_path else old_path + [str(SIM_DIR)]
    ns["AG"]["pending"].clear()                           # the dummy --agent command
    return ns


# v5 speaks Italian; the console is in English. Regex -> replacement (unknown lines pass through unchanged).
_EN = [
    (r"^Aggancio non riuscito: chiamo assistenza\.$", "Docking failed: calling for assistance."),
    (r"^Buon caffe', (\w+)!$", r"Enjoy your coffee, \1!"),
    (r"^Caffe' pronto!$", "Coffee ready!"),
    (r"^Carico i flaconi dal banco A\.$", "Loading the bottles from bench A."),
    (r"^Ecco a te!$", "Here you go!"),
    (r"^Arrivo, (\w+)!$", r"Coming, \1!"),
    (r"^Ecco il tuo caffe', (\w+)\.$", r"Here is your coffee, \1."),
    (r"^Non conosco '(.*)'\.$", r"I don't know '\1'."),
    (r"^Il banco A e' vuoto: serve un rifornimento\.$", "Bench A is empty: needs a refill."),
    (r"^In carica: contatti chiusi, 48 V\.$", "Charging: contacts closed, 48 V."),
    (r"^Preparo il caffe'.*$", "Making coffee: cup on the shuttle, pressing the button."),
    (r"^Vado alla stazione di ricarica\.$", "Going to the charging station."),
    (r"^a bordo (\d+) flaconi.*$", r"\1 bottles on board"),
    (r"^AMR agganciato a B: (.*) mm, (.*) gradi$", r"docked at B: \1 mm, \2 deg"),
    (r"^(right|left): flacone INSERITO \((.*) mm dal centro del foro\)$", r"\1: bottle INSERTED (\2 mm from hole centre)"),
    (r"^(right|left): flacone NON INSERITO \((.*) mm dal centro del foro\)$", r"\1: bottle NOT inserted (\2 mm from hole centre)"),
    (r"^visione: (\d+) flaconi sul banco A, errore medio (.*) mm$", r"vision: \1 bottles on bench A, mean error \2 mm"),
    (r"^visione: (\d+) fori liberi, errore medio (.*) mm$", r"vision: \1 free holes, mean error \2 mm"),
]


def to_english(text: str) -> str:
    import re
    for pat, rep in _EN:
        if re.match(pat, text):
            return re.sub(pat, rep, text)
    return text


class _Action:
    """A base-level action executed by the engine (navigation, docking, v5 choreography)."""

    def __init__(self, handle: ActionHandle):
        self.handle = handle

    def step(self, k: float) -> bool:    # pragma: no cover - interface
        raise NotImplementedError

    def on_cancel(self) -> None:
        pass


class SimEngine:
    """Owns the v5 namespace, steps physics, renders cameras, and hosts long-running actions."""

    CONTROL_DT = 0.02

    def __init__(self, soc: float = 0.85, hands: str = "gripper", humans: bool = True, seed: int = 3, look: str = "gb",
                 quiet: bool = True):
        self.g = load_v5_namespace(soc=soc, hands=hands, humans=humans, seed=seed, look=look, quiet=quiet)
        g = self.g
        self.m, self.d = g["m"], g["d"]
        self.DT: float = float(g["DT"])
        self.hands = hands
        self.k_arm_cmd = self.k_base_cmd = 1.0
        self.k_arm = self.k_base = 1.0
        self.display_zone = 0
        self.scan_stamp = -1.0
        self.base_action: Optional[_Action] = None
        self.watchers: list[tuple[ActionHandle, Callable[[], Optional[tuple[bool, str]]]]] = []
        self.timers: list[tuple[float, Callable[[], None]]] = []
        self.face_override: tuple[int, float] = (-1, -1.0)
        self.events: list[tuple[float, str, str]] = []           # (sim time, kind, text) - drained by the runtime
        self.hw_estop = False
        self.people_div = 5
        self._renderers: dict[tuple[int, int], Any] = {}
        self._chase_cam = None
        self._hook_v5()
        if g["mission"]["state"] == "settle":
            g["teach_contour"](); g["mission"]["state"] = "agente"

    # ------------------------------------------------------------------ v5 hooks
    def _hook_v5(self) -> None:
        g = self.g
        v5_log = g["log"]

        def _log(msg: str) -> None:
            g["mission"]["log"] = (g["mission"]["log"] + [msg])[-4:]
            self.events.append((self.time, "sim", to_english(str(msg))))

        def _say(txt: str) -> None:
            g["AG"]["say"], g["AG"]["say_t"] = txt, self.d.time
            self.events.append((self.time, "say", to_english(str(txt))))

        def _no_llm(text: str) -> dict:     # never shell out to the claude CLI from the sim
            return {"say": "", "plan": []}

        g["log"], g["ag_say"], g["system2"] = _log, _say, _no_llm
        self._v5_log = v5_log

    # ------------------------------------------------------------------ time
    @property
    def time(self) -> float:
        return float(self.d.time)

    def advance(self, dt: float) -> None:
        n = max(1, int(round(dt / self.DT)))
        for _ in range(n):
            self._physics_step()
        self._check_watchers()

    def after(self, delay_s: float, fn: Callable[[], None]) -> None:
        self.timers.append((self.time + delay_s, fn))

    def watch(self, handle: ActionHandle, fn: Callable[[], Optional[tuple[bool, str]]]) -> ActionHandle:
        handle.state = ActionState.RUNNING
        self.watchers.append((handle, fn))
        return handle

    def _check_watchers(self) -> None:
        keep = []
        for h, fn in self.watchers:
            if h.done:
                continue
            r = fn()
            if r is None:
                keep.append((h, fn))
            elif r[0]:
                h.succeed(message=r[1])
            else:
                h.fail(r[1])
        self.watchers = keep
        people = self.g["people"]
        for p in list(people):            # v5 people loop their path: drop the intruder once it is back at its start
            info = getattr(p, "giorgio_intruder", None)
            if info is None:
                continue
            if np.linalg.norm(p.pos - info["near"]) < 0.3:
                info["arrived"] = True
            elif info["arrived"] and np.linalg.norm(p.pos - info["far"]) < 0.4:
                people.remove(p)
                self.events.append((self.time, "sim", "the person left"))
        due = [t for t in self.timers if t[0] <= self.time]
        self.timers = [t for t in self.timers if t[0] > self.time]
        for _, fn in due:
            fn()

    # ------------------------------------------------------------------ the control step (replaces v5 control_step)
    def _physics_step(self) -> None:
        g, m, d, DT = self.g, self.m, self.d, self.DT
        t = d.time
        d.qfrc_applied[g["GC_DOFS"]] = np.clip(d.qfrc_bias[g["GC_DOFS"]], -g["GC_TAU"], g["GC_TAU"])
        st = g["state"]
        st["zone"] = self.display_zone                       # eyes / LED strip colour follow the supervisor
        if int(round(t / DT)) % 16 == 0:
            g["face_step"]()
            code, until = self.face_override
            if code >= 0 and t < until:
                g["FACE"][0] = code
        for p in g["people"]:
            p.step(t, DT)
        if int(round(t / DT)) % self.people_div == 0:      # mocap bodies at 100 Hz: plenty for walking people
            g["place_people"]()
        st["scan_t"] += DT
        if st["scan_t"] >= 0.03 or not st["hits"]:
            st["scan_t"] = 0.0
            _, st["hits"] = g["safety"]()                     # device-level field evaluation (emulates the nanoScan3)
            self.scan_stamp = t
        # speed ramps toward the supervisor's command (stop: 0.3 s ramp = SS1-like controlled stop)
        self.k_arm = self._ramp(self.k_arm, self.k_arm_cmd)
        self.k_base = self._ramp(self.k_base, self.k_base_cmd)
        st["k"] = min(self.k_arm, self.k_base)
        g["cup_hold_follow"]()
        g["agent_people"]()
        if self.base_action is not None:
            try:
                done = self.base_action.step(self.k_base)
            except Exception as e:                           # never let a v5 exception kill the loop
                log.exception("sim action failed")
                self.base_action.handle.fail(f"sim exception: {e}")
                done = True
            if done:
                self.base_action = None
        if g["mission"]["state"] in ("look_A", "load_A", "look_B", "unload_B"):
            g["mission_step"](self.k_arm)
        if not g["mission"]["state"].startswith("drive"):
            g["hold_step"]()
        g["teach_step"]()
        for a in g["arms"].values():
            a.step(DT, self.k_arm)
            a.apply()
        g["clips_step"](); g["handover_step"]()
        g["mujoco"].mj_step(m, d)
        g["energy_step"]()

    def _ramp(self, k: float, cmd: float) -> float:
        return max(cmd, k - self.DT / 0.3) if cmd < k else min(cmd, k + self.DT / 0.6)

    # ------------------------------------------------------------------ base actions
    def start_base_action(self, action: _Action) -> ActionHandle:
        if self.base_action is not None and not self.base_action.handle.done:
            self.cancel_base_action("preempted")
        self.base_action = action
        action.handle.state = ActionState.RUNNING
        action.handle._cancel_cb = lambda h: self.cancel_base_action("canceled")
        return action.handle

    def cancel_base_action(self, why: str = "canceled") -> None:
        a = self.base_action
        if a is None:
            return
        self.base_action = None
        a.on_cancel()
        g = self.g
        g["mission"]["route"] = None
        if g["mission"]["state"].startswith("drive") or g["mission"]["state"] in ("look_A", "load_A", "look_B", "unload_B"):
            g["mission"]["state"] = "agente"
        g["AG"]["approach"] = False
        a.handle.state = ActionState.CANCELED
        a.handle.message = why

    def stop_arms(self) -> None:
        for a in self.g["arms"].values():
            a.segs, a.queue = [], []

    # ------------------------------------------------------------------ helpers used by drivers/services
    def base_pose(self) -> Pose2D:
        x, y, th = self.g["base_pose"]()
        return Pose2D(float(x), float(y), float(th))

    def soc(self) -> float:
        return float(self.g["soc"]())

    def set_soc(self, soc: float) -> None:
        bat = self.g["BAT"]
        bat["E"] = float(np.clip(soc, 0.0, 1.0)) * bat["cap"]

    def onboard_count(self) -> int:
        return int(self.g["onboard_count"]())

    def spawn_intruder(self, stop_dist: float = 0.9, hold_s: float = 3.0, side_deg: float = 0.0) -> None:
        """Test/demo helper: a person walks up to the robot, waits ``hold_s`` and walks away."""
        g = self.g
        x, y, th = g["base_pose"]()
        a = th + math.radians(side_deg)
        u = np.array([math.cos(a), math.sin(a)])
        far = np.array([x, y]) + 4.0 * u + np.array([-u[1], u[0]]) * 1.5
        near = np.array([x, y]) + stop_dist * u
        p = g["spawn"](0, [far, near, near, far], 1.2, (1.0, 0.78, 0.05), waits={2: hold_s}, look="operatore")
        p.giorgio_intruder = {"near": near, "far": far, "arrived": False}
        self.events.append((self.time, "sim", "a person is walking towards Giorgio"))

    # ------------------------------------------------------------------ rendering
    def _renderer(self, w: int, h: int):
        key = (w, h)
        if key not in self._renderers:
            self._renderers[key] = self.g["mujoco"].Renderer(self.m, h, w)
        return self._renderers[key]

    def camera_names(self) -> list[str]:
        return [self.m.camera(i).name for i in range(self.m.ncam)]

    def render(self, camera: str, width: int = 640, height: int = 400, overlay: bool = True) -> np.ndarray:
        mj = self.g["mujoco"]
        r = self._renderer(width, height)
        if camera == "chase":
            if self._chase_cam is None:
                c = mj.MjvCamera(); c.distance = 3.6; c.elevation = -24; c.azimuth = 205
                b = self.d.body("amr").xpos
                c.lookat[:] = [b[0], b[1], 0.8]
                self._chase_cam = c
            c = self._chase_cam
            b = self.d.body("amr").xpos
            c.lookat[:] = 0.8 * np.array(c.lookat) + 0.2 * np.array([b[0], b[1], 0.8])
            r.update_scene(self.d, c)
            if overlay:
                self.g["draw"](r.scene)
        elif camera == "top":
            c = mj.MjvCamera(); c.distance = 11.0; c.elevation = -89; c.azimuth = 90; c.lookat[:] = [-1.4, 0.2, 0.0]
            r.update_scene(self.d, c)
            if overlay:
                self.g["draw"](r.scene)
        else:
            r.update_scene(self.d, camera)
        return r.render().copy()

    def close(self) -> None:
        v = self.g.get("vision")
        for r in [getattr(v, "rgb", None), getattr(v, "dep", None)] + list(self._renderers.values()):
            if r is None:
                continue
            with contextlib.suppress(Exception):
                r.close()
        self._renderers.clear()
        if v is not None:
            v.rgb = v.dep = None


# ---------------------------------------------------------------------- concrete actions
class NavigateAction(_Action):
    """Plan (A* + Chaikin smoothing) and follow (pure pursuit, jerk-limited) with v5's own code."""

    def __init__(self, engine: SimEngine, goal: Pose2D, handle: ActionHandle):
        super().__init__(handle)
        self.e, self.goal, self.phase = engine, goal, 0

    def step(self, k: float) -> bool:
        g = self.e.g
        if self.phase == 0:
            g["mission"]["route"] = g["route_pose"](np.array(self.goal.as_list()))
            g["FIELDS"]["mode"] = "marcia"; g["mission"]["state"] = "drive_ag"; self.phase = 1
            return False
        if g["drive_step"](k):
            g["teach_contour"](); g["mission"]["state"] = "agente"
            err = self.e.base_pose().dist(self.goal)
            self.handle.feedback["final_error_m"] = err
            if err < 0.10:
                self.handle.succeed(message=f"arrived ({1000 * err:.0f} mm)")
            else:
                self.handle.fail(f"stopped {err:.2f} m from goal")
            return True
        self.handle.feedback["distance_m"] = self.e.base_pose().dist(self.goal)
        return False


class LegacySkillAction(_Action):
    """Run one of v5's proven choreographies (docking, coffee, hand-over, tray load/unload)."""

    def __init__(self, engine: SimEngine, spec: dict[str, Any], handle: ActionHandle,
                 success: Optional[Callable[[], tuple[bool, str]]] = None, timeout_s: float = 240.0):
        super().__init__(handle)
        self.e, self.spec = engine, spec
        self.sk = engine.g["Skill"](dict(spec))
        self.success = success
        self.t0, self.timeout = engine.time, timeout_s

    def step(self, k: float) -> bool:
        if self.e.time - self.t0 > self.timeout:
            self.handle.fail("timeout"); self.on_cancel(); return True
        if self.sk.step(k):
            ok, msg = self.success() if self.success else (True, "done")
            if ok:
                self.handle.succeed(message=msg)
            else:
                self.handle.fail(msg)
            return True
        self.handle.feedback["phase"] = self.sk.phase
        return False

    def on_cancel(self) -> None:
        g = self.e.g
        g["BAT"]["heater"] = False
        g["AG"]["mode"] = "lavoro"
