# Giorgio — mechanical CAD (parametric, validated)

Parametric CadQuery model of every part we must manufacture for Giorgio (mobile bimanual service robot), with the
purchased parts as datasheet envelopes (or the official mesh), every bolted joint specified, and a headless validator that
checks interference, clearances, fits, fasteners, mass and tipping. Results are in **[VALIDATION.md](VALIDATION.md)**
(regenerated on every run); sources in **[SOURCES.md](SOURCES.md)**; processes and assembly sequence in
**[MANUFACTURING.md](MANUFACTURING.md)**.

Frame and units everywhere: millimetres, robot base frame = MuJoCo `amr` body (origin on the floor at the Tracer centre,
x forward, y left, z up), column lift = 0, coffee shuttle retracted ("out").

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

## Results summary (last run — see VALIDATION.md for every number)

**57 PASS, 17 WARN, 0 FAIL** (2026-10-03, after the mass-reduction pass and the coffee shelf raised to 0.69 m as the lead
asked; base decision in **[BASE_DECISION.md](BASE_DECISION.md)**). Of the 17 WARN:
- 12 are joint groups that rely on an ASSUMED purchased-part interface; they pass with the assumed values.
- 3 are arm clearances under the 5 mm target: cup ring 2.4 mm, Gemini camera 3.1 mm, coffee machine 4.4 mm. The 3 poses where the fingers touch the machine top to press the button are intended contacts and are excluded.
- 1 is the transient extension CoG while holding 2 × 3 kg at 300 mm.
- 1 is the worst-case forward tipping margin (0.46 g at lift 150 with 2 × 6 kg at full reach).

