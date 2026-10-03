"""Task / mission manager.

A *task* is an ordered list of skill calls (a tiny sequence behaviour tree: Sequence[Skill...]) with a
priority and a source (operator UI, agent, energy manager). The manager is a small explicit state
machine:

    IDLE --submit--> RUNNING --task done--> IDLE
      ^                 |  \\--software stop--> STOPPED --reset--> IDLE
      |                 \\--abort_and_charge (energy)--> RUNNING(charge task)
      \\-------------------------------------------------------------/

Safety is NOT handled here: when the supervisor scales speed to 0 the skills simply stop moving
(the manager shows HOLD). The manager only reacts to the *software* stop by cancelling.
"""
from __future__ import annotations

import enum
import itertools
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..skills.base import REGISTRY, SkillContext, SkillRunner, SkillStatus

log = logging.getLogger("giorgio.mission")


class ManagerState(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class SkillCall:
    skill: str
    args: dict[str, Any] = field(default_factory=dict)

    def label(self) -> str:
        a = ", ".join(f"{v}" for v in self.args.values())
        return f"{self.skill}({a})"


_task_ids = itertools.count(1)


@dataclass
class Task:
    title: str
    steps: list[SkillCall]
    source: str = "operator"
    priority: int = 0
    id: int = field(default_factory=lambda: next(_task_ids))
    status: TaskStatus = TaskStatus.QUEUED
    step_index: int = 0
    message: str = ""
    created: float = 0.0
    started: Optional[float] = None
    finished: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "source": self.source, "priority": self.priority,
                "status": self.status.value, "step": self.step_index, "steps": [s.label() for s in self.steps],
                "message": self.message, "created": self.created, "started": self.started, "finished": self.finished}


GuardFn = Callable[[str], tuple[bool, str]]


class TaskManager:
    def __init__(self, ctx: SkillContext, guard: Optional[GuardFn] = None, history: int = 30):
        self.ctx = ctx
        self.guard = guard
        self.state = ManagerState.IDLE
        self.queue: list[Task] = []
        self.current: Optional[Task] = None
        self.runner: Optional[SkillRunner] = None
        self.history: list[Task] = []
        self._hist_n = history

    # ------------------------------------------------------------------ API
    def validate(self, steps: list[SkillCall]) -> Optional[str]:
        for s in steps:
            spec = REGISTRY.get(s.skill)
            if spec is None:
                return f"unknown skill '{s.skill}'"
            ok, why = spec.available(self.ctx.cfg, self.ctx.hw)
            if not ok:
                return why
        return None

    def submit(self, title: str, steps: list[SkillCall], source: str = "operator", priority: int = 0) -> Task:
        t = Task(title, steps, source, priority, created=self.ctx.now())
        err = self.validate(steps)
        if err:
            t.status, t.message, t.finished = TaskStatus.FAILED, err, self.ctx.now()
            self._archive(t)
            return t
        # stable priority insert (higher first)
        i = next((k for k, q in enumerate(self.queue) if q.priority < priority), len(self.queue))
        self.queue.insert(i, t)
        self.ctx.event(f"task #{t.id} queued: {title}")
        return t

    def cancel(self, task_id: int, why: str = "canceled by operator") -> bool:
        if self.current is not None and self.current.id == task_id:
            self._finish_current(TaskStatus.CANCELED, why)
            return True
        for t in list(self.queue):
            if t.id == task_id:
                self.queue.remove(t)
                t.status, t.message, t.finished = TaskStatus.CANCELED, why, self.ctx.now()
                self._archive(t)
                return True
        return False

    def cancel_all(self, why: str) -> None:
        if self.current is not None:
            self._finish_current(TaskStatus.CANCELED, why)
        for t in self.queue:
            t.status, t.message, t.finished = TaskStatus.CANCELED, why, self.ctx.now()
            self._archive(t)
        self.queue.clear()

    def abort_current(self, why: str) -> None:
        if self.current is not None:
            self._finish_current(TaskStatus.FAILED, why)

    def software_stop(self, why: str) -> None:
        """Cancel the running task; keep the queue; refuse to start anything until ``resume``."""
        if self.current is not None:
            self._finish_current(TaskStatus.CANCELED, f"software stop: {why}")
        self.state = ManagerState.STOPPED

    def resume(self) -> None:
        if self.state == ManagerState.STOPPED:
            self.state = ManagerState.IDLE

    @property
    def idle(self) -> bool:
        return self.current is None and not self.queue

    def has_pending(self, skill: str) -> bool:
        tasks = ([self.current] if self.current else []) + self.queue
        return any(s.skill == skill for t in tasks for s in t.steps[t.step_index if t is self.current else 0:])

    # ------------------------------------------------------------------ tick
    def tick(self) -> None:
        if self.state == ManagerState.STOPPED:
            return
        if self.current is None:
            if not self.queue:
                self.state = ManagerState.IDLE
                return
            self.current = self.queue.pop(0)
            self.current.status, self.current.started = TaskStatus.RUNNING, self.ctx.now()
            self.state = ManagerState.RUNNING
            self.ctx.event(f"task #{self.current.id} started: {self.current.title}")
            self._start_step()
            if self.current is None:
                return
        if self.runner is None:
            return
        st = self.runner.tick()
        if st == SkillStatus.RUNNING:
            return
        t = self.current
        if st == SkillStatus.SUCCEEDED:
            self.ctx.event(f"{t.steps[t.step_index].label()}: {self.runner.message}")
            t.step_index += 1
            if t.step_index >= len(t.steps):
                self._finish_current(TaskStatus.SUCCEEDED, self.runner.message)
            else:
                self._start_step()
        else:
            self._finish_current(TaskStatus.FAILED if st == SkillStatus.FAILED else TaskStatus.CANCELED, self.runner.message)

    def _start_step(self) -> None:
        t = self.current
        assert t is not None
        call = t.steps[t.step_index]
        if self.guard is not None:
            ok, why = self.guard(call.skill)
            if not ok and why == "charge_first":
                self.ctx.say("Battery is low: I'll charge first, then I'll do it.")
                t.steps.insert(t.step_index, SkillCall("dock_charge"))
                call = t.steps[t.step_index]
            elif not ok:
                self._finish_current(TaskStatus.FAILED, why)
                return
        self.runner = SkillRunner(REGISTRY[call.skill], self.ctx.child(), dict(call.args))

    def _finish_current(self, status: TaskStatus, msg: str) -> None:
        t = self.current
        if t is None:
            return
        if self.runner is not None and self.runner.status == SkillStatus.RUNNING:
            self.runner.cancel(msg)
        t.status, t.message, t.finished = status, msg, self.ctx.now()
        self.ctx.event(f"task #{t.id} {status.value}: {msg}")
        self._archive(t)
        self.current, self.runner = None, None
        if self.state == ManagerState.RUNNING:
            self.state = ManagerState.IDLE

    def _archive(self, t: Task) -> None:
        self.history = ([t] + self.history)[: self._hist_n]

    def snapshot(self) -> dict[str, Any]:
        cur = None
        if self.current is not None:
            cur = self.current.to_dict()
            if self.runner is not None:
                cur["skill"] = self.current.steps[self.current.step_index].label()
                cur["skill_elapsed"] = round(self.ctx.now() - self.runner.t0, 1)
        return {"state": self.state.value, "current": cur, "queue": [t.to_dict() for t in self.queue],
                "history": [t.to_dict() for t in self.history[:12]]}
