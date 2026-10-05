# GIORGIO — mobile bimanual service robot

> We couldn't build the parts. So we bought them, and made them work together.

Giorgio is a mobile two-armed service robot assembled from open-hardware projects and certified off-the-shelf components,
with a custom structure, shells, power system and software. It does logistics, sorting, works next to people — and makes espresso.

**Status: design + simulation stage.** Nothing here has been built yet. Every number is either sourced (datasheets, URLs in the
respective folders) or explicitly marked as assumed.

**Open project.** Code, CAD, electrical design, simulation and training are public: fork it, open issues, send pull requests
(see [CONTRIBUTING.md](CONTRIBUTING.md)). Licences: software [Apache-2.0](LICENSE), hardware/CAD [CERN-OHL-S-2.0](LICENSE-HARDWARE),
documents, renders and videos [CC BY 4.0](LICENSE-DOCS). Third-party models keep their own licences (see NOTICE.md).

**New (Oct 2026): our own mobile base** → [`amr/`](amr/README.md): a CE-oriented AMR built from certified safety modules
(SICK nanoScan3, Pilz PNOZmulti 2, ez-Wheel SWD), with CAD, calculations, electrical + safety package, CE technical-file
skeleton, Italian industrialisation plan and a component-by-component certainty audit (`amr/CERTAINTY.md`). The simulation
uses it by default (`giorgio_model.py`, `BASE = "amr_revB"`). Video series: `render/video_series.py`.

| Area | Folder | What's there | Check |
|---|---|---|---|
| Own mobile base (AMR) | `amr/` | CAD rev B4 (170 parts, keep-out checks), CALC, electrical/safety (Pilz + SICK + ez-Wheel), CE file, BOM + industrialisation, certainty audit | `amr/amr_cad.py`, `amr/amr_calc.py`, `amr/electrical/check_amr.py` |
| Simulation (MuJoCo 3.8) | `giorgio_v5.py`, `giorgio_model.py`, `giorgio_sort.py`, `giorgio_hands.py`, `rec_ricarica.py` | full robot with official OpenArm 2.0 MJCF, own AMR base (rev B) with diff-drive, safety scanners (ray-cast), people, vision, energy model, auto-docking, coffee module | `verifiche/urti.py` (no arm contact with placed objects), `verifiche/aggancio.py` (auto-docking) |
| Mechanical CAD (CadQuery) | `cad/` | ~100 parts, 128 bolted joints, STEP/STL exports, fastener BOM, mass properties | `cad/validate.py` → `cad/VALIDATION.md` |
| Electrical | `electrical/` | 48 V LiFePO4 (15s, 1.92 kWh) architecture, safety chain (PNOZ, 2× nanoScan3, PL d target), netlist with part numbers, schematic | `electrical/calc.py` → `electrical/CHECKS.md` |
| Software — GIORGIO-OS | `giorgio_os/` | HAL with sim + real (stub) backends, skills, safety supervisor (not in the AI path), energy manager, task manager, NL agent, operator web console | `pytest` (29 tests, headless on the sim) |
| Feasibility | `FEASIBILITY.md` | SDK/driver/licence check for every component, recommended swaps, top risks | — |
| Dexterous hands (RL) | `rl_mani/` | PPO on mujoco_warp, ORCA hand in-hand cube rotation | `rl_mani/valutazione/` |
| Renders & video | `render/` | Blender 4.5 pipeline, logo, compositing (`compose.py`), music synthesis | — |
| Business | `kickstarter/`, `docs/` | campaign drafts (IT/EN), power & certification notes | — |

## Bill of materials (main purchased parts)
Own AMR base (see `amr/bom_amr.csv`; earlier variants used an AgileX Tracer 2.0) · 2× Enactic OpenArm 2.0 (open hardware, CERN-OHL-S) · OpenArm grippers / ORCA Hand / AmazingHand (open) ·
2× SICK nanoScan3 + Pilz PNOZmulti 2 (safety) · Orbbec Gemini 336L · NVIDIA Jetson AGX Orin · 48 V LFP pack with CAN BMS · Mean Well DDR DC-DCs ·
32×16 LED face · any compact capsule coffee machine. See `FEASIBILITY.md` for the 360° camera replacement and the updated BOM (~€30k).

## Quick start
```bash
PY=~/IsaacLab/env_isaaclab/bin/python                    # MuJoCo 3.8 + numpy/scipy
MUJOCO_GL=egl PYTHONPATH=. $PY giorgio_v5.py             # GUI simulation (logistics mission)
MUJOCO_GL=egl giorgio_os/.venv/bin/python -m giorgio_os.sim_server   # operator console → http://127.0.0.1:8080
cd cad && .env/bin/python validate.py                     # mechanical validation (needs the CadQuery env, see cad/README.md)
$PY electrical/calc.py                                    # electrical checks
```
Third-party models (OpenArm MJCF, ORCA, AmazingHand, menagerie) live in `third_party/` and are not committed — see `docs/README_IT.md`.

## Open decisions (owner)
1. **Arms**: OpenArm (open, cheap; no STO/brakes → non-collaborative, no hand-to-hand handover in a certified product) vs a certified cobot (e.g. UR3e with 48 V DC control box).
2. **Coffee power**: brew at the dock (default, fastest certification) · 24 V on-board capsule module · 230 V on board (rejected: inverter, 2.35 C peaks).
3. **Base**: resolved, own AMR with a certified safety chain (`amr/`). Remaining residuals: `amr/DOWNLOAD_LIST.md`.
4. **Price**: updated BOM ≈ €30k → at 30% margin ≈ €43k (the old €39,900 needs revisiting).

Italian documentation and the full history of the simulation work: `docs/README_IT.md`.

## Third-party components and trademarks

See [NOTICE.md](NOTICE.md): licences of the OpenArm, ORCA and AmazingHand models, and trademark notes. Giorgio is an unbuilt concept, not affiliated with or endorsed by any component maker.
