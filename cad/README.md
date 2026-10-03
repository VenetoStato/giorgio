# Giorgio — mechanical CAD (parametric, validated)

Parametric CadQuery model of every part we must manufacture for Giorgio (mobile bimanual service robot), with the
purchased parts as datasheet envelopes (or the official mesh), every bolted joint specified, and a headless validator that
checks interference, clearances, fits, fasteners, mass and tipping. Results are in **[VALIDATION.md](VALIDATION.md)**
(regenerated on every run); sources in **[SOURCES.md](SOURCES.md)**; processes and assembly sequence in
**[MANUFACTURING.md](MANUFACTURING.md)**.

Frame and units everywhere: millimetres, robot base frame = MuJoCo `amr` body (origin on the floor at the base centre,
x forward, y left, z up), coffee shuttle retracted ("out"). **Current design: AgileX RANGER AIR base (owner decision 2026-10-03).** The Tracer 2.0 design is archived in git at commit 2660c92.

## How to run

```bash
cd ~/giorgio_sim
# one-off environment (≈2 GB, already created): conda create -p cad/.env python=3.11 &&
#   cad/.env/bin/pip install --no-cache-dir cadquery trimesh manifold3d scipy rtree python-fcl networkx shapely mujoco==3.8.0
# coffee poses at the 0.69 m shelf (re-record if the sim changes; ~42 MB, git-ignored):
MUJOCO_GL=egl PYTHONPATH=~/giorgio_sim ~/IsaacLab/env_isaaclab/bin/python giorgio_v5.py --agent "1:Giorgio, fammi un caffe e portalo a Marco" --seconds 100 --record cad/data/rec_caffe_sh069.pkl
cad/.env/bin/python cad/sim_export.py          # read-only: arm meshes + recorded poses (render/logistica_v9 + cad/data/rec_caffe_sh069.pkl) -> cad/data/
cd cad && .env/bin/python validate.py          # build + all checks + exports, ~2.5 min (--no-export, --skip-sweep, --poses N)
.env/bin/python model.py                        # just build and list parts/masses (11 s)
~/tools/blender-4.5.9-linux-x64/blender -b -P render_blender.py -- both   # preview PNGs (Workbench)
```

Outputs (git-ignored, regenerated): `out/step/<part>.step` (one per custom/purchased B-rep part), `out/stl/<part>.stl`,
`out/giorgio_assembly.step` (19 MB) + `.stl`, `out/exploded/<part>.stl` already displaced + `out/exploded/exploded.json`
(per part: file, category, material, process, RGB colour, finish suggestion, explode vector, motion group),
`out/bom_parts.csv`, `out/bom_fasteners.csv`, `out/mass_properties.json`, `out/render_*.png`.

Files: `params.py` (all dimensions, each purchased value tagged SOURCED/ESTIMATE/ASSUMED), `geom.py` (Part/Hole model,
superellipsoid B-rep lofts), `model.py` (all parts + joints), `fasteners.py` (ISO tables, bolt solids, geometric checks),
`validate.py` (assembly, checks, loads, exports, report), `sim_export.py`, `render_blender.py`, `mass_budget_before.json` (reference for the before/after table), `BASE_DECISION.md`.


## Results summary — Ranger Air design (VALIDATION.md has every number)

**55 PASS, 17 WARN, 0 FAIL.** The 17 WARN are:
- 10 bolt groups on ASSUMED purchased-part interfaces (they pass with the assumed values);
- 3 arm clearances under the 5 mm target (cup ring 2.4 mm, Gemini 3.1 mm, coffee machine 4.4 mm; 0 contacts);
- the plan overhang of the coffee module and tray beyond the 552 × 500 base;
- 3 tipping cases below the 0.5 g target (all above the 2.2 m/s² floor).

