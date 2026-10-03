"""Headless integration tests against the MuJoCo backend (giorgio_v5 physics)."""
import numpy as np
import pytest

from giorgio_os.mission.manager import SkillCall
from giorgio_os.runtime import GiorgioRuntime
from giorgio_os.types import Zone


@pytest.fixture
def quiet_rt():
    rt = GiorgioRuntime("barista", humans=False)
    rt.run_for(1.2)                     # supervisor starts stopped; 1 s of clear scans releases it
    yield rt
    rt.close()


def done(rt):
    return rt.mission.idle


def test_pick_and_place_into_tray(quiet_rt):
    rt = quiet_rt
    assert rt.decision.zone == Zone.CLEAR and rt.decision.arm_scale == 1.0
    rt.submit("pick", {"what": "bottle", "side": "right"})
    rt.submit("place", {"where": "tray"})
    assert rt.run_until(lambda: done(rt), 60)
    h = {t.title.split("(")[0]: t for t in rt.mission.history}
    assert h["pick"].status.value == "succeeded", h["pick"].message
    assert h["place"].status.value == "succeeded", h["place"].message
    assert rt.hw.engine.onboard_count() == 1
    assert not rt.hw.grippers["right"].status().holding


def test_dock_and_charge_is_automatic():
    rt = GiorgioRuntime("barista", humans=False, soc=0.25)
    try:
        rt.run_for(0.5)
        # nobody asked: the energy manager queues the charge task by itself
        assert rt.mission.has_pending("dock_charge")
        assert rt.run_until(lambda: rt.hw.battery.status().charging and done(rt), 120)
        t = rt.mission.history[0]
        assert t.source == "energy" and t.status.value == "succeeded", t.message
        st = rt.hw.dock.status()
        assert st.docked and st.contacts_closed
        soc0 = rt.hw.battery.status().soc
        rt.run_for(2.0)
        assert rt.hw.battery.status().soc > soc0
    finally:
        rt.close()


def test_safety_supervisor_stops_arms_for_a_person():
    rt = GiorgioRuntime("barista", humans=True)
    try:
        rt.run_for(1.2)
        rt.hw.engine.spawn_intruder(stop_dist=1.0, hold_s=3.0, side_deg=180)
        rt.mission.submit("pick & place", [SkillCall("pick", {"side": "right"}), SkillCall("place", {"where": "tray"})])
        saw_warning = False

        def protective():
            nonlocal saw_warning
            saw_warning |= rt.decision.zone == Zone.WARNING
            return rt.decision.zone == Zone.PROTECTIVE
        assert rt.run_until(protective, 20), "the person never entered the protective field"
        assert rt.mission.current is not None, "arms finished before the person arrived - test is not meaningful"
        assert rt.decision.arm_scale == 0.0 and rt.decision.base_scale == 0.0
        rt.run_for(0.5)                                         # controlled-stop ramp (0.3 s)
        q1 = np.array(rt.hw.arms["right"].status().q)
        rt.run_for(0.8)
        q2 = np.array(rt.hw.arms["right"].status().q)
        assert rt.decision.zone == Zone.PROTECTIVE
        assert np.abs(q2 - q1).max() < 1e-6, "arm moved inside the protective field"
        assert rt.snapshot()["mode"] == "hold (safety)"
        # the person leaves -> after the clear-hold time the task resumes and completes
        assert rt.run_until(lambda: done(rt), 60)
        assert rt.mission.history[0].status.value == "succeeded", rt.mission.history[0].message
        assert rt.safety.stops >= 1 and saw_warning
    finally:
        rt.close()


def test_software_stop_and_reset(quiet_rt):
    rt = quiet_rt
    rt.submit("wave")
    rt.run_for(1.0)
    assert rt.mission.current is not None
    rt.software_stop("test")
    rt.run_for(0.2)
    assert rt.mission.history[0].status.value == "canceled"
    assert rt.snapshot()["mode"] == "software stop"
    rt.submit("wave")                                           # queued but not started while stopped
    rt.run_for(0.5)
    assert rt.mission.current is None and len(rt.mission.queue) == 1
    assert rt.reset()["ok"]
    assert rt.run_until(lambda: done(rt), 30)
    assert rt.mission.history[0].status.value == "succeeded"


def test_chat_router_plans_navigation(quiet_rt):
    rt = quiet_rt
    r = rt.chat("go to B")
    assert r["engine"] == "router" and r["plan"] == ["navigate(B)"]
    assert rt.run_until(lambda: done(rt), 90)
    assert rt.mission.history[0].status.value == "succeeded", rt.mission.history[0].message
    assert rt.hw.base.status().pose.dist(rt.hw.world.resolve("B")) < 0.1
