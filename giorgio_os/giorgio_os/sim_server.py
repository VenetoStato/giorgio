"""Run Giorgio (sim backend by default) with the operator web UI.

    python -m giorgio_os.sim_server [--config barista] [--port 8080] [--speed 1.0] [--soc 0.85]

then open http://localhost:8080 . The control loop runs in ONE background thread that owns the
runtime (and the MuJoCo EGL context); HTTP handlers only read published snapshots/JPEGs or submit
commands that the control thread executes between ticks.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import logging
import os
import queue
import threading
import time
import traceback
from typing import Any, Callable, Optional

from .runtime import CONTROL_DT, GiorgioRuntime

log = logging.getLogger("giorgio.server")


class SimServer:
    def __init__(self, config: str = "barista", backend: str = "sim", speed: float = 1.0, render: bool = True,
                 **overrides: Any):
        self.config, self.backend, self.speed, self.render = config, backend, speed, render
        self.overrides = overrides
        self.rt: Optional[GiorgioRuntime] = None
        self._q: "queue.Queue[tuple[Callable[[GiorgioRuntime], Any], cf.Future]]" = queue.Queue()
        self._snap: dict[str, Any] = {"booting": True}
        self._frames: dict[str, bytes] = {}
        self._want: dict[str, float] = {}          # camera -> last time a client asked for it
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self.error: Optional[str] = None
        self._thread = threading.Thread(target=self._loop, name="giorgio-control", daemon=True)

    # ------------------------------------------------------------------ lifecycle
    def start(self, wait: bool = True, timeout: float = 120.0) -> "SimServer":
        self._thread.start()
        if wait:
            self._ready.wait(timeout)
        return self

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=10)

    # ------------------------------------------------------------------ API used by HTTP handlers
    def call(self, fn: Callable[[GiorgioRuntime], Any], timeout: float = 30.0) -> Any:
        fut: cf.Future = cf.Future()
        self._q.put((fn, fut))
        return fut.result(timeout=timeout)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            s = dict(self._snap)
        if self.error:
            s["error"] = self.error
        return s

    def frame(self, camera: str) -> Optional[bytes]:
        self._want[camera] = time.monotonic()
        with self._lock:
            return self._frames.get(camera)

    def switch_config(self, name: str) -> None:
        self.call(lambda rt: self._rebuild(name), timeout=120)

    # ------------------------------------------------------------------ control thread
    def _build(self) -> None:
        self.rt = GiorgioRuntime(self.config, self.backend, **self.overrides)

    def _rebuild(self, name: str) -> str:
        if self.rt is not None:
            self.rt.close()
        self.config = name
        self._build()
        with self._lock:
            self._frames.clear()
        return name

    def _loop(self) -> None:
        try:
            self._build()
        except Exception as e:
            self.error = f"startup failed: {e!r}"
            log.exception("startup failed")
            self._ready.set()
            return
        self._publish()
        self._ready.set()
        wall0, sim0 = time.monotonic(), self.rt.now()
        last_pub = last_render = 0.0
        while not self._stop.is_set():
            # commands first: they run between ticks, so they see a consistent state
            while True:
                try:
                    fn, fut = self._q.get_nowait()
                except queue.Empty:
                    break
                try:
                    fut.set_result(fn(self.rt))
                except Exception as e:
                    fut.set_exception(e)
                wall0, sim0 = time.monotonic(), self.rt.now()
            try:
                if self.speed <= 0:
                    for _ in range(5):
                        self.rt.tick()
                else:
                    target = sim0 + (time.monotonic() - wall0) * self.speed
                    if target - self.rt.now() > 0.5:          # can't keep up: don't spiral, just re-anchor
                        wall0, sim0 = time.monotonic(), self.rt.now()
                    n = 0
                    while self.rt.now() < target and n < 10:
                        self.rt.tick(); n += 1
                    if n == 0:
                        time.sleep(CONTROL_DT / 2)
                self.error = None
            except NotImplementedError as e:
                self.error = f"backend '{self.backend}': {e}"
                time.sleep(0.5)
            except Exception as e:
                self.error = f"control loop error: {e!r}"
                log.error("control loop error\n%s", traceback.format_exc())
                time.sleep(0.2)
            now = time.monotonic()
            if now - last_pub > 0.1:
                last_pub = now
                self._publish()
            if self.render and now - last_render > 0.12:
                last_render = now
                self._render_wanted(now)

    def _publish(self) -> None:
        try:
            s = self.rt.snapshot()
        except Exception as e:
            s = {"error": f"snapshot failed: {e!r}", "backend": self.backend, "config": {"name": self.config}}
        with self._lock:
            self._snap = s

    def _render_wanted(self, now: float) -> None:
        import cv2
        for cam, t in list(self._want.items()):
            if now - t > 3.0 or (cam not in self.rt.hw.cameras and cam != "gemini_overlay"):
                continue
            try:
                if cam == "gemini_overlay":
                    img = self.rt.hw.perception.overlay()
                    if img is None and "gemini" in self.rt.hw.cameras:     # nothing detected yet: raw stream
                        img = self.rt.hw.cameras["gemini"].frame(640, 400)
                    if img is None:
                        continue
                else:
                    size = (960, 540) if cam in ("chase", "top") else (640, 400)
                    img = self.rt.hw.cameras[cam].frame(*size)
                ok, jpg = cv2.imencode(".jpg", img[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    with self._lock:
                        self._frames[cam] = jpg.tobytes()
            except NotImplementedError:
                pass
            except Exception:
                log.exception("render %s failed", cam)


def main() -> None:
    ap = argparse.ArgumentParser(description="Giorgio operator console (sim backend)")
    ap.add_argument("--config", default="barista")
    ap.add_argument("--backend", default="sim", choices=["sim", "real"])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--speed", type=float, default=1.0, help="sim speed (1 = real time, 0 = as fast as possible)")
    ap.add_argument("--soc", type=float, default=None, help="initial battery state of charge (sim)")
    ap.add_argument("--no-humans", action="store_true")
    args = ap.parse_args()
    os.environ.setdefault("MUJOCO_GL", "egl")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    overrides: dict[str, Any] = {}
    if args.backend == "sim":
        if args.soc is not None:
            overrides["soc"] = args.soc
        if args.no_humans:
            overrides["humans"] = False
    from .api.app import create_app
    import uvicorn
    server = SimServer(args.config, args.backend, args.speed, **overrides).start()
    app = create_app(server)
    print(f"\n  Giorgio operator console: http://{args.host}:{args.port}\n", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    server.stop()


if __name__ == "__main__":
    main()
