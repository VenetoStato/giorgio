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


## Results summary — Ranger Mini 3.0 design (VALIDATION.md has every number)

**57 PASS, 18 WARN, 0 FAIL.** The 18 WARN are:
- 10 bolt groups on ASSUMED purchased-part interfaces (rail slot and T-nut type, OpenArm plate/post/top holes, scanner holes, Gemini);
- 3 arm clearances under the 5 mm target (cup ring 2.4 mm, Gemini 3.1 mm, coffee machine 4.4 mm; 0 contacts in 793 poses);
- the plan overhang (scanner pods, tray, coffee shelf);
- the transient CoG while holding 2 × 3 kg (+22.9 mm);
- 3 tipping cases below the 0.5 g target. All are above the 3.3 m/s² floor (2.2 × the 1.5 m/s² commanded limit).

| Check | Result |
|---|---|
| **Payload (Ranger Mini 3.0: 120 kg; target ≤ 96 kg = 80 %, hard ≤ 108 kg)** | **PASS — superstructure 77.2 kg + product payload 8.1 kg (2 × 3 kg in the hands + 2.1 kg tray) = 85.3 kg = 71 % of 120 kg**, margin 34.7 kg |
| Extension CoG vs centre of rotation (±20 mm) | PASS nominal (+1.9, +3.2) mm, CoG 694 mm above the floor; WARN while holding 2 × 3 kg at 300 mm: +22.9 mm (transient) |
| Interference (858 pairs incl. 124 bolts, exact OCC), shuttle positions | PASS, 0 overlaps |
| Holes / ISO 273 / tap drills / engagement / edge distance (198 holes) | PASS |
| Bolt loads (all groups, 10 load cases incl. 0.5 g, +2 g bump, rebound) | PASS; 10 WARN = ASSUMED interfaces |
| body_link0 covered by the shells | PASS 100 % |
| Arm sweep (793 recorded poses: logistics + coffee at the 0.69 m shelf) | 0 contacts; link2 ≥ 10.3 mm from body_link0, ≥ 12.6 mm from the torso shell |
| Dock-receiver zones (front and rear centre, \|y\| ≤ 150, z ≤ 350, outside the body) | PASS — both free, because the AgileX kit position is UNVERIFIED |
| Footprint | WARN: plan envelope 864 × 864 mm with the corner pods (body 720 × 500); tray ±309 mm |
| **Tipping (wheels ±247 × ±182)** | nominal 5.38 / 5.31 / **3.90** / 3.98 m/s² (fwd/back/left/right); work 4.78 / 5.28 / 3.67 / 3.74; worst (arms fwd, 2 × 3 kg at 0.55 m) 4.33 / 5.67 / **3.65** / 3.72 |

**Required motion limits** (lateral is critical with the 364 mm track; worst lateral tip 3.65 m/s²; safety factor ≥ 2.2):
- **Linear acceleration/deceleration ≤ 1.5 m/s²**, e-stop included. The Ranger Mini braking value is not published → measure it (PAYLOAD_TEST_PLAN.md).
- **Lateral (centripetal) acceleration ≤ 1.5 m/s²**, i.e. turning radius ≥ v²/1.5: ≥ 0.67 m at 1.0 m/s and ≥ 1.5 m at 1.5 m/s.
- Speed ≤ 1.5 m/s (the ROS 2 driver default cap).
- Crab and diagonal motion: apply the same 1.5 m/s² vector limit.
- Spin in place: yaw rate ≤ 1.5 rad/s with the arms stowed (the extended-arm tip radius is about 0.6 m).

## Mass budget (kg; before = validated Tracer design, git 2660c92)

| Group | Tracer | Ranger Mini 3.0 | Note |
|---|---|---|---|
| mobile base | 55.0 | 75.0 | counts against nothing; payload 120 kg |
| OpenArm arms + body_link0 | 26.2 | 26.2 | unchanged |
| our 48 V pack 15s 30 Ah | 13.0 | 13.0 | restored (1.44 kWh) |
| electronics | 6.5 | 8.1 | 3 × DDR-480C (2 arm DC-DCs + coffee), S24/CPU/5 V DC-DCs, Orion-Tr 48/48-6 isolated charger from the base 48 V output (1.3 kg), PNOZ, 2 contactors, Jetson module, Ethernet switch |
| column (foot + profile + bracket) | 6.5 (telescopic) | 4.8 (fixed) | the rails are at 345 mm, so only 207 mm of column fits under the torso; no stroke possible |
| adapter plate | 6.0 | 5.9 | 8 mm 6082 on the 2 rails (16 × M5 into T-nuts) |
| shells | 5.0 | 4.3 | aluminium sheet deck cover (cheaper than SLS) + PA12 waist/torso/head/column/coffee covers |
| coffee module + tray | 7.4 | 7.1 | unchanged geometry |
| scanner pods + 2 × nanoScan3 | 1.9 | 1.9 | kept (our safety chain) |
| other (brackets, wiring 2 kg, fasteners) | 8.2 | 6.9 | |
| **robot total** | **135.7** | **152.2** | |
| **superstructure + product payload** | **88.8** | **85.3** = 71 % of 120 kg | |

