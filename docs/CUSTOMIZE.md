# Customise your Giorgio

Giorgio is meant to be forked and changed: a different base size, other hands, another face, a new module, a new skill.
This page shows **where each knob lives, what to change, and which check to re-run** so you know your variant still holds
together.

Be aware of what this means in practice: Giorgio is a **design and simulation**. Nothing here has been built yet. Green
checks mean "consistent with the datasheets and our models", not "safe" or "certified". Values tagged ESTIMATE or ASSUMED
in the code stay estimates until someone measures them.

> Setup first: `make setup` (or `scripts/setup.sh`) creates `.venv`, installs `requirements.txt` and fetches the
> third-party models into `third_party/`. CAD work needs the separate CadQuery environment described in
> [`cad/README.md`](../cad/README.md) (`cad/requirements.txt`). Renders need Blender 4.5 (`BLENDER=/path/to/blender`).
> Training needs an NVIDIA GPU. All scripts accept `PYTHON=...` / `BLENDER=...` overrides.

Italian names in the code are translated in [GLOSSARY.md](GLOSSARY.md).

## At a glance

| I want to change... | Edit | Re-check with | Needs |
|---|---|---|---|
| Base size, wheels, castors, batteries, scanners | `amr/amr_params.py` | `make amr-cad` + `make amr-check` | CadQuery env, ~minutes |
| Which base the simulation uses | `GIORGIO_BASE` env var (`giorgio_model.py`) | `make sim`, `verifiche/aggancio.py` | sim env |
| Hands / end effectors | `--hands` (`giorgio_v5.py`), `hands:` in `giorgio_os` configs | `make sim`, `make test` | sim env + `third_party/` |
| Colours, face, hat | `LOOKS` in `giorgio_model.py`, `render/ledface.py`, `render/hats.py` | a render | Blender for hats/faces |
| Shell shapes | `shells.py` → `assets/shells/*.obj` | `verifiche/carene.py`, `verifiche/gusci_reali.py` | sim env |
| Modules (coffee, tray, box racks) | `build(...)` flags in `giorgio_model.py`, `modules:` in configs | `make sim`, `verifiche/urti.py` | sim env |
| Superstructure CAD (column, brackets, shelf, tray) | `cad/params.py` | `cd cad && python validate.py` | CadQuery env, ~2.5 min |
| Electrical design | `amr/electrical/netlist_amr.yaml`, `electrical/*.yaml` | `amr/electrical/check_amr.py`, `electrical/calc.py` | PyYAML only |
| A learned skill | `rl_mani/`, `rl_openarm/` | the `run_cpu.py` / `valuta_e_video.py` evaluations | NVIDIA GPU |

## 1. The mobile base (AMR)

All base dimensions are in **`amr/amr_params.py`** (millimetres, kilograms; origin on the floor at the base centre,
x forward, y left, z up). Every purchased value carries a SOURCED / SECONDARY / ESTIMATE tag: keep the tag honest when you
change it. The most useful knobs:

- `L`, `W`, `CHAMF` - body plan (780 × 560 mm, 95 mm corner chamfers where the scanners sit);
- `GROUND`, `DECK_Z1`, `DECK_T` - ground clearance and the top deck, which is also the superstructure flange
  (z = 353 mm; if you move it, the arms, poses and the superstructure CAD move too);
- `WHEEL_D`, `WHEEL_Y` (track = 2 × `WHEEL_Y`), `SWD` - the ez-Wheel SWD 125 drives;
- `CASTER_*`, `SUSP_*`, `SPRING` - the four sprung castors;
- `BATT`, `BATT_X_IN` - the two Discover LFP packs and where they sit;
- `SCAN_Z`, `SCAN_XY`, `SCAN_CORNERS` - the two nanoScan3 safety scanners;
- `ROBOPAD` - the charging collector for the dock.

Then re-run the base pipeline (from `amr/`, with the CadQuery environment):

```bash
make amr-cad && make amr-check  # from the repository root; or, by hand, from amr/ with the CAD env's python:
python amr_cad.py              # CAD -> out/step, out/stl, out/parts.json, interference + keep-out checks
python integrate.py            # superstructure on the base -> out/integration.json (needs ../cad/out/stl: run cad/validate.py once)
python amr_calc.py             # mass, tipping, drives, energy, charging, safety fields, structure -> CALC.md
python electrical/check_amr.py # electrical + safety netlist checks -> electrical/CHECKS_AMR.md (PyYAML only)
```

