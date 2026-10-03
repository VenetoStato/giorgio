"""Fast, simulator-free tests of the pure logic layers."""
import pytest

from giorgio_os.agent.agent import LocalRouter
from giorgio_os.config import SafetyConfig, EnergyConfig, list_configs, load_config
from giorgio_os.energy.manager import EnergyAction, EnergyManager
from giorgio_os.safety.supervisor import SafetySupervisor
from giorgio_os.types import BatteryStatus, RelayStatus, ScanFrame, Zone


def scan(t, prot=False, warn=False, name="front"):
    return ScanFrame(name, t, -2.4, 0.0175, [3.0] * 10, prot, warn, min_range=3.0)


def test_iso13855_distance():
    assert SafetyConfig().protective_distance_m == pytest.approx(1.72, abs=1e-3)


def test_supervisor_zones_and_hysteresis():
    sup = SafetySupervisor(SafetyConfig(clear_hold_s=1.0))
    ok = RelayStatus()
    d = sup.update(0.0, [scan(0.0)], ok)                       # starts stopped (fail-safe) ...
    assert d.arm_scale == 0.0
    d = sup.update(1.1, [scan(1.1)], ok)                       # ... runs after 1 s of valid clear data
    assert d.zone == Zone.CLEAR and d.arm_scale == 1.0 and d.base_scale == 1.0
    d = sup.update(1.2, [scan(1.2, warn=True)], ok)
    assert d.zone == Zone.WARNING and d.arm_scale == pytest.approx(0.3)
    d = sup.update(1.3, [scan(1.3, prot=True, warn=True)], ok)
    assert d.zone == Zone.PROTECTIVE and d.arm_scale == 0.0 and d.base_scale == 0.0
    d = sup.update(1.5, [scan(1.5)], ok)                       # clear, but not long enough
    assert d.arm_scale == 0.0
    d = sup.update(2.6, [scan(2.6)], ok)
    assert d.arm_scale == 1.0 and sup.stops == 1          # the start-up hold is not counted as a stop


def test_supervisor_fail_safe_on_stale_or_missing_data():
    sup = SafetySupervisor(SafetyConfig())
    sup.update(0.0, [scan(0.0)], RelayStatus()); sup.update(2.0, [scan(2.0)], RelayStatus())
    d = sup.update(3.0, [scan(2.0)], RelayStatus())            # 1 s old frame
    assert d.zone == Zone.PROTECTIVE and "stale" in d.reason
    assert sup.update(3.1, [], RelayStatus()).zone == Zone.PROTECTIVE


def test_supervisor_relay_and_software_stop():
    sup = SafetySupervisor(SafetyConfig())
    sup.update(0.0, [scan(0.0)], RelayStatus()); sup.update(2.0, [scan(2.0)], RelayStatus())
    d = sup.update(2.1, [scan(2.1)], RelayStatus(estop_ok=False, drives_enabled=False, arm_power=False))
    assert d.zone == Zone.PROTECTIVE and "E-stop" in d.reason
    sup = SafetySupervisor(SafetyConfig())
    sup.update(0.0, [scan(0.0)], RelayStatus()); sup.update(2.0, [scan(2.0)], RelayStatus())
    sup.request_software_stop("test")
    d = sup.update(2.1, [scan(2.1)], RelayStatus())
    assert d.software_stop and d.arm_scale == 0.0
    sup.update(2.2, [scan(2.2, prot=True)], RelayStatus())
    assert not sup.reset_software_stop()                       # person still in the field: no reset
    sup.update(2.3, [scan(2.3)], RelayStatus())
    assert sup.reset_software_stop()


def test_energy_policy():
    em = EnergyManager(EnergyConfig())
    bat = lambda soc, ch=False: BatteryStatus(soc, 50, 2, 100, ch)
    assert em.update(bat(0.5), True, False).action == EnergyAction.NONE
    assert em.update(bat(0.25), True, False).action == EnergyAction.CHARGE
    assert em.update(bat(0.25), False, False).action == EnergyAction.NONE      # busy: wait until idle
    assert em.update(bat(0.10), False, False).action == EnergyAction.ABORT_AND_CHARGE
    assert em.update(bat(0.10, True), False, False).action == EnergyAction.NONE
    assert em.guard("make_coffee", bat(0.18)) == (False, "charge_first")
    assert em.guard("make_coffee", bat(0.18, True))[0]
    assert em.guard("wave", bat(0.05))[0]


@pytest.mark.parametrize("text,skills", [
    ("Giorgio, make a coffee for Marco", ["make_coffee", "hand_over"]),
    ("fammi un caffe e portalo a Sara", None),                  # compound ('e portalo' is fine, 'poi' is not) -> router handles
    ("go to B", ["navigate"]),
    ("vai alla ricarica", ["dock_charge"]),
    ("please load the tray", ["load_tray"]),
    ("wave to the guests", ["wave"]),
])
def test_router(text, skills):
    r = LocalRouter(["Marco", "Sara"]).route(text, lambda: {})
    assert r is not None
    if skills:
        assert [c.skill for c in r.plan] == skills


def test_router_defers_compound_and_stops():
    router = LocalRouter(["Marco"])
    assert router.route("go to A and then make coffee if Marco is there", lambda: {}) is None
    assert router.route("stop!", lambda: {}).stop


def test_configs_load():
    names = {c["name"] for c in list_configs()}
    assert {"barista", "logistics", "dexterous", "lowcost"} <= names
    for n in names:
        cfg = load_config(n)
        assert cfg.skills and cfg.real["base"]["driver"] == "tracer_ros2"
        assert cfg.agent.llm_enabled is False                   # the LLM is off by default everywhere
