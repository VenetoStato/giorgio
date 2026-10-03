"""Operator HTTP API (FastAPI) + static single-page UI."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..config import list_configs
from ..sim_server import SimServer

STATIC = Path(__file__).resolve().parent.parent / "ui" / "static"


class TaskIn(BaseModel):
    skill: str
    args: dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = None


class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ConfigIn(BaseModel):
    name: str


class SocIn(BaseModel):
    soc: float = Field(ge=0.0, le=1.0)


class PersonIn(BaseModel):
    hold_s: float = Field(default=3.0, ge=0.0, le=60.0)
    side_deg: float = 180.0


class EstopIn(BaseModel):
    pressed: bool


def create_app(server: SimServer) -> FastAPI:
    app = FastAPI(title="Giorgio operator API", version="0.1.0")

    def need_sim():
        if server.backend != "sim":
            raise HTTPException(400, "sim-only endpoint")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/api/health")
    def health():
        s = server.snapshot()
        return {"ok": "error" not in s and not s.get("booting"), "backend": server.backend, "config": server.config,
                "error": s.get("error")}

    @app.get("/api/status")
    def status():
        return JSONResponse(server.snapshot())

    @app.get("/api/configs")
    def configs():
        return {"current": server.config, "configs": list_configs()}

    @app.post("/api/config")
    def set_config(body: ConfigIn):
        if body.name not in {c["name"] for c in list_configs()}:
            raise HTTPException(404, f"unknown configuration {body.name}")
        server.switch_config(body.name)
        return {"ok": True, "current": server.config}

    @app.get("/api/skills")
    def skills():
        return server.snapshot().get("skills", [])

    @app.get("/api/tasks")
    def tasks():
        return server.snapshot().get("mission", {})

    @app.post("/api/tasks")
    def submit(body: TaskIn):
        t = server.call(lambda rt: rt.submit(body.skill, body.args, body.title).to_dict())
        if t["status"] == "failed":
            raise HTTPException(409, t["message"])
        return t

    @app.delete("/api/tasks/{task_id}")
    def cancel(task_id: int):
        ok = server.call(lambda rt: rt.mission.cancel(task_id))
        if not ok:
            raise HTTPException(404, "no such queued/running task")
        return {"ok": True}

    @app.post("/api/chat")
    def chat(body: ChatIn):
        return server.call(lambda rt: rt.chat(body.text), timeout=60)

    @app.post("/api/estop")
    def estop():
        """SOFTWARE stop request. NOT safety-rated: the real E-stop is the red mushroom button wired to the PNOZ."""
        server.call(lambda rt: rt.software_stop("operator console"))
        return {"ok": True, "safety_rated": False}

    @app.post("/api/reset")
    def reset():
        return server.call(lambda rt: rt.reset())

    @app.get("/api/camera/{name}.jpg")
    def camera(name: str):
        jpg = server.frame(name)
        if jpg is None:
            return Response(status_code=204)
        return Response(jpg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

    # ---------------------------------------------------------------- sim-only helpers (demo & tests)
    @app.post("/api/sim/person")
    def sim_person(body: Optional[PersonIn] = None):
        need_sim()
        b = body or PersonIn()
        server.call(lambda rt: rt.hw.engine.spawn_intruder(stop_dist=1.0, hold_s=b.hold_s, side_deg=b.side_deg))
        return {"ok": True}

    @app.post("/api/sim/battery")
    def sim_battery(body: SocIn):
        need_sim()
        server.call(lambda rt: rt.hw.engine.set_soc(body.soc))
        return {"ok": True}

    @app.post("/api/sim/hw_estop")
    def sim_hw_estop(body: EstopIn):
        need_sim()

        def f(rt):
            rt.hw.engine.hw_estop = body.pressed
        server.call(f)
        return {"ok": True}

    return app
