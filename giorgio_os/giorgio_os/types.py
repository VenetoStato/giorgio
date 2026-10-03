"""Plain data types shared by every layer (HAL, skills, safety, API).

Everything here is backend-agnostic and JSON-friendly (``to_dict``) so the same objects travel
from a MuJoCo backend or from ROS 2 callbacks up to the operator UI.
"""
from __future__ import annotations

import enum
import itertools
import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


class Zone(enum.IntEnum):
    """Scanner field state, ordered by severity."""

    CLEAR = 0
    WARNING = 1       # warning field interrupted  -> reduced speed
    PROTECTIVE = 2    # protective field interrupted -> stop


class ActionState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

    @property
    def done(self) -> bool:
        return self in (ActionState.SUCCEEDED, ActionState.FAILED, ActionState.CANCELED)


_ids = itertools.count(1)


class ActionHandle:
    """Handle for a long-running device action (ROS 2 action goal on the real robot)."""

    def __init__(self, name: str):
        self.id = next(_ids)
        self.name = name
        self.state = ActionState.PENDING
        self.message = ""
        self.result: Any = None
        self.feedback: dict[str, Any] = {}
        self._cancel_cb = None

    @property
    def done(self) -> bool:
        return self.state.done

    @property
    def ok(self) -> bool:
        return self.state == ActionState.SUCCEEDED

    def succeed(self, result: Any = None, message: str = "") -> None:
        if not self.done:
            self.state, self.result, self.message = ActionState.SUCCEEDED, result, message

    def fail(self, message: str) -> None:
        if not self.done:
            self.state, self.message = ActionState.FAILED, message

    def cancel(self) -> None:
        if self.done:
            return
        if self._cancel_cb is not None:
            self._cancel_cb(self)
        self.state = ActionState.CANCELED

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ActionHandle {self.name}#{self.id} {self.state.value} {self.message}>"


@dataclass
class Pose2D:
    x: float
    y: float
    theta: float = 0.0

    def dist(self, other: "Pose2D") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.theta]


@dataclass
class BaseStatus:
    pose: Pose2D
    v: float = 0.0               # m/s
    w: float = 0.0               # rad/s
    navigating: bool = False
    speed_scale: float = 1.0


@dataclass
class ArmStatus:
    side: str
    q: list[float]
    busy: bool = False
    speed_scale: float = 1.0
    holding: Optional[str] = None


@dataclass
class GripperStatus:
    side: str
    kind: str                     # "parallel" | "orca" | "amazing"
    opening: float = 0.0          # 0 closed .. 1 fully open
    holding: bool = False


@dataclass
class ScanFrame:
    """One scanner frame. ``protective``/``warning`` are the DEVICE's own field evaluation
    (on a nanoScan3 they are the safety outputs / field-interruption bits); ``ranges`` are
    the measurement data used for visualisation and for the software SSM layer."""

    scanner: str
    stamp: float
    angle_min: float
    angle_inc: float
    ranges: list[float]
    protective: bool = False
    warning: bool = False
    field_case: str = "default"
    origin_xy: tuple[float, float] = (0.0, 0.0)   # scanner origin in the robot frame
    yaw: float = 0.0                               # scanner mounting yaw in the robot frame
    min_range: float = float("inf")
    field_radii: Optional[tuple[float, float]] = None   # (protective, warning) for display, if the device reports it


@dataclass
class RelayStatus:
    """State of the Pilz PNOZmulti safety relay as read back by the controller (read-only)."""

    estop_ok: bool = True               # hardware E-stop chain closed
    scanners_ok: bool = True            # OSSD inputs from both scanners high
    drives_enabled: bool = True         # base drive enable output
    arm_power: bool = True              # arm bus contactors closed
    reset_required: bool = False
    stamp: float = field(default_factory=time.time)


@dataclass
class BatteryStatus:
    soc: float                          # 0..1
    voltage: float
    current: float                      # A, + = discharge
    power: float                        # W, + = discharge
    charging: bool = False
    temperature_c: float = 25.0
    capacity_wh: float = 2400.0


@dataclass
class DockStatus:
    docked: bool
    contacts_closed: bool
    error_mm: Optional[tuple[float, float, float]] = None   # gap, lateral, yaw(deg*1000) diagnostic


@dataclass
class CoffeeStatus:
    shuttle: str = "out"                # "out" | "in" | "moving"
    brewing: bool = False
    cups_left: int = 5
    ready: bool = True


@dataclass
class Detection:
    label: str
    xy: tuple[float, float]             # world frame [m]
    z: float = 0.0
    score: float = 1.0
    box: Optional[tuple[int, int, int, int]] = None
    ref: Optional[str] = None           # backend reference (sim: body name)


@dataclass
class SafetyDecision:
    zone: Zone
    arm_scale: float
    base_scale: float
    reason: str
    software_stop: bool = False
    min_distance: float = float("inf")
    stamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["zone"] = self.zone.name
        d["min_distance"] = None if math.isinf(self.min_distance) else round(self.min_distance, 3)
        return d


FACE_EXPRESSIONS = ("neutral", "happy", "coffee", "stop", "thinking", "love", "attentive", "charging", "wave")
