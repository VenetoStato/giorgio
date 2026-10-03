"""Safety supervisor: speed & separation monitoring (SSM) in software, OUTSIDE the AI path.

Layering (see ARCHITECTURE.md):

1. **Safety-rated layer (hardware, PL d)**: 2x SICK nanoScan3 evaluate protective/warning fields
   internally; their OSSDs go into the Pilz PNOZmulti 2, which removes drive enable and opens the arm
   bus contactors (after a controlled stop). Nothing in this repository can override that.
2. **This module (non-safety-rated, but deterministic and simple)**: reads the scanners' own field
   flags and the relay status, and scales arm/base speed *before* the hardware has to intervene
   (warning field -> reduced speed, protective field -> controlled stop, stale data -> stop). It also
   latches the operator's *software* stop.

Design rules enforced here:
* Inputs are sensor data only. No LLM / agent / skill output is an input.
* ``apply()`` is the ONLY caller of ``set_speed_scale`` on drivers. Skills never get this object.
* Fail-safe: missing or stale scanner data == protective stop.
* Speed may go DOWN immediately but only goes UP after the fields have been clear for ``clear_hold_s``.
"""
from __future__ import annotations

import logging
import math
from typing import Iterable, Optional

from ..config import SafetyConfig
from ..hal.interfaces import HardwareSet
from ..types import RelayStatus, SafetyDecision, ScanFrame, Zone

log = logging.getLogger("giorgio.safety")


class SafetySupervisor:
    def __init__(self, cfg: SafetyConfig):
        self.cfg = cfg
        self._cmd = 0.0                      # start STOPPED: motion allowed only after valid clear data for clear_hold_s
        self._clear_since: Optional[float] = None
        self._sw_stop: Optional[str] = None
        self.last = SafetyDecision(Zone.CLEAR, 1.0, 1.0, "init")
        self.stops = 0
        self._raw_zone = Zone.CLEAR          # zone from sensors/relay only (excluding the software stop)
        self.slowdowns = 0

    # ------------------------------------------------------------------ operator software stop (NOT safety-rated)
    def request_software_stop(self, reason: str = "operator") -> None:
        if self._sw_stop is None:
            log.warning("software stop requested: %s", reason)
        self._sw_stop = reason

    def reset_software_stop(self) -> bool:
        """Release the software stop. Allowed only if no protective condition is active."""
        if self._raw_zone == Zone.PROTECTIVE:
            return False
        self._sw_stop = None
        return True

    @property
    def software_stop_active(self) -> bool:
        return self._sw_stop is not None

    # ------------------------------------------------------------------ core logic (pure function of inputs + memory)
    def update(self, now: float, scans: Iterable[ScanFrame], relay: Optional[RelayStatus]) -> SafetyDecision:
        scans = list(scans)
        zone, reasons = Zone.CLEAR, []
        min_d = math.inf
        if not scans:
            zone, reasons = Zone.PROTECTIVE, ["no scanner data"]
        for s in scans:
            if s.stamp < 0 or now - s.stamp > self.cfg.scanner_timeout_s:
                zone = Zone.PROTECTIVE; reasons.append(f"{s.scanner}: stale data")
                continue
            min_d = min(min_d, s.min_range)
            if s.protective:
                zone = Zone.PROTECTIVE; reasons.append(f"{s.scanner}: protective field")
            elif s.warning and zone < Zone.WARNING:
                zone = Zone.WARNING; reasons.append(f"{s.scanner}: warning field")
        arm_hw = base_hw = 1.0
        if relay is not None:
            if not relay.estop_ok:
                zone = Zone.PROTECTIVE; reasons.append("hardware E-stop pressed")
            elif relay.reset_required:
                zone = Zone.PROTECTIVE; reasons.append("safety relay: reset required")
            if not relay.drives_enabled:
                base_hw = 0.0
            if not relay.arm_power:
                arm_hw = 0.0
        # hysteresis: drop immediately, raise only after a clear period
        if zone == Zone.PROTECTIVE:
            if self._cmd > 0:
                self.stops += 1
            cmd = 0.0; self._clear_since = None
        else:
            target = self.cfg.reduced_speed if zone == Zone.WARNING else 1.0
            if self._clear_since is None:
                self._clear_since = now
            if self._cmd == 0.0 and now - self._clear_since < self.cfg.clear_hold_s:
                cmd = 0.0; reasons.append("waiting for clear field")
            else:
                if target < 1.0 and self._cmd == 1.0:
                    self.slowdowns += 1
                cmd = target
        self._cmd = cmd
        self._raw_zone = zone
        sw = self._sw_stop is not None
        if sw:
            reasons.insert(0, f"software stop: {self._sw_stop}")
        arm = 0.0 if sw else min(cmd, arm_hw)
        base = 0.0 if sw else min(cmd, base_hw)
        shown_zone = zone if not sw else Zone.PROTECTIVE
        self.last = SafetyDecision(shown_zone, arm, base, "; ".join(reasons) or "clear", sw, min_d, now)
        return self.last

    # ------------------------------------------------------------------ the only place where speed scales are written
    def apply(self, hw: HardwareSet, decision: SafetyDecision) -> None:
        for arm in hw.arms.values():
            arm.set_speed_scale(decision.arm_scale)
        hw.base.set_speed_scale(decision.base_scale)

    def step(self, now: float, hw: HardwareSet) -> SafetyDecision:
        scans = [s.read() for s in hw.scanners.values()]
        d = self.update(now, scans, hw.relay.status())
        self.apply(hw, d)
        return d

    @property
    def protective_distance_m(self) -> float:
        return self.cfg.protective_distance_m