Read the diffs of `amr/CALC.md` and `amr/electrical/CHECKS_AMR.md`: a new FAIL or WARN is the useful output. A bigger
base usually moves the tipping limits and the safety-field sizes; a heavier one changes braking and autonomy.

**The simulation reads part of this automatically.** `giorgio_model.py` takes the base mass, centre of mass and
inertia from `amr/out/parts.json`, and the visual meshes from `amr/out/stl/`. The collision box, wheel and castor
positions, scanner positions, battery capacity and dock position are in the `REVB` dictionary in `giorgio_model.py`:
update them by hand to match your new `amr_params.py` (they are not read from it yet - a good first contribution).

Renders of the base: `make render-amr`, or
`blender -b -P amr/render_amr.py -- --view hero --out amr/renders/amr_hero.png` (views, `--yaw`, `--part`, `--light`,
`--no_robot`, `--samples`, `--res`). Cycles on a GPU takes about a minute per still.

### Choosing another base in the simulation

`giorgio_model.py` has `BASE = os.environ.get("GIORGIO_BASE", "amr_revB")`:

- `amr_revB` (default) - our own AMR, rev B;
- `ranger_mini` - the historic AgileX Ranger Mini 3.0 path, kept unchanged for comparison.

Example: `GIORGIO_BASE=ranger_mini make sim`. Tipping test for a base: `python stability_test.py amr quick`.

## 2. Arms and hands

The arms are the official **Enactic OpenArm 2.0** MJCF from `third_party/openarm_mujoco/v2` (fetched, not committed).
Swapping the arms for a different model is a bigger job: `giorgio_model.py` attaches the OpenArm bimanual model to the
torso, and `giorgio_ik.py`, the choreographies in `giorgio_v5.py` and the `rl_openarm` policies all assume OpenArm
kinematics. The open owner decision (OpenArm vs a certified cobot) is in the main README.

Hands are a command-line option. `giorgio_v5.py --hands right+left`:

- `gripper` - the OpenArm parallel gripper (default; the only one with scripted grasping);
- `orca` - ORCA Hand v2 (`third_party/orcahand_description/v2`);
- `amazing` - Pollen AmazingHand (`third_party/AmazingHand`);
- `leap` - LEAP hand from mujoco_menagerie, both sides only.

Example: `python giorgio_v5.py --hands orca+amazing`. `giorgio_hands.py` is a small demo of ORCA (right) and AmazingHand
(left). Dexterous hands need a learned policy: scripted grasping is disabled for them (see section 6).

In the software stack, the configuration files in `giorgio_os/giorgio_os/configs/` choose the hands and modules:
`barista.yaml`, `logistics.yaml`, `dexterous.yaml` (`hands: orca+amazing`), `lowcost.yaml`. Copy one to make your own
variant (`name`, `hands`, `modules`, `skills`, named `locations`, `people`, safety and energy parameters), then run the
console with `--config <name>` and the tests with `make test`.

## 3. Looks: colours, face, hats, shells

- **Colour schemes**: `LOOKS` in `giorgio_model.py` (`gb` default, plus `eva`, `akira`, `gits`, `blame`, `cyber`):
  armour, accent, dark joints, visor, ambient neon, metal. Add an entry and use `--look <name>`.
- **LED face**: `render/ledface.py` draws the 64 × 32 RGB matrix procedurally. Expression codes live in `draw_px()`
  (0 neutral, 1 happy, 2 coffee, 3 stop, 4 thinking, 5 hearts, 6 alert, plus the style variants). Add a code, then
  render it with `render/blender_render.py --face_seq "<code>:<seconds>,..."`.
- **Hats**: `render/hats.py` (`HATS = {"coppola", "bustina", "snapback"}`). Each hat is a Blender mesh builder;
  `fit_outside()` lifts it so it does not cut into the head. Pick it with `--hat` in `render/blender_render.py`
  (`none` for no hat); `render/verifica_cappelli.py` (run inside Blender via `--debug_py`) checks that no hat vertex
  enters the head.
- **Shells**: `shells.py` builds the cosmetic covers as superellipsoids and writes `assets/shells/*.obj` (run
  `python shells.py`). The same meshes are used in MuJoCo (visual only) and Blender. Check them with
  `verifiche/carene.py` (the torso and column parts stay inside the shells) and
  `verifiche/gusci_reali.py render/rec_*.pkl` (true clearance between arm links and the torso shell in recorded poses). The manufacturable
  shells for the superstructure CAD are separate parts in `cad/model.py`.

## 4. Modules: coffee, tray, boxes

`build()` in `giorgio_model.py` switches the modules on and off:
`build(look, hands, humans, fixed_base, base, buffer=True, coffee=True, box_tray=False, rear_rack=False, support=False)`.