| Check | Result |
|---|---|
| **Payload, HARD (Tracer manual p.3: ≤ 100 kg; target ≤ 90 kg)** | **PASS — superstructure 80.7 kg + product payload 8.1 kg (2 × 3 kg in the hands + 2.1 kg in the tray) = 88.8 kg** (was 99.2 kg before; FAIL is raised automatically above 100 kg, WARN above 90 kg). With the OpenArm *peak* 2 × 6 kg it would be 92.7 kg (info) |
| **Extension CoG vs centre of rotation (±20 mm)** | PASS nominal (+4.5, +1.2) mm; WARN while holding 2 × 3 kg at x = 300 mm (+24.4 mm, transient). Centre of rotation ASSUMED at the plan centre |
| Interference, all part pairs incl. 128 bolts/washers/nuts, exact OCC boolean | PASS — 987 pairs at lift 0, 328 moving pairs at lift 150 + shuttle under the spout, and at mid-stroke: 0 overlaps |
| Hole alignment / ISO 273 / tap drills / insert bores / stack contiguity | PASS — 128 bolts, offset 0.000 mm, 0.00°, gaps 0.00 mm |
| Thread engagement, bottoming, protrusion | PASS — min Le/required 1.00 |
| Edge distance | PASS — 203 holes |
| Bolt loads: 31 groups, 10 load cases (incl. 0.5 g, +2 g bump, rebound, Tracer e-stop 2.2 m/s², 2 × 6 kg at reach, shoulder peak torques) | PASS on all; 12 groups WARN only because the interface is ASSUMED |
| body_link0 covered by the shells (lead's request) | PASS — base plate 100 % inside the waist cover; top z 1310–1353, \|y\| ≤ 68: 100 % inside the torso shell / under the neck plate |
| Arm sweep: 793 poses (logistics recording + the **new coffee recording with the shelf at 0.69 m**, `cad/data/rec_caffe_sh069.pkl`), 23 parts | PASS on 20 parts, 0 contacts; link2 ≥ 10.3 mm from body_link0, ≥ 12.6 mm from the torso shell, coffee housing ≥ 26.6 mm; WARN cup ring 2.4 mm, Gemini 3.1 mm, machine 4.4 mm (plus 3 intended button-press contacts) |
| Coffee shuttle stroke | PASS — 2.0 mm min |
| Footprint | PASS (upper body in the skirt outline); plan envelope 832 × 832 mm because of the scanner pods |
| Tipping (support ±281 × ±255 mm) | nominal 7.28 / 7.26 / 6.58 / 6.62 m/s²; work (2 × 4.1 kg) 6.22 / 7.02 / 5.99 / 6.03; worst 4.53 / 6.84 / 5.14 / 5.17 → every case ≥ Tracer e-stop 2.2 m/s²; ≥ 0.5 g except worst-forward (WARN) |

### Mass budget before → after (kg)

| Group | Before | After | How (real change, re-validated) |
|---|---|---|---|
| 48 V battery | 17.0 | **13.0** | 15s 40 Ah 1.92 kWh → **15s 30 Ah LFP, 48 V nominal, 1.44 kWh**, flat pack 270 × 400 × 75 mm (ESTIMATE) |
| base adapter plate | 8.97 | 6.03 | 10 → 8 mm 6082-T6 + 5 more lightening windows. The column foot is now **tapped in its own 12 mm flange** and bolted from below (DIN 7984 M8 × 20) |
| shells | 6.63 | 5.02 | SLS PA12: skirt 3.0 → 2.5 mm; torso, waist, column cover, head, coffee housing 3.0 → 2.0 mm |
| column sleeve | 3.13 | 2.40 | tube 100×100×5 → 100×100×3 (EN 755-2), POM liners 6.8 mm |
| column-to-torso bracket | 2.18 | 1.82 | underside pockets, 6 mm web |
| bumper, e-plates, coffee uprights | — | −0.9 | thinner EPDM profile; 3 → 2 mm sheet |
| **robot total** | **146.1** | **135.7** | |
| superstructure (− Tracer 55 kg) | 91.1 | **80.7** | |
| + product payload 8.1 kg | 99.2 | **88.8 ≤ 90** | |

Product payload definition (to be written in the product spec and enforced in software): **≤ 3.0 kg object per arm**
(the OpenArm gripper is already in the arm mass; OpenArm rates 4.1 kg nominal *including* the end effector). The chest tray
holds ≤ 2.1 kg (6 × 0.35 kg flasks). The tasks in the sim handle 0.15–0.35 kg.

### Values the electrical design must adopt / recheck
- Battery **15s 30 Ah LiFePO4, 1.44 kWh** (was 40 Ah, 1.92 kWh). The mechanical envelope is 270 × 400 × 75 mm, ≤ 13 kg incl. BMS and case, in tray P03 at x 49…319, y ±200, z 182…257.
  Autonomy at 250 W typical: 1.44 kWh × 0.9 / 250 W ≈ **5.2 h** (was ≈ 6.9 h). Recharge 30 → 80 % at 25 A takes ≈ 35 min.
  Peak current to recheck: arms ~720 W + Jetson + Tracer charger on 1C (30 A) cells.
- Mean Well DDR-480C ×2 lying on 2 mm plates inside the skirt: check the convection derating.
- The Tracer has **no external safety input**. The PNOZ can only cut the arm bus; the base stops via CAN (not safety-rated) — see BASE_DECISION.md.
- Tracer charging is a 2-pin plug, 10 A. Size the 48 → 24 V Tracer charger at ≤ 10 A.

## What the design is (stack-up, lift 0)

| z (mm) | Element |
|---|---|
| 0–169 | AgileX Tracer 2.0 (octagon from the manual drawing; two top rails 230 mm apart, top at 169 = ASSUMED rail top) |
| 169–177 | **P01 base adapter plate**, 8 mm 6082-T6 with lightening windows, 16 × M5×16 countersunk into slot-6 T-nuts in the Tracer rails (x position free along the rails) |
| 177–300 | battery tray P03 with the 48 V 30 Ah pack (front), 3 electronics plates P06/P07/P08 (DC-DCs, PNOZ on DIN rail, contactors, Jetson, Tracer charger), column foot, coffee uprights, 6 skirt standoffs; all under the **SH01 base skirt** (top 300, open bottom at 56, EPDM bumper 40–76) |
| 177–555 | **W01 column sleeve**: 12 mm flange (8 × M8 tapped, bolted from under P01 before P01 goes on the Tracer) + 100×100×3 tube, POM liners at the top, M10 clamp levers on a gib strip, GN 617 index plunger every 25 mm |
| 195–565 (+lift) | **S01 item Profil 8 80×80 leicht**, 370 mm, POM guide pads at its bottom; telescopes 0–150 mm |
| 560–580 (+lift) | **P02 column-to-torso bracket**, 20 mm 6082, 80×80 spigot pocket + 1 × M12 DIN 7984 into the profile core; 8 × M6 from below into the OpenArm body_link0 plate (free grid holes (75, ±15/±75), (−135, ±45/±75)) |
| 580–1353 (+lift) | OpenArm 2.0 body_link0 + 2 arms (official), waist cover SH03 (hung on P02), torso shell halves SH04a/b (on post brackets P27/P28), chest tray (carrier P19 on the post, 2 MJF halves on locating pins = quick release), Gemini 336L on P18 |
| 1353–1660 (+lift) | neck plate P16 + mast P17 on top of body_link0 (ASSUMED holes), head shell SH05 on 4 inserts, Insta360 X4 |
| 684–942 | coffee backpack (shelf top at **0.69 m**): 6 mm shelf P21 on 2 sheet-metal C-uprights P22 from P01, Inissia envelope, MGN12 rail + carriage, MJF cup carrier P24, Actuonix P16-150, cup-stack holder P26, housing SH06 (open toward the column, the waist cover closes it) |

Key decisions (why):
1. **Column stroke 150 mm, not 400.** With the torso at z = 580 at lift 0, a telescope needs inner length ≤ 565 − 195 = 370 mm; keeping ≥ 200 mm engagement in the sleeve gives ≤ 160 mm stroke. A 400 mm stroke with this torso height is not physically realisable with a top-mounted torso (any "slide + clamp" on the side would put the column through body_link0's 250 × 190 plate).
2. **Scanners in corner pods outside the Tracer outline, scan plane kept at 180 mm.** The nanoScan3 scan plane is 50.5 mm above its base; on top of the Tracer the plane would be ≥ 230 mm, too high for the ISO 3691-4 lying test piece (Ø200 mm). The pods sit outside the Tracer chamfers (centres (346.7, −346.7) and (−340.7, 340.7)), which grows the plan envelope to ≈ 832 × 832 mm at those two corners.
3. **Shells re-proportioned to the real hardware** (sim shells are visual only and intersect the arms/hardware): torso a = b = 105 mm (was 135 × 170, centre x −30 → 0) so that arms hanging and reaching back to the coffee module clear it by ≥ 9 mm; base skirt e1 0.15 (was 0.28) so its lower part clears the Tracer octagon; column cover split into a fixed cover and a waist cover that moves with the torso; coffee housing becomes a rounded box open toward the column.
4. Electronics and battery have a real place and mass (46.2 kg fixed on the base besides the Tracer).
5. Mass budget kept ≤ 90 kg incl. product payload (see above); the base choice is discussed in BASE_DECISION.md (prototype on Tracer 2.0, product on MiR250).

## Real vs assumed

SOURCED (datasheet / manual / official files, see SOURCES.md): Tracer 702×610×169, 580 body, 2 rails 230 apart, mass, 100 kg
(manual) / 150 kg (datasheet) payload, braking; OpenArm body_link0 geometry, 30 mm hole grid, masses, payload 4.1/6.0 kg;
nanoScan3 housing, scan plane 50.5, M5×7.5 side threads 44 apart, 0.67 kg; Gemini 336L size, 2 × M4 95 mm apart (max 4 mm,
0.4 N·m), 135 g; Insta360 X4; item 80×80 L 5.33 kg/m, Ix 134 cm⁴; T-nut item 8 M8 5 kN; Inissia 119×320×229, 2.4 kg;
Roboteq RPCOL90-100 74×56 pattern; Kerb Konus 860 insert bores/lengths/walls; ISO 273/898-1 tables; Mean Well DDR-480C, Pilz PNOZ m B0,
Jetson mass; Actuonix P16-150.

ASSUMED / ESTIMATE (must be confirmed before ordering — each is flagged in params.py and in the joint table):
- Tracer rail profile (slot 6, M5 T-nuts, 1000 N allowable), rail height 20 mm (the column-foot bolt heads under P01 need ≥ 12 mm between P01 and the Tracer deck), plan octagon measured on the drawing (±3 mm), CoG height 80 mm, which end is the front.
- OpenArm base plate thread: docs say **M6 taps**, the official STL draws **Ø5.5** holes. Design uses M6×30 from below; if the holes are Ø5.5 clearance, use M5×35 + nuts on top (same 8 positions, all have > 600 mm free above).
- body_link0 post T-slots (front/rear, "Misumi series 6 slot 8") for the tray carrier, Gemini and torso-shell brackets; holes on the top of the shoulder block for the neck plate (4 × M4).
- nanoScan3 side-hole positions (reading of the dimension chain), scanner rear plug 15 mm.
- 48 V 30 Ah LFP pack (15s) as a custom flat pack 270 × 400 × 75 mm, 13 kg (commercial 48 V packs are ~200 mm tall and would not fit under the skirt).
- Tracer centre of rotation at the plan centre (not shown on the manual drawing; measure on the unit). Tracer payload: manual 100 kg (binding), web page 80 kg, datasheet 150 kg — get it in writing.
- Contactor and Tracer-charger envelopes; insert pull-out forces (1.0/1.5/2.0 kN for M3/M4/M5 — not published, test them); item core bore Ø10.2; Inissia cup recess (625–735 mm); P16 section 20 × 26.
- Bolt-load model parameters: Φ = 0.2, μ = 0.15, K = 0.2, docking push 200 N, person leaning on the skirt 300 N.

## Proposed changes to the sim model (exact values, base frame, metres)

The sim files were not modified. To make `giorgio_model.py` / `shells.py` match the CAD:

| Item | Sim now | CAD value |
|---|---|---|
| `COLUMN_STROKE` | 0.40 | **0.15** (index positions every 0.025) |
| `column_inner` geom (body `column`, origin z 0.30) | box half (0.04, 0.04, 0.2) at z +0.2, 6.0 kg | half (0.04, 0.04, 0.185) at z **+0.080** (profile z 0.195–0.565), **1.97 kg** |
| fixed sleeve (new geom on `amr`) | — | box half (0.05, 0.05, 0.189) at (−0.06, 0, 0.366), **2.40 kg** (flange + 100×100×3 tube) |
| `torso_link0` mass | 8.0 | **13.89** (URDF) |
| base payload mass (new, on `amr`, not visual) | 0 (battery/electronics are visual only) | **46.2 kg at (−0.002, 0.002, 0.281)** = everything fixed on the base except the Tracer, incl. battery, coffee module, scanners, skirt (from `out/mass_properties.json`) |
| `pw_battery` | half (0.20, 0.11, 0.04) at (−0.10, 0, 0.245) | half (0.135, 0.20, 0.0375) at (**0.184, 0, 0.2195**), 13 kg (15s 30 Ah, 1.44 kWh — battery model in the sim: capacity 1.44 kWh) |
| `SCANNERS` | ((0.321, −0.275), −45°), ((−0.321, 0.275), 135°) | ((**0.3467, −0.3467**), −45°), ((**−0.3407, 0.3407**), 135°); `scanner{k}_body` half (0.050, 0.051, 0.040) — `SCAN_Z` 0.18 unchanged |
| charge pads | 2 at (0.378, ±0.06, 0.14) | RoboPad: contact face at x **0.406**, poles at y **±0.020** (40.5 mm apart, ASSUMED same as the studs), z 0.14; robot nose is now at x 0.406 |
| `shells.py` `base_skirt` | (0.375, 0.33, 0.125, e1 0.28, e2 0.30), pos z 0.165 | (0.375, 0.33, **0.130**, e1 **0.15**, e2 0.30), pos z **0.170**, cut below z 0.056 (same for `scan_band`, `led_band`, `tricolor_band`) |
| `shells.py` `torso` | (0.135, 0.17, 0.235, e1 0.45, e2 0.5, taper), pos (−0.03, 0, PED_TOP − 0.195) | (**0.105, 0.105, 0.261**, same e1/e2/taper law), pos (**0.0, 0, 0.529** in the torso frame), 2 mm wall, open below torso-z 0.312 and above **0.771** (the head, bottom at 0.776, closes it), shoulder openings = cylinders r 0.082 along y about (0, ±y, 0.698) for \|y\| ≥ 0.058. Covers body_link0 up to its top (0.773) incl. the part sticking out in the sim; ≥ 10.3 mm from link2 in all 833 recorded poses |
| `column_neck` cover | one superellipsoid 0.285–0.885 (does not cover the 0.25 × 0.19 body_link0 plate) | fixed cover 180 × 200 mm (r 45) world z 0.300–0.540 centred x −0.06 on `amr` + **waist cover 268 × 200 mm (r 8) centred x −0.028, world z 0.562–0.838 at lift 0, on `torso`** — contains the whole body_link0 base plate |
| coffee housing | superellipsoid (0.112, 0.12, 0.31) at (−0.255, 0.058, 0.615) | rounded box x −0.330…−0.166, y −0.135…0.205, z **0.380…0.942** (as now in the sim), 2 mm wall, open toward the column, open on the spout side, **open on top over the head/buttons** (x −0.295…−0.161, y −0.135…−0.045, z above 0.889) |
| Inissia meshes | 0.12 × 0.31 × 0.30 m, buttons at sh + 0.301 | real 0.119 × 0.320 × 0.229 m: machine x −0.2895…−0.1705, y −0.130…0.190, top (buttons) at **sh + 0.229 = 0.919** (shelf `COF_SH` **0.69**, adopted from the lead) |
| `COF_LIFT` (shuttle) | 0.09 | **0.020** (plate top at **0.720**; cup ≤ 85 mm tall under the spout at ~0.815–0.840) |
| cup-stack ring | h 0.07 | h **0.045** with two 44 mm finger slots on ±x (through the floor), stack top at sh + 0.12 = 0.81 |
| robot mass | 88.6 kg | **135.7 kg**, CoG (0, 1, 376) mm at lift 0 (re-run `stability_test.py` and the braking-distance limits) |
| product payload in tasks | — | ≤ 3.0 kg per arm (software limit), tray ≤ 2.1 kg |

## Open issues (honest list)

1. **Footprint growth at two corners** (scanner pods): plan 832 × 832 mm vs the sim skirt 762 × 672. The alternative (scanners on top of the Tracer, plan unchanged) puts the scan plane at ~230 mm, which fails the ISO 3691-4 lying-person test piece. A custom chassis or a Tracer with lower scanner mounts would remove this. Scanner fields must also tolerate the skirt 13 mm inside the beam origin line along the sides (contour teach).
2. **Payload / base:** resolved for the prototype: 88.8 kg ≤ 90 kg incl. product payload, CoG centred. Remaining:
   - the AgileX web page says 80 kg;
   - the centre of rotation is assumed;
   - **the Tracer has no external safety-stop input**, which blocks certification.

   Verdict in BASE_DECISION.md: keep the Tracer for the prototype; the sellable product goes on the MiR250, with the Robotnik RB-THERON+ as second choice.
3. ASSUMED purchased interfaces (Tracer rail slot/T-nut capacity, OpenArm plate thread, post slots, top-of-torso holes, scanner hole chain): the corresponding joints are WARN until checked on the real parts or the vendors' CAD. The Tracer rail joint was designed for a 1000 N T-nut allowable, hence the low torque (0.6 N·m) — with real item/Bosch slot-6 nuts this can be raised.
4. Coffee module: resolved with the lead. The shelf is at 0.69 m in both CAD and sim, and the coffee poses were re-recorded (`cad/data/rec_caffe_sh069.pkl`); the old `caffe_v9`/`espr_v9` recordings are superseded and no longer used. The C-uprights are now 504 mm long (2 mm sheet; bolt loads pass, no FEA). The housing starts at 0.38 m, so 80 mm of the uprights are visible above the skirt, as in the sim. The machine envelope is a box: the button-press contact is accepted within the top 25 mm on the spout side.
5. 230 V capsule machine needs an inverter (~1.5 kW) that has no place in the base; the CAD assumes the 24 V DC machine option or a later redesign (see docs/alimentazione_e_certificazione.md, decision 2).
6. Arm sweep uses the recorded missions at lift 0 only; Gemini (3.1 mm) and cup ring (4.4 mm) are below the 5 mm target. Self-collision arm–arm is not checked here (the sim handles it).
7. Not modelled: pauldrons, face visor/eyes/moustache, LED bands, cable routing and the column cable chain, rear hatch in the skirt for the Tracer power switch/charging port, ventilation of the DC-DCs mounted lying (derating), tongue-and-groove seams of the shell halves, the skirt's 4-segment split.
8. Loads are quasi-static (0.5 g, 3 g) with a simple elastic bolt-group model; no fatigue, no FEA of plates/brackets (plate bending under the column foot and the sheet-metal brackets should get a quick FEA before release).

## Fastener check method (fasteners.py / validate.py)

- **Geometry per bolt** (128): every hole of the stack is a feature on its part; the check transforms them into the base frame and verifies parallel axes (≤ 0.5°), coaxiality (clearance holes: bolt must fit, (d_h − d)/2; tapped/insert/nut: ≤ 0.05 mm), contiguous clamped stack (gaps −0.05…0.25 mm), head seated (washer / counterbore), hole diameters (ISO 273 fine…coarse, tap drill d − P, Kerb Konus bore), engagement Le vs requirement (Al 6082-T6 ≥ 1.25 d, 6063/6060 ≥ 1.5 d, 5754 ≥ 1.6 d, purchased threads ≥ 0.7 d within the datasheet max insertion, inserts ≥ 0.9 L, nuts full height + 1 P protrusion, T-nuts full nut height) and bottoming in blind holes/inserts.
- **Edge distance**: OCC solid classification on growing circles around every hole at mid-depth (part locally cropped): e ≥ 1.2 d0 (EN 1999-1-1 minimum) in metal, wall ≥ insert spec in PA12. Purchased parts are not checked.
- **Loads**: for each joint group, the supported parts (mass/CoG from the CAD) under each load case give force F and moment M at the bolt-pattern centroid; per bolt f_i = F/n + θ × r_i with θ = J⁻¹M (polar), moments the pattern cannot carry (collinear bolts, single bolt) go to a contact-edge lever; tension = component pulling toward the support. Checks: F_V + Φ·T ≤ 0.9 F_proof; slip μ Σ(F_V − (1−Φ)T_i) ≥ 1.25 ΣV, else bolt shear ≤ 0.6 Rm As/1.25; female thread stripping 0.6 Rm·0.75·π d Le ≥ 1.25 (F_V + Φ T); insert pull-out ≥ 1.5 (F_V + T); T-nut allowable ≥ F_V + T. Torque T = 0.2 F_V d is reported per group.
