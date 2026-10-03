"""Robot configuration: one YAML file per product configuration (barista, logistics, dexterous, low-cost).

The YAML is the single source of truth for which devices are fitted, which skills are offered,
safety/energy parameters and the real-robot device addresses (CAN interfaces, IPs, serial ports).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).parent / "configs"


@dataclass
class SafetyConfig:
    # ISO 13855: S = K * T + C   (K = 1600 mm/s walking speed, T = response + stopping time, C = intrusion allowance)
    k_mm_s: float = 1600.0
    t_s: float = 0.37
    c_mm: float = 1128.0
    reduced_speed: float = 0.30        # speed scale inside the warning field
    clear_hold_s: float = 1.0          # field must stay clear this long before speed goes back up
    scanner_timeout_s: float = 0.25    # stale scanner data -> protective stop (fail-safe)

    @property
    def protective_distance_m(self) -> float:
        return (self.k_mm_s * self.t_s + self.c_mm) / 1000.0


@dataclass
class EnergyConfig:
    capacity_wh: float = 2400.0
    charge_below: float = 0.30         # go and charge when idle and below this
    critical_below: float = 0.15       # abort the current task and charge
    resume_above: float = 0.80         # leave the dock automatically once here (if work is queued earlier: task_min_soc)
    task_min_soc: float = 0.40         # a queued user task may pull the robot off the dock above this
    coffee_min_soc: float = 0.20       # do not brew (1.3 kW heater) below this unless docked


@dataclass
class AgentConfig:
    llm_enabled: bool = False          # Claude API is OPTIONAL and OFF by default
    llm_model: str = "claude-opus-5-5"
    llm_effort: str = "low"           # routing a request to skills is a light task
    llm_timeout_s: float = 20.0
    language: str = "en"


@dataclass
class RobotConfig:
    name: str
    title: str
    description: str
    hands: str = "gripper"                      # gripper | orca | amazing | orca+amazing (right+left)
    modules: dict[str, bool] = field(default_factory=dict)   # coffee, cam360, tray ...
    skills: list[str] = field(default_factory=list)
    locations: dict[str, list[float]] = field(default_factory=dict)
    people: dict[str, list[float]] = field(default_factory=dict)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    energy: EnergyConfig = field(default_factory=EnergyConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    sim: dict[str, Any] = field(default_factory=dict)
    real: dict[str, Any] = field(default_factory=dict)
    bom_eur: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def has(self, module: str) -> bool:
        return bool(self.modules.get(module, False))

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self.raw)


def _sub(cls, data: dict | None):
    data = data or {}
    known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
    return cls(**known)


def load_config(name_or_path: str | Path, **overrides: Any) -> RobotConfig:
    p = Path(name_or_path)
    if not p.suffix:
        p = CONFIG_DIR / f"{name_or_path}.yaml"
    raw = yaml.safe_load(p.read_text())
    raw.update(overrides)
    return RobotConfig(
        name=raw.get("name", p.stem),
        title=raw.get("title", p.stem),
        description=raw.get("description", ""),
        hands=raw.get("hands", "gripper"),
        modules=raw.get("modules", {}),
        skills=raw.get("skills", []),
        locations=raw.get("locations", {}),
        people=raw.get("people", {}),
        safety=_sub(SafetyConfig, raw.get("safety")),
        energy=_sub(EnergyConfig, raw.get("energy")),
        agent=_sub(AgentConfig, raw.get("agent")),
        sim=raw.get("sim", {}),
        real=raw.get("real", {}),
        bom_eur=raw.get("bom_eur"),
        raw=raw,
    )


def list_configs() -> list[dict[str, str]]:
    out = []
    for p in sorted(CONFIG_DIR.glob("*.yaml")):
        raw = yaml.safe_load(p.read_text())
        out.append({"name": p.stem, "title": raw.get("title", p.stem), "description": raw.get("description", "")})
    return out
