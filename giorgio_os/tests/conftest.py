import os

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ["GIORGIO_OFFLINE"] = "1"          # never call external services from tests
