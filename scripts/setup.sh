#!/usr/bin/env bash
# One-command setup for the simulation, the checks and the GIORGIO-OS console:
#   1. creates .venv (Python 3.10+; 3.12 recommended), 2. installs requirements.txt + giorgio_os,
#   3. fetches the third-party robot models into third_party/.
# Usage: scripts/setup.sh            (PYTHON=python3.12 scripts/setup.sh to choose the interpreter)
# The CAD environment (cad/requirements.txt) and the GPU training environment (requirements-train.txt) are separate;
# see README "Quick start".
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-$(command -v python3.12 || command -v python3)}"
echo "==> Python: $PY ($("$PY" --version 2>&1))"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "Python >= 3.10 needed"; exit 1; }

if [[ ! -x .venv/bin/python ]]; then
  echo "==> creating .venv"
  if ! "$PY" -m venv .venv 2>/dev/null; then
    rm -rf .venv
    if command -v uv >/dev/null; then
      uv venv --seed --python "$PY" .venv
    else
      echo "The venv module is missing. On Debian/Ubuntu: sudo apt install python3-venv (or install uv: https://docs.astral.sh/uv/)"
      exit 1
    fi
  fi
fi
VPY="$ROOT/.venv/bin/python"
echo "==> installing requirements (MuJoCo 3.8, numpy, scipy, OpenCV, FastAPI, ...)"
"$VPY" -m pip install --upgrade --quiet pip
"$VPY" -m pip install --quiet -r requirements.txt
"$VPY" -m pip install --quiet --no-deps -e giorgio_os

echo "==> fetching third-party models"
bash scripts/fetch_third_party.sh

echo "==> smoke test"
MUJOCO_GL=${MUJOCO_GL:-egl} "$VPY" -c "import giorgio_model, mujoco; m = giorgio_model.build().compile(); print('Giorgio model OK:', m.nbody, 'bodies, MuJoCo', mujoco.__version__)"
cat <<MSG

Ready. Next:
  make sim        # GUI simulation (logistics mission)
  make console    # operator console at http://127.0.0.1:8080
  make check      # fast checks (same as CI)
  make help       # all tasks
MSG