## What the design is now (Ranger Mini 3.0, z in mm)

| z | Element |
|---|---|
| 0–329 | AgileX RANGER MINI 3.0: body 720 × 500, ground clearance 105. 4 steerable wheels Ø200 at (±247, ±182). Deck plate 329 + 2 T-slot rails 230 mm apart, top at 345 |
| 345–353 | **P01 adapter** 8 mm 6082, 16 × M5 countersunk into slot-6 T-nuts (rail type ASSUMED) |
| 353–470 | battery tray + 15s 30 Ah pack (front); side e-plates (2 × DDR-480C, PNOZ on DIN, K1/K2); rear e-plate (Jetson module, Orion-Tr charger); all under the **SH01 deck cover** (1.5 mm aluminium, powder coated) |
| 353–565 | fixed column: P29 foot + item 80×80 L profile 197 mm + P02 → torso origin at 580, shoulders at 1278 (as validated) |
| 129–331 | 2 × nanoScan3 pods outside the front-right / rear-left corners at (±359.7, ∓359.7), scan plane 180 |
| 474–942 | coffee module (shelf 0.69 m, unchanged); housing from 474; backpack e-plate (coffee DDR-480C, small DC-DCs, switch) hung under the shelf on 3 standoffs |
| 580–1660 | unchanged: OpenArm torso + arms, waist cover, torso shell, head, Gemini, Insta360, chest tray |

## Cost drivers (custom parts, prototype qty 1, EU job shops — ESTIMATE ±40 %, no quotes yet)

| Part | Process | € (est.) |
|---|---|---|
| P01 adapter plate | waterjet 8 mm 6082 + 48 holes / countersinks | 180 |
| P29 column foot | CNC 20 mm | 110 |
| P02 column-to-torso bracket | waterjet 20 mm + 1 CNC set-up (lightening pockets removed for cost) | 150 |
| P03/P04/P05 battery tray, pad, hold-downs | laser + bend, die-cut EPDM | 100 |
| P06/P07/P08/P30 electronics plates | laser 2 mm + PEM | 80 |
| P09 scanner pods ×2 | laser + bend 3 mm | 90 |
| SH01 deck cover | laser + bend 1.5 mm, powder coat (**instead of SLS ≈ 550 €**) | 160 |
| SH02 column cover, SH03 waist cover | SLS/MJF PA12, 2 halves each | 320 |
| SH04a/b torso shell | MJF PA12 2 halves, painted | 450 |
| SH05 head shell | MJF PA12, painted | 140 |
| SH06 coffee housing | SLS/MJF PA12 | 380 |
| P20 tray halves ×2, P24, P26 | MJF PA12 | 285 |
| P17 Insta360 mast | CNC turned + milled | 60 |
| P21 shelf, P22 uprights, P23, P25 | waterjet 6 mm / bent 2 mm | 145 |
| small sheet brackets (P16, P18, P19, P27, P28) | laser + bend | 105 |
| standoffs | catalogue hex standoffs | 25 |
| **total custom parts** | | **≈ 2,800 €** (+ fasteners/inserts ≈ 120 €) |

| Cost-down option | € saved | Impact |
|---|---|---|
| **Done:** deck cover in bent aluminium instead of SLS | ≈ 390 | +1.2 kg; flat-faceted look |
| **Done:** no lightening pockets on P02; catalogue standoffs | ≈ 80 | +0.6 kg |
| Coffee housing as bent aluminium/PC sheet box | ≈ 230 | less organic look |
| Waist cover as bent sheet box | ≈ 150 | look |
| Torso/head shells in MJF instead of SLS and unpainted dyed black | ≈ 200 | finish |
| P29 foot → item standard base plate for profile 8 80×80 (P/N to confirm) | ≈ 70 | ASSUMED availability |
| Mast → standard Ø14 tube + printed foot | ≈ 40 | none |
| **Series (≥ 20 units):** thermoformed ABS shells on 3D-printed moulds | ≈ 50 % of shell cost | moulds ≈ 1.5 k€ |

## Real vs assumed (Ranger Mini 3.0 specific; the rest as in SOURCES.md)

**SOURCED** (manual + ROS params; data in BASE_OPTIONS.md section 0):
- 720 × 500 mm, 75 kg, payload 120 kg, CoG 213 mm, payload centroid at the rotation centre;
- wheels Ø200 at 494 × 364;
- 2 rails 230 mm apart, top 345;
- 48 V 24 Ah; rear output 46–50 V ≤ 15 A / 720 W (cut below 10 %);
- onboard e-stop only;
- price €12,480 excl. VAT.

**ASSUMED / UNVERIFIED:**
- rail profile, slot and T-nut type (16 M5 at 0.6 N·m); rail width 40 mm;
- charging-kit receiver position (front and rear zones kept free) and the kit/NAVIS price and licence;
- braking deceleration;
- peak output current;
- Orion-Tr envelope (fits a 150 × 100 slot? confirm);
- contactor envelope (45 × 60 × 80).

## Proposed changes to the sim model (exact values, metres)