- `coffee` - the coffee backpack (capsule machine, cup shuttle, cup stack);
- `buffer` - the front tray for flasks;
- `box_tray` / `rear_rack` - box-carrying variants (see `giorgio_scatole.py` for a working example).

The main mission scripts call `build()` with fixed flags; for a new combination, copy the call in `giorgio_v5.py` or
`giorgio_scatole.py`. In GIORGIO-OS the equivalent switches are `modules:` in the YAML configs. After changing modules,
re-run `verifiche/urti.py` (arm contacts with placed objects) and, if you changed the superstructure geometry, the CAD
validation below. Coffee module dimensions for the CAD are in `cad/params.py` (`COF_SH` shelf height and the shuttle
values next to it).

## 5. Superstructure CAD and electrical design

- **Mechanical**: `cad/params.py` holds every superstructure dimension (column, torso bracket, Gemini mount, coffee shelf,
  tray, fasteners). `cad/model.py` builds the parts, `cad/validate.py` checks interference, hole fits, bolt loads,
  arm sweep against recorded poses, mass and tipping, and writes `cad/VALIDATION.md` (about 2.5 min;
  `--no-export`, `--skip-sweep`, `--poses N` make it faster). Note: `cad/` still models the superstructure on the
  historic Ranger Mini adapter; integration on our own base is checked by `amr/integrate.py`.
- **Electrical**: the own-base netlist is `amr/electrical/netlist_amr.yaml`; `python amr/electrical/check_amr.py`
  validates ratings, fuses, voltage drops and safety chains (needs only PyYAML). The older whole-robot variants live in
  `electrical/` (`netlist*.yaml`, `python electrical/calc.py <netlist.yaml> <CHECKS.md>`). Every new part needs its
  datasheet URL and a SOURCED/SECONDARY/ESTIMATE/ASSUMED tag - see [CONTRIBUTING.md](../CONTRIBUTING.md).

## 6. Re-training a skill

Both training folders use PPO on **mujoco_warp** with 4,096 parallel environments, so you need an NVIDIA GPU with CUDA
(the published runs took 50-95 min on an RTX 5070). The training environment is **separate from the simulation one**:
it was run with MuJoCo 3.5, mujoco_warp, warp 1.12, torch (CUDA) and `mjlab` (used only for `expand_model_fields`).
Evaluation and videos run on the CPU.

- **`rl_openarm/`** - one OpenArm 2.0 policy (lift a cube; open a drawer/door with `--task cabinet`), trained on the
  standalone arm and run unchanged on Giorgio. Train: `python train.py --envs 4096 --max_minutes 50 --out runs/rX`;
  evaluate: `python run_cpu.py eval --robot giorgio --n 100 --json valutazione/x.json`. Reward, randomisation and
  latency are in `env_openarm.py` / `env_cabinet.py`; the observation/action interface in `policy_io*.py`. Details and
  results in [`rl_openarm/README.md`](../rl_openarm/README.md).
- **`rl_mani/`** - ORCA hand rotating a cube in hand. `build_model.py` generates the MJCF from the ORCA files,
  `env_orca.py` is the environment, `train.py --envs 4096 --max_minutes 90 --out runs/r2` trains,
  `valuta_e_video.py` evaluates. Documented in Italian in [`rl_mani/README_IT.md`](../rl_mani/README_IT.md).

A new skill usually means: a scene (copy `scene*.py`), an environment with its reward (`env_*.py`), a policy interface
(`policy_io_*.py`), then a CPU runner that loads the weights into Giorgio's model. The sim-to-real caveats in both READMEs
apply to anything you train.

## 7. Renders and videos

- Robot renders: `render/blender_render.py` (Blender 4.5, Cycles) renders recorded simulation runs (`--record` in
  `giorgio_v5.py` → `render/to_npz.py` → Blender). Flags include `--dark`, `--solo`, `--hat`, `--face_seq`, `--xray`,
  `--newbase`, `--explode`.
- Base renders: `amr/render_amr.py` (`make render-amr`).
- The video series: `render/video_series.py` assembles the six films from rendered frames (`teaser`, `componenti`,
  `attivita`, `training`, `personalizza`, `lungo`). A full re-render takes many GPU hours; render single stills first.

## 8. Share your variant

Open an issue with the "design question" template or a pull request: say what you changed, paste the summary lines of
the checks you re-ran (PASS/WARN/FAIL counts), and cite a source for every new purchased-part value. Variants that do not
pass every check are still welcome as long as the README of your change says so.
