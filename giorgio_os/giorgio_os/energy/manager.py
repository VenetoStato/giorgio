"""Energy manager: auto-charge policy and energy guards for power-hungry skills.

Policy (thresholds in the YAML ``energy`` section):
* idle and SoC < ``charge_below``            -> queue a dock_charge task (priority above user tasks)
* any time and SoC < ``critical_below``      -> abort the current task, go charge
* docked & charging, SoC >= ``resume_above`` -> stay docked but report "full" (charger tapers)
* user task while charging: allowed only if SoC >= ``task_min_soc``, else it waits in the queue
* make_coffee (1.3 kW heater) below ``coffee_min_soc`` and not docked -> charge first, then brew
"""
from __future__ import annotations

import enum
from dataclasses import dataclass

from ..config import EnergyConfig
from ..types import BatteryStatus


class EnergyAction(str, enum.Enum):
    NONE = "none"
    CHARGE = "charge"                 # queue dock_charge when idle
    ABORT_AND_CHARGE = "abort_and_charge"


@dataclass
class EnergyDecision:
    action: EnergyAction
    reason: str = ""


class EnergyManager:
    HUNGRY_SKILLS = {"make_coffee": "coffee_min_soc"}

    def __init__(self, cfg: EnergyConfig):
        self.cfg = cfg
        self.charge_requested = False

    def update(self, bat: BatteryStatus, idle: bool, charge_task_pending: bool) -> EnergyDecision:
        if bat.charging:
            self.charge_requested = False
            return EnergyDecision(EnergyAction.NONE, "charging")
        if charge_task_pending:
            return EnergyDecision(EnergyAction.NONE, "charge task already queued")
        if bat.soc < self.cfg.critical_below:
            self.charge_requested = True
            return EnergyDecision(EnergyAction.ABORT_AND_CHARGE, f"battery critical ({100 * bat.soc:.0f}%)")
        if idle and bat.soc < self.cfg.charge_below:
            self.charge_requested = True
            return EnergyDecision(EnergyAction.CHARGE, f"battery low ({100 * bat.soc:.0f}%)")
        return EnergyDecision(EnergyAction.NONE)

    def may_leave_dock(self, bat: BatteryStatus) -> bool:
        return not bat.charging or bat.soc >= self.cfg.task_min_soc

    def guard(self, skill: str, bat: BatteryStatus) -> tuple[bool, str]:
        """(ok, reason). ok=False with reason 'charge_first' means: insert dock_charge before this skill."""
        key = self.HUNGRY_SKILLS.get(skill)
        if key and not bat.charging and bat.soc < getattr(self.cfg, key):
            return False, "charge_first"
        return True, ""

    def autonomy_h(self, bat: BatteryStatus, avg_power_w: float = 250.0) -> float:
        return bat.soc * bat.capacity_wh * 0.9 / max(avg_power_w, 1.0)