| Check | Result |
|---|---|
| **Payload (hard ≤ 68 kg, target ≤ 64 kg; Ranger Air rated 80 kg)** | **PASS — superstructure 54.2 kg + product payload 5.1 kg (2 × 1.5 kg in the hands + 2.1 kg tray) = 59.3 kg = 74 % of 80 kg, margin 20.7 kg (26 %)** |
| Extension CoG vs centre of rotation (±20 mm) | PASS nominal (−17.7, +0.2) mm; holding 2 × 1.5 kg at 300 mm (−1.7, +0.2) mm. CoG height 788 mm above the floor (538 mm above the deck) |
| Interference (all pairs incl. 97 bolts, exact OCC), shuttle positions | PASS, 0 overlaps |
| Hole alignment / ISO 273 / tap drills / engagement / edge distance | PASS |
| Bolt loads (all groups, 10 load cases incl. 0.5 g omni braking/cornering, +2 g bump, e-stop) | PASS; 10 groups WARN for ASSUMED interfaces (Ranger Air hole thread, OpenArm plate/post/top, scanner holes, Gemini) |
| body_link0 covered by the shells | PASS 100 % (plate in the waist cover; top under the torso shell / neck plate) |
| Arm sweep, 793 recorded poses (logistics + coffee at the 0.69 m shelf) | 0 contacts; WARN cup ring 2.4, Gemini 3.1, machine 4.4 mm |
| **Docking zone** (rear brush plate of the AgileX station, x < −276, \|y\| ≤ 90, z ≤ 300) | PASS — free. The coffee housing overhangs 54 mm behind the base above z 380 (dock height to confirm) |
| Footprint | WARN: plan 780 × 780 mm (pods at 2 corners, tray ±309, coffee module rear) vs base 552 × 500 |
| **Tipping (support ±194 × ±169 mm)** | nominal 4.40 / 3.83 / **3.58** / 3.59 m/s²; work 3.92 / 3.88 / 3.39 / 3.40; worst (arms fwd, 2 × 1.5 kg) **3.43** / 4.34 / **3.38** / 3.39 → all ≥ 2.2 m/s² but < 0.5 g → **software limit on base acceleration and lateral acceleration ≤ 1.5 m/s²** (safety factor ≥ 2.2). Beyond the rating (2 × 4.1 kg at reach): forward 2.89 m/s² |

### Mass budget (kg; before = validated Tracer design)

| Group | Tracer | Ranger Air | How (real change) |
|---|---|---|---|
| mobile base | 55.0 | 50.0 | Ranger Air (50–55 kg; payload counts separately) |
| 48 V battery + tray + charger + RoboPad | 13.0 + 0.9 + 1.2 + 0.4 | **0** | base-powered at 24 V from the Ranger Air battery; the AgileX station charges everything |
| electronics | 6.5 | 2.0 + 1.9 buffer | no 48→24 V DC-DCs (the arms run at 24 V); Jetson module + carrier (0.6, ESTIMATE); 24→19 V and 24→5 V DC-DCs; 24 V LFP peak buffer 1.9 kg (electrical lead, ≤ 2 kg) |
| column (sleeve + liners + profile + bracket) | 6.5 | 4.6 | fixed height: 20 mm foot P29 + 292 mm profile + P02 |
| base adapter plate | 6.0 | 3.1 | 8 mm "butterfly" plate: core + front/rear wings + 2 pod arms, grid lightening |
| shells | 5.0 | 3.0 | no skirt (the base has its own body): 2 mm deck cover; column cover 120 × 120 |
| bumper | 1.1 | 0 | removed (decorative) |
| wiring allowance | 3.0 | 2.0 | ESTIMATE, no 48 V battery harness |
| OpenArm arms + body_link0, coffee module, tray, head, sensors | unchanged | unchanged | |
| **robot total** | **135.7** | **104.2** | |
| **superstructure + product payload** | **88.8** (2 × 3 + 2.1) | **59.3** (2 × 1.5 + 2.1) | |

The product payload is now **≤ 1.5 kg per arm** (cups, bottles; software limit) plus ≤ 2.1 kg in the tray. Both task modules (coffee and tray) stay installed. Making them optional would give another −6.1 kg (coffee) or −2.3 kg (tray) if the margin is ever needed.

## What the design is now (Ranger Air, z in mm)

