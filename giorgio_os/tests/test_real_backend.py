"""The real backend is stubbed: it must build without hardware and fail loudly, naming the SDK."""
import pytest

from giorgio_os.config import load_config
from giorgio_os.hal import build_hal
from giorgio_os.hal.real.drivers import NotBroughtUp
from giorgio_os.mission.manager import SkillCall, TaskManager
from giorgio_os.skills import REGISTRY, SkillContext
from giorgio_os.types import Pose2D


def test_real_hal_builds_and_names_sdks():
    hw = build_hal(load_config("barista"), "real")
    assert hw.backend == "real" and hw.engine is None and hw.choreo is None
    with pytest.raises(NotBroughtUp, match="ugv_sdk"):
        hw.base.navigate_to(Pose2D(0, 0))
    with pytest.raises(NotBroughtUp, match="sick_safetyscanners2"):
        hw.scanners["front"].read()
    with pytest.raises(NotBroughtUp, match="openarm_can"):
        hw.arms["right"].status()
    assert hw.world.resolve("C").theta == pytest.approx(-1.5708)


def test_choreographed_skills_unavailable_on_real():
    cfg = load_config("barista")
    hw = build_hal(cfg, "real")
    ok, why = REGISTRY["make_coffee"].available(cfg, hw)
    assert not ok and "real backend" in why
    assert REGISTRY["navigate"].available(cfg, hw)[0]
    tm = TaskManager(SkillContext(hw, cfg, lambda: 0.0, lambda k, t: None))
    t = tm.submit("coffee", [SkillCall("make_coffee")])
    assert t.status.value == "failed"


def test_config_gates_skills():
    cfg = load_config("logistics")
    hw = build_hal(cfg, "real")
    ok, why = REGISTRY["make_coffee"].available(cfg, hw)
    assert not ok and "not enabled" in why
