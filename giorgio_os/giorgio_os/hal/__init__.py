"""Hardware abstraction layer. ``build_hal(cfg, 'sim' | 'real')`` returns a :class:`HardwareSet`."""
from __future__ import annotations

from typing import Any

from ..config import RobotConfig
from .interfaces import HardwareSet


def build_hal(cfg: RobotConfig, backend: str = "sim", **overrides: Any) -> HardwareSet:
    if backend == "sim":
        from .sim import build_sim_hal          # imports mujoco lazily: the real robot does not need it
        return build_sim_hal(cfg, **overrides)
    if backend == "real":
        from .real import build_real_hal
        return build_real_hal(cfg)
    raise ValueError(f"unknown backend {backend!r}")


__all__ = ["HardwareSet", "build_hal"]