| z | Element |
|---|---|
| 0–250 | AgileX RANGER AIR: 552 × 500 × 250, 4WD/4WS. Flat top plate with 8 tapped holes (200 × 80 grid). Rear charging brush plate at z ≈ 115–180 |
| 250–258 | **P01 adapter plate** 8 mm 6082 "butterfly" (3.1 kg), 8 × M6 countersunk into the deck holes (thread ASSUMED) |
| 258–376 | front e-plate (buffer, Jetson module, DC-DCs) and rear e-plate (PNOZ on DIN, 2 arm-bus contactors), under the **SH01 deck cover** (2 mm PA12, standing on the base deck inside its outline) |
| 258–565 | fixed column: **P29 foot** (20 mm, 8 × M6 into P01, M12 from below into the profile core) + item 80×80 L profile 292 mm + **P02** (unchanged) |
| 129–261 | 2 × SICK nanoScan3 in corner pods outside the base at (±317.7, ∓317.7), scan plane 180 mm |
| 580–1660 | unchanged: OpenArm body_link0 + arms, waist cover, torso shell, head, Gemini, Insta360, chest tray |
| 684–942 | coffee module unchanged (shelf 0.69 m). Uprights moved to x −266…−190, inside the base outline |

## Real vs assumed (Ranger Air specific; the rest as before, see SOURCES.md)

**SOURCED** (Ranger Air manual V1.0.0 2026-01-25, product page, ROS `ranger_ros` air_delta, Generation Robots):
- 552 × 500 × 250 mm, 50–55 kg, 80 kg payload, payload CoG at the rotation centre;
- wheelbase 388 / track 338, 1.5 m/s, 8° slope;
- 24 V 30 Ah LFP; expansion 24–29.6 V ≤ 25 A, ≤ 600 W total (the plug table says 10 A: conflict);
- 8-hole top grid 200 × 80 (drawing);
- contact-type charging brush plate at the rear (drawing);
- automatic recharging (product page);
- price €3,700 (standard) / €5,600 (navigation version) excl. VAT;
- no external safety input; no braking or deceleration data.

**ESTIMATE / ASSUMED:**
- deck height 250 (from the drawing);
- hole x-offsets and thread (M6, depth ≥ 12);
- base CoG 118 mm (from the 131.8 mm figure);
- wheel Ø122;
- contact plate height and width;
- whether the dock needs the navigation version/NAVIS;
- dock height and depth (coffee overhang);
- peak expansion current;
- Jetson module, DC-DC and buffer envelopes.

## Proposed changes to the sim model (exact values, metres)

| Item | Sim now (Tracer) | Ranger Air design |
|---|---|---|
| base | Tracer box 0.702 × 0.61, 55 kg, diff drive + casters | **Ranger Air**: body 0.552 × 0.500, z 0.043–0.250, **50 kg**, CoG z 0.118; 4 wheels Ø0.122 at (±0.194, ±0.169) with independent steering (omni: spin, crab, Ackermann); speed ≤ 1.5 m/s; deck at z 0.250 |
| support / tipping | casters ±0.281 × ±0.255 | wheels ±0.194 × ±0.169 → **limit base accel/decel and lateral accel to ≤ 1.5 m/s²** in the controller |
| base fixed mass (not visual, on `amr`) | 46.2 kg | **23.6 kg at (−0.070, 0.001, 0.424)** (adapter, e-plates, buffer, electronics, scanners, pods, deck cover, column foot, coffee module) |
| battery | own 48 V box | **none**: base 24 V 30 Ah (0.72 kWh shared with traction). Runtime model ≈ 0.72 × 0.9 / (250 W + traction) ≈ 2 h (ESTIMATE) → opportunity charging |
| docking | RoboPad on the nose, 0.406 | **AgileX station at the rear**: the robot **reverses** onto it; contact plate at the rear face centre, z ≈ 0.115–0.18, width ≈ 0.137 (EST). Remove the nose pads |
| column | sleeve + profile, stroke 0.15 | **fixed** (`COLUMN_STROKE` 0): profile z 0.273–0.565, 1.56 kg; foot 1.25 kg at z 0.268; torso origin z 0.580 unchanged |
| `SCANNERS` | (0.3467, −0.3467), (−0.3407, 0.3407) | **(0.3177, −0.3177), (−0.3177, 0.3177)**, headings −45° / 135°, `SCAN_Z` 0.18 |
| base skirt, bumper, LED / tricolour bands | superellipsoid skirt | **removed**. Replaced by a deck cover box 0.550 × 0.498, z 0.250–0.376 (corner cut-outs at the pods) |
| fixed column cover | 180 × 200 mm | **120 × 120 mm** (r 24), z 0.376–0.540 |
| coffee uprights | x −0.29…−0.21 | x −0.266…−0.190 |
| torso/waist/head shells, tray, coffee module, Gemini, Insta360 | | unchanged (from the previous table: torso (0.105, 0.105, 0.261) at 0.529, waist cover 268 × 200, shelf 0.69, `COF_LIFT` 0.020) |
| product payload | 2 × 3 kg | **≤ 1.5 kg per arm**, tray ≤ 2.1 kg |
| robot mass | 135.7 kg | **104.2 kg**, CoG (−0.013, 0.000, 0.462) |

