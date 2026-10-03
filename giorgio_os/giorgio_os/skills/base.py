"""Skill framework: skills are Python generators ticked by the mission manager.

A skill's ``run(ctx, **args)`` yields once per control tick while it waits, and returns a short
result string. Raising :class:`SkillError` fails the skill. Cancelling closes the generator and
cancels every device action the skill started (tracked through ``ctx.track``).

Skills see a :class:`SkillContext`: the HAL drivers, services and a few helpers. They do NOT see
the safety supervisor (they cannot change speed limits) nor the agent.
"""
from __future__ import annotations

import enum
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional

from ..config import RobotConfig
from ..hal.interfaces import HardwareSet
from ..types import ActionHandle, Pose2D

log = logging.getLogger("giorgio.skills")

SkillGen = Generator[None, None, str]


class SkillError(RuntimeError):
    pass


class SkillStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class SkillContext:
    def __init__(self, hw: HardwareSet, cfg: RobotConfig, now: Callable[[], float],
                 emit: Callable[[str, str], None]):
        self.hw, self.cfg, self._now, self._emit = hw, cfg, now, emit
        self._handles: list[ActionHandle] = []

    def child(self) -> "SkillContext":
        """Fresh context (own handle tracking) for one skill run."""
        return SkillContext(self.hw, self.cfg, self._now, self._emit)

    # helpers ---------------------------------------------------------------
    def now(self) -> float:
        return self._now()

    def say(self, text: str) -> None:
        self._emit("say", text)

    def event(self, text: str) -> None:
        self._emit("skill", text)

    def track(self, h: ActionHandle) -> ActionHandle:
        self._handles.append(h)
        return h

    def cancel_tracked(self) -> None:
        for h in self._handles:
            if not h.done:
                h.cancel()
        self._handles.clear()

    def wait(self, h: ActionHandle, timeout_s: float | None = None, what: str = "") -> Generator[None, None, ActionHandle]:
        self.track(h)
        t0 = self.now()
        while not h.done:
            if timeout_s is not None and self.now() - t0 > timeout_s:
                h.cancel()
                raise SkillError(f"{what or h.name}: timeout after {timeout_s:.0f} s")
            yield
        if not h.ok:
            raise SkillError(f"{what or h.name}: {h.state.value} - {h.message}")
        return h

    def sleep(self, seconds: float) -> Generator[None, None, None]:
        t0 = self.now()
        while self.now() - t0 < seconds:
            yield

    def robot_frame(self, xy: tuple[float, float]) -> tuple[float, float]:
        """World xy -> robot frame (x forward, y left)."""
        p: Pose2D = self.hw.base.status().pose
        dx, dy = xy[0] - p.x, xy[1] - p.y
        c, s = math.cos(p.theta), math.sin(p.theta)
        return c * dx + s * dy, -s * dx + c * dy


@dataclass
class SkillSpec:
    name: str
    description: str
    fn: Callable[..., SkillGen]
    params: dict[str, str] = field(default_factory=dict)
    requires_modules: tuple[str, ...] = ()
    requires_hands: tuple[str, ...] = ()        # e.g. ("parallel",)
    requires_choreo: bool = False

    def available(self, cfg: RobotConfig, hw: Optional[HardwareSet] = None) -> tuple[bool, str]:
        if cfg.skills and self.name not in cfg.skills:
            return False, f"'{self.name}' is not enabled in configuration '{cfg.name}'"
        for m in self.requires_modules:
            if not cfg.has(m):
                return False, f"'{self.name}' needs the {m} module (not fitted in '{cfg.name}')"
        if hw is not None and self.requires_hands:
            kinds = {g.kind for g in hw.grippers.values()}
            if not kinds & set(self.requires_hands):
                return False, f"'{self.name}' needs {'/'.join(self.requires_hands)} end effectors"
        if hw is not None and self.requires_choreo:
            if hw.choreo is None or self.name not in hw.choreo.available():
                return False, f"'{self.name}' is not yet available on the {hw.backend} backend"
        return True, ""


REGISTRY: dict[str, SkillSpec] = {}


def skill(name: str, description: str, params: dict[str, str] | None = None, requires_modules: tuple[str, ...] = (),
          requires_hands: tuple[str, ...] = (), requires_choreo: bool = False):
    def deco(fn: Callable[..., SkillGen]) -> Callable[..., SkillGen]:
        REGISTRY[name] = SkillSpec(name, description, fn, params or {}, requires_modules, requires_hands, requires_choreo)
        return fn
    return deco


class SkillRunner:
    """Wraps one running skill generator."""

    def __init__(self, spec: SkillSpec, ctx: SkillContext, args: dict[str, Any]):
        self.spec, self.ctx, self.args = spec, ctx, args
        self.status = SkillStatus.RUNNING
        self.message = ""
        self.t0 = ctx.now()
        try:
            self._gen = spec.fn(ctx, **args)
        except TypeError as e:
            self._gen = None
            self.status, self.message = SkillStatus.FAILED, f"bad arguments: {e}"

    def tick(self) -> SkillStatus:
        if self.status != SkillStatus.RUNNING or self._gen is None:
            return self.status
        try:
            next(self._gen)
        except StopIteration as stop:
            self.status, self.message = SkillStatus.SUCCEEDED, str(stop.value or "done")
        except SkillError as e:
            self.ctx.cancel_tracked()
            self.status, self.message = SkillStatus.FAILED, str(e)
        except Exception as e:  # a bug in a skill must not take the robot down
            log.exception("skill %s crashed", self.spec.name)
            self.ctx.cancel_tracked()
            self.status, self.message = SkillStatus.FAILED, f"internal error: {e!r}"
        return self.status

    def cancel(self, why: str = "canceled") -> None:
        if self.status != SkillStatus.RUNNING:
            return
        if self._gen is not None:
            self._gen.close()
        self.ctx.cancel_tracked()
        self.status, self.message = SkillStatus.CANCELED, why
