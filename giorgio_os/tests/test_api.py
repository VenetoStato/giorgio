"""HTTP API smoke tests: real server object, sim backend, as-fast-as-possible clock."""
import time

import pytest
from fastapi.testclient import TestClient

from giorgio_os.api.app import create_app
from giorgio_os.sim_server import SimServer


@pytest.fixture(scope="module")
def client():
    server = SimServer("barista", speed=0, humans=False).start()
    with TestClient(create_app(server)) as c:
        yield c
    server.stop()


def wait_for(fn, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if fn():
            return True
        time.sleep(0.1)
    return False


def test_index_and_static(client):
    r = client.get("/")
    assert r.status_code == 200 and "GIORGIO" in r.text
    assert client.get("/static/app.js").status_code == 200


def test_health_and_status(client):
    assert client.get("/api/health").json()["ok"]
    s = client.get("/api/status").json()
    for k in ("battery", "safety", "mission", "face", "base", "skills", "cameras", "chat", "events"):
        assert k in s
    assert s["safety"]["iso13855_s_m"] == pytest.approx(1.72, abs=0.01)


def test_configs(client):
    c = client.get("/api/configs").json()
    assert c["current"] == "barista" and len(c["configs"]) >= 4


def test_tasks_and_validation(client):
    assert client.post("/api/tasks", json={"skill": "does_not_exist"}).status_code == 409
    r = client.post("/api/tasks", json={"skill": "wave"})
    assert r.status_code == 200
    tid = r.json()["id"]
    assert wait_for(lambda: any(t["id"] == tid and t["status"] == "succeeded"
                                for t in client.get("/api/tasks").json()["history"]), 60)


def test_chat(client):
    r = client.post("/api/chat", json={"text": "how is your battery?"}).json()
    assert r["engine"] == "router" and "Battery" in r["say"]
    r = client.post("/api/chat", json={"text": "recite a poem about the moon then dance"}).json()
    assert r["engine"] == "none" and r["plan"] == []              # LLM off by default


def test_camera(client):
    client.get("/api/camera/chase.jpg")                          # first request subscribes the camera
    assert wait_for(lambda: client.get("/api/camera/chase.jpg").status_code == 200)
    r = client.get("/api/camera/chase.jpg")
    assert r.headers["content-type"] == "image/jpeg" and len(r.content) > 5000


def test_software_stop_endpoint(client):
    r = client.post("/api/estop").json()
    assert r["ok"] and r["safety_rated"] is False
    assert wait_for(lambda: client.get("/api/status").json()["mode"] == "software stop")
    assert client.post("/api/reset").json()["ok"]
    assert wait_for(lambda: client.get("/api/status").json()["mode"] != "software stop")


def test_sim_helpers(client):
    assert client.post("/api/sim/battery", json={"soc": 0.9}).json()["ok"]
    assert client.post("/api/sim/battery", json={"soc": 2}).status_code == 422
