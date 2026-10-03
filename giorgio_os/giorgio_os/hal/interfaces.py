"""Hardware Abstraction Layer: one driver interface per physical device, plus two services.

Rules that every implementation (``sim`` and ``real``) must respect:

* Drivers are *thin*: they translate between giorgio_os types and the vendor SDK / ROS 2 interface.
  No mission logic lives here.
* Long-running operations return an :class:`~giorgio_os.types.ActionHandle` immediately
  (ROS 2 action semantics); callers poll ``handle.done``.
* ``set_speed_scale`` is called ONLY by the safety supervisor (see ``safety/supervisor.py``).
  Skills and the agent never get a reference to the supervisor, so no AI output can raise speed.
* The safety relay and safety scanners are READ-ONLY from software, except for selecting the
  scanner monitoring case (field set), exactly as on the real hardware.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from ..types import (ActionHandle, ArmStatus, BaseStatus, BatteryStatus, CoffeeStatus, Detection, DockStatus,
                     GripperStatus, Pose2D, RelayStatus, ScanFrame)


class Device(ABC):
    """Common lifecycle for every driver."""

    name: str = "device"
    backend: str = "abstract"

    def connect(self) -> None:          # open CAN socket / subscribe topics / etc.
        pass

    def close(self) -> None:
        pass

    def healthy(self) -> bool:
        return True

    def info(self) -> dict[str, Any]:
        return {"name": self.name, "backend": self.backend, "healthy": self.healthy()}


# ----------------------------------------------------------------------------------- mobility
class BaseDriver(Device):
    """Differential-drive mobile base (AgileX Tracer 2.0)."""

    @abstractmethod
    def status(self) -> BaseStatus: ...

    @abstractmethod
    def navigate_to(self, goal: Pose2D) -> ActionHandle:
        """Global navigation to a map pose (Nav2 ``NavigateToPose`` on the real robot)."""

    @abstractmethod
    def stop(self) -> None:
        """Controlled stop (ramp to zero), cancels navigation."""

    @abstractmethod
    def set_speed_scale(self, k: float) -> None:
        """0..1 multiplier on commanded velocity. SAFETY SUPERVISOR ONLY."""


class DockDriver(Device):
    """Charging-station docking (opennav_docking on the real robot) + contact sensing."""

    @abstractmethod
    def dock(self, dock_id: str = "home") -> ActionHandle: ...

    @abstractmethod
    def undock(self) -> ActionHandle: ...

    @abstractmethod
    def status(self) -> DockStatus: ...


# ----------------------------------------------------------------------------------- manipulation
@dataclass
class Trajectory:
    """A planned arm motion. ``payload`` is backend specific (sim: segment list; real: JointTrajectory)."""

    side: str
    payload: Any
    q_end: Optional[np.ndarray] = None
    duration_s: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


class ArmDriver(Device):
    """One 7-DOF arm (Enactic OpenArm 2.0, Damiao motors on CAN-FD)."""

    side: str = "right"

    @abstractmethod
    def status(self) -> ArmStatus: ...

    @abstractmethod
    def execute(self, traj: Trajectory) -> ActionHandle:
        """Follow a planned trajectory (FollowJointTrajectory on the real robot)."""

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def set_speed_scale(self, k: float) -> None:
        """0..1 time-scaling of trajectory execution. SAFETY SUPERVISOR ONLY."""


class GripperDriver(Device):
    """End effector: OpenArm parallel gripper, ORCA Hand v2 or Pollen AmazingHand."""

    side: str = "right"
    kind: str = "parallel"

    @abstractmethod
    def status(self) -> GripperStatus: ...

    @abstractmethod
    def command(self, opening: float, effort: float = 0.5) -> ActionHandle:
        """opening 0 (closed) .. 1 (open). Dexterous hands map this to a power-grasp synergy."""

    def open(self) -> ActionHandle:
        return self.command(1.0)

    def close(self, effort: float = 0.5) -> ActionHandle:
        return self.command(0.0, effort)


# ----------------------------------------------------------------------------------- safety hardware
class SafetyScannerDriver(Device):
    """SICK nanoScan3: field evaluation happens IN the scanner (safety-rated). We read it."""

    @abstractmethod
    def read(self) -> ScanFrame: ...

    @abstractmethod
    def set_field_case(self, case: str) -> None:
        """Select monitoring case (e.g. 'drive_fast', 'drive_slow', 'docking', 'stationary', 'service')."""


class SafetyRelayDriver(Device):
    """Pilz PNOZmulti 2: configured offline (PNOZmulti Configurator); software only reads status."""

    @abstractmethod
    def status(self) -> RelayStatus: ...


# ----------------------------------------------------------------------------------- perception & HMI
class CameraDriver(Device):
    @abstractmethod
    def frame(self, width: int = 640, height: int = 400) -> Optional[np.ndarray]:
        """Latest RGB frame (H, W, 3) uint8, or None if unavailable."""


class BatteryDriver(Device):
    """48 V LiFePO4 pack with BMS on CAN."""

    @abstractmethod
    def status(self) -> BatteryStatus: ...


class FaceDriver(Device):
    """32x16 RGB LED matrix face (HUB75 panel driven by an MCU over USB serial)."""

    @abstractmethod
    def set_expression(self, expression: str, hold_s: float = 0.0) -> None: ...

    @abstractmethod
    def state(self) -> dict[str, Any]:
        """{'expression': str, 'gaze': [x, y], 'blink': float, 'color': [r, g, b]}"""

    def show_safety(self, zone: int) -> None:
        """Mirror the safety zone on the face/status LEDs (0 clear, 1 warning, 2 stop). Informational only."""


class CoffeeModuleDriver(Device):
    """Capsule machine + linear shuttle, controlled by an MCU (micro-ROS or serial)."""

    @abstractmethod
    def status(self) -> CoffeeStatus: ...

    @abstractmethod
    def shuttle(self, position: str) -> ActionHandle:
        """'in' (under the spout) or 'out' (pick position)."""

    @abstractmethod
    def brew(self) -> ActionHandle: ...


# ----------------------------------------------------------------------------------- services
class MotionPlanner(ABC):
    """Arm motion planning (sim: giorgio_v5 IK + clash-aware planner; real: MoveIt 2)."""

    @abstractmethod
    def plan_pick(self, side: str, target: Detection, surface: str = "bench") -> Optional[Trajectory]: ...

    @abstractmethod
    def plan_place(self, side: str, where: dict[str, Any]) -> Optional[Trajectory]:
        """where = {'kind': 'tray', 'slot': k} | {'kind': 'hole', 'xy': (x, y)} | {'kind': 'bench', 'xy': (x, y)}"""

    @abstractmethod
    def plan_to_point(self, side: str, xyz_robot: tuple[float, float, float], duration_s: float | None = None) -> Optional[Trajectory]:
        """Cartesian target in the ROBOT frame (x forward, y left, z up from floor)."""

    @abstractmethod
    def plan_home(self, side: str) -> Optional[Trajectory]: ...


class Perception(ABC):
    @abstractmethod
    def detect(self, what: str) -> list[Detection]:
        """'bottle' | 'hole' | 'cup' | 'person' ..."""

    def overlay(self) -> Optional[np.ndarray]:
        return None


class WorldModel(ABC):
    """Semantic map: named places and people -> poses."""

    @abstractmethod
    def resolve(self, target: str) -> Optional[Pose2D]: ...

    @abstractmethod
    def known_targets(self) -> list[str]: ...


class Choreographies(ABC):
    """Proven multi-device routines that are not yet decomposed into HAL primitives.

    Sim: v5's choreographies (tray load/unload, coffee, hand-over) run unchanged.
    Real: empty until each one is rebuilt from pick/place/coffee primitives (README roadmap).
    """

    @abstractmethod
    def available(self) -> list[str]: ...

    @abstractmethod
    def run(self, name: str, **args: Any) -> ActionHandle: ...


@dataclass
class HardwareSet:
    """Everything the upper layers may touch. Built by ``hal.factory.build_hal``."""

    backend: str
    base: BaseDriver
    dock: DockDriver
    arms: dict[str, ArmDriver]
    grippers: dict[str, GripperDriver]
    scanners: dict[str, SafetyScannerDriver]
    relay: SafetyRelayDriver
    cameras: dict[str, CameraDriver]
    battery: BatteryDriver
    face: FaceDriver
    coffee: Optional[CoffeeModuleDriver]
    planner: MotionPlanner
    perception: Perception
    world: WorldModel
    engine: Any = None          # sim only: the physics engine (None on the real robot)
    choreo: Optional[Choreographies] = None

    def devices(self) -> list[Device]:
        out: list[Device] = [self.base, self.dock, self.relay, self.battery, self.face]
        out += list(self.arms.values()) + list(self.grippers.values()) + list(self.scanners.values()) + list(self.cameras.values())
        if self.coffee is not None:
            out.append(self.coffee)
        return out

    def advance(self, dt: float) -> None:
        """Advance time. Sim: steps physics. Real: no-op (hardware runs in real time)."""
        if self.engine is not None:
            self.engine.advance(dt)