## Open issues (honest list)

1. **Lateral stability** on a 338 mm track: 3.4–3.6 m/s². OK only with software acceleration limits (≤ 1.5 m/s²) and the 1.5 kg payload rating. Ranger Air braking deceleration is not published → measure it (PAYLOAD_TEST_PLAN.md).
2. **Power:** 600 W expansion (25 A, or 10 A per the plug table) vs arm peaks of about 720 W → arm power cap + 1.9 kg buffer (electrical lead). Runtime is about 2 h on 0.72 kWh (ESTIMATE). The base cuts the port below 10 % SOC.
3. **Dock:** contact type (brush plate) seen in the drawings, but the alignment method, NAVIS/navigation-version requirement, station price and height/depth are unknown. The coffee housing overhangs 54 mm behind the base above z 380.
4. **No external safety input on the Ranger Air** (as on every AgileX base). The PNOZ cuts the arm bus. The base stop is via CAN only → certification issue.
5. ASSUMED interfaces: deck hole thread, OpenArm plate/post/top holes, scanner hole chain.
6. Plan overhang: tray ±309 mm and coffee module beyond 552 × 500. Scanner fields must be taught with these.
7. Not modelled: cable routing, the navigation-version lidars (4 pucks on the top corners — they would conflict with our pods/adapter if the navigation version is required).

## Archive / history

- Tracer 2.0 design (column 150 mm stroke, 48 V pack, RoboPad dock, skirt): git commit **2660c92** — `cad/` files, VALIDATION.md (57 PASS / 17 WARN / 0 FAIL).
- BASE_DECISION.md (MiR) is superseded. BASE_OPTIONS.md now records the Ranger Air choice.

## Fastener check method (fasteners.py / validate.py)

- **Geometry per bolt** (128): every hole of the stack is a feature on its part; the check transforms them into the base frame and verifies parallel axes (≤ 0.5°), coaxiality (clearance holes: bolt must fit, (d_h − d)/2; tapped/insert/nut: ≤ 0.05 mm), contiguous clamped stack (gaps −0.05…0.25 mm), head seated (washer / counterbore), hole diameters (ISO 273 fine…coarse, tap drill d − P, Kerb Konus bore), engagement Le vs requirement (Al 6082-T6 ≥ 1.25 d, 6063/6060 ≥ 1.5 d, 5754 ≥ 1.6 d, purchased threads ≥ 0.7 d within the datasheet max insertion, inserts ≥ 0.9 L, nuts full height + 1 P protrusion, T-nuts full nut height) and bottoming in blind holes/inserts.
- **Edge distance**: OCC solid classification on growing circles around every hole at mid-depth (part locally cropped): e ≥ 1.2 d0 (EN 1999-1-1 minimum) in metal, wall ≥ insert spec in PA12. Purchased parts are not checked.
- **Loads**: for each joint group, the supported parts (mass/CoG from the CAD) under each load case give force F and moment M at the bolt-pattern centroid; per bolt f_i = F/n + θ × r_i with θ = J⁻¹M (polar), moments the pattern cannot carry (collinear bolts, single bolt) go to a contact-edge lever; tension = component pulling toward the support. Checks: F_V + Φ·T ≤ 0.9 F_proof; slip μ Σ(F_V − (1−Φ)T_i) ≥ 1.25 ΣV, else bolt shear ≤ 0.6 Rm As/1.25; female thread stripping 0.6 Rm·0.75·π d Le ≥ 1.25 (F_V + Φ T); insert pull-out ≥ 1.5 (F_V + T); T-nut allowable ≥ F_V + T. Torque T = 0.2 F_V d is reported per group.