| Item | Sim now (Tracer) | Ranger Mini 3.0 design |
|---|---|---|
| base body | box 0.702 × 0.61 × 0.25, diff drive + casters, 55 kg | **0.720 × 0.500, z 0.105–0.329 (+ 2 rails 0.04 wide at y ±0.115, top 0.345), 75 kg, CoG z 0.213** |
| wheels | 2 drive + 4 casters | **4 steerable drive wheels Ø0.200 at (±0.247, ±0.182)**; 4WS modes (Ackermann, crab, spin); speed ≤ 1.5 m/s; **accel/decel and lateral accel ≤ 1.5 m/s²** |
| base fixed mass (not visual, on `amr`) | 46.2 kg | **46.6 kg at (−0.011, 0.006, 0.445)** (pack, electronics, adapter, pods, deck cover, coffee module, column foot) |
| battery | 15s 30 Ah | unchanged 15s 30 Ah (1.44 kWh) + base 48 V 24 Ah (1.15 kWh); the Orion-Tr charges our pack from the base output; the AgileX station charges the base |
| docking | RoboPad nose 0.406 | **AgileX charging kit (NAVIS); receiver position UNVERIFIED**; assume a rear approach as on the Ranger Air (contacts at the rear face centre, z ≈ 0.12–0.18). Front and rear zones are kept free |
| column | telescopic, stroke 0.15 | **fixed** (`COLUMN_STROKE` 0): profile z 0.368–0.565 (1.05 kg), foot 1.25 kg at z 0.363; torso origin 0.580 unchanged |
| `SCANNERS` | Tracer pods | **(0.3597, −0.3597) −45°, (−0.3597, 0.3597) 135°**, `SCAN_Z` 0.18 |
| shells | skirt + bands + bumper | **removed**; deck cover box 0.718 × 0.498, z 0.329–0.470 (pod corner cut-outs); column cover 0.12 × 0.12, z 0.47–0.54; coffee housing from z 0.474 |
| torso, waist, head, tray, coffee module | | unchanged (torso shell (0.105, 0.105, 0.261) at 0.529; waist 268 × 200; shelf 0.69; `COF_LIFT` 0.020) |
| product payload | | 3 kg per arm, tray 2.1 kg |
| robot mass | 135.7 kg | **152.2 kg**, CoG (−0.002, 0.002, 0.453) |

## Open issues (honest list)

1. **Lateral stability**: the motion limits above are mandatory. Ranger Mini braking is unknown → measure it before integration.
2. **Charging kit**: price, licence, receiver position, current; whether the payload output stays live while docked (our Orion-Tr charges the pack from it); NAVIS dependence.
3. **No external safety input** on the base: our PNOZ stops the arms, but the base stops via CAN only → certification issue.
4. **Power**: the base output is 720 W / 15 A. The Orion-Tr draws ≈ 6 A at 48 V while docked; peaks run from our own pack.
5. **ASSUMED interfaces**: rail T-nut type and allowable, OpenArm holes, post slots, scanner holes.
6. **No column adjustment** (geometric impossibility with shoulders at 1.278 m and the rails at 0.345 m).
7. **Not modelled**: cable routing, the NAVIS computer/lidars if the charging kit requires them.

## Fastener check method (fasteners.py / validate.py)

- **Geometry per bolt** (128): every hole of the stack is a feature on its part; the check transforms them into the base frame and verifies parallel axes (≤ 0.5°), coaxiality (clearance holes: bolt must fit, (d_h − d)/2; tapped/insert/nut: ≤ 0.05 mm), contiguous clamped stack (gaps −0.05…0.25 mm), head seated (washer / counterbore), hole diameters (ISO 273 fine…coarse, tap drill d − P, Kerb Konus bore), engagement Le vs requirement (Al 6082-T6 ≥ 1.25 d, 6063/6060 ≥ 1.5 d, 5754 ≥ 1.6 d, purchased threads ≥ 0.7 d within the datasheet max insertion, inserts ≥ 0.9 L, nuts full height + 1 P protrusion, T-nuts full nut height) and bottoming in blind holes/inserts.
- **Edge distance**: OCC solid classification on growing circles around every hole at mid-depth (part locally cropped): e ≥ 1.2 d0 (EN 1999-1-1 minimum) in metal, wall ≥ insert spec in PA12. Purchased parts are not checked.
- **Loads**: for each joint group, the supported parts (mass/CoG from the CAD) under each load case give force F and moment M at the bolt-pattern centroid; per bolt f_i = F/n + θ × r_i with θ = J⁻¹M (polar), moments the pattern cannot carry (collinear bolts, single bolt) go to a contact-edge lever; tension = component pulling toward the support. Checks: F_V + Φ·T ≤ 0.9 F_proof; slip μ Σ(F_V − (1−Φ)T_i) ≥ 1.25 ΣV, else bolt shear ≤ 0.6 Rm As/1.25; female thread stripping 0.6 Rm·0.75·π d Le ≥ 1.25 (F_V + Φ T); insert pull-out ≥ 1.5 (F_V + T); T-nut allowable ≥ F_V + T. Torque T = 0.2 F_V d is reported per group.
