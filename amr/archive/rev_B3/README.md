# Giorgio AMR: our own mobile base (design rev B3, 2026-10-05)

Giorgio's own mobile base. It is built from certified safety modules plus laser-cut, bent and bolted parts. It turns on the spot,
carries and powers the whole robot, and docks to charge by itself. **Rev B has no waist joint** (owner decision): the 15 mm top deck
is the superstructure flange, at the same height as before (z = 353 mm). Everything above it is unchanged: torso, arms, head, coffee
module and tray.

Status: **design, not built.** The CAD (rev B3, `CAD_REV_B3.md`) has 160 parts and 0 interferences. 22 keep-out volumes
(battery top covers, Mean Well converters at their true sizes, castor swivel spaces) are checked against every part (3,086 pairs):
0 violated. The sprung castor carriages are swept over their travel (−2.5/+17 mm): 0 overlaps. The superstructure fits without
collisions. Calculations: 54 PASS / 6 WARN / 1 FAIL. The only FAIL is "OpenArm holding a cup by friction while driving", so objects
travel in the tray or a form-fit cradle. Electrical checks: 252 PASS / 0 FAIL (`electrical/CHECKS_AMR.md`, incl. CAD ↔ netlist
consistency). Every purchased-part technical value is SOURCED from a manufacturer document; what is left are type tests and price
quotes (end of this file).

![AMR rev B](renders/amr_hero.png)

## Why our own base
No base on the market meets all three requirements:
- payload of at least 85 kg;
- automatic charging confirmed by the manufacturer;
- at least 370 W of power for the superstructure.

The closest, Slamtec Poseidon Standard, publishes neither a dock nor a price (`../docs/BASE_DECISION_2026-10-05.md`). Our own base
gives a documented, certified safety chain for CE, and puts power and docking under our control. At 10 units it also costs less than
a commercial base with the same content (`INDUSTRIALIZATION.md`).

## Architecture (rev B)
| Item | Choice |
|---|---|
| Kinematics | Differential drive: 2 rigid drive wheels at the centre (track 464 mm) + 4 sprung castors **Blickle L-ALST 80K** (D80, 200 kg) at (±275, ±180), each on a HIWIN MGN15 guide with 2 × Gutekunst D-313J-02 springs (28.3 N/mm, 76 N preload, −2.5/+17 mm travel) in the spine/battery gap (`CASTOR_SUSPENSION.md`). Rotates on the spot. |
| Body | 780 × 560 mm with 45° corners, ground clearance 32 mm. 15 mm deck = superstructure flange at z 353. |
| Drives | 2× ez-Wheel SWD 125 (4:1, brake). Integrated STO SIL3/PL e; SBC, SLS, SDI SIL2/PL d; safe encoder. 24 V. |
| Battery | 2× Discover AES PRO DLP-GC2-48V in parallel: LFP 51.2 V, 3.07 kWh, IEC 62619 / UN 38.3 / CE. Each pack is under 2 kWh, so no EU battery passport is needed. Rev B2: each pack lies on its side with the top cover facing outward and 50 mm free in front of it (Discover manual 805-0027). Over-the-top straps hold it down, and it slides out at the front or rear. |
| Safety | 2× SICK nanoScan3 Pro I/O (PL d) on the front-right and rear-left castor-tower roofs; scan plane 184.5 mm (≤ 200 mm everywhere in the field incl. body pitch: per-band accel/decel limits, CALC §7b), continuous 40 mm slot all round. Safety controller: see `electrical/ELECTRICAL.md` (rev B, lowest-cost certified option). 3 E-stops, key service disconnect, reset, enabling-pendant socket. |
| Power | B48 bus 40–58.4 V: 100 A NH00 fuse, SW80B contactor + precharge. Traction 24 V from 2× DDR-480C-24 in parallel with ORing and a 27 V clamp. S24 always on. All DDR/DRDN converters are mounted vertically with their Mean Well keep-outs; one DIN position table for CAD and electrical (`electrical/din_layout.md`). K0V 48 V cut-off = Carlo Gavazzi DUB01CD48500V. LYNK II gateway (120 × 135 × 44) on a bracket in the right bay. The Jetson is on the deck at the rear, under cover K06. |
| Dock | Roboteq RoboPad at the rear (z 120, off-centre at y −137, clear of the rear battery keep-out). The dock holds an NPB-750-48 charger (EMC Class B, DIP preset 56.8/53.6 V), a DC contactor, a Carlo Gavazzi DUB01CD48500V over-voltage relay (58.5 V) and a controller; the pads stay dead until the Hall sensor and the CAN handshake both confirm docking. AprilTag + reflector, Nav2 Docking Server. |
| Cooling | 2 IP54 60 mm fans with filters per DIN bay: intake on the side covers above the wheel arch, exhaust high on the rear cover (y ±150). The centre bay is fed by 2 × 40 mm fans in the spine cut-outs, through the gaps beside the batteries. |

## Key numbers (`CALC.md`, rev B3)
- **Mass:** base 113.3 kg CAD (116.3 kg with harness; incl. 28 kg batteries, which also serve as ballast). Robot 160.5 kg empty, 168.6 kg loaded.
- **Load split:** each drive wheel carries 40.3 % of the weight (flat, empty); castor rating 200 kg @ 4 km/h vs 116 kg (×3 obstacle factor).
- **Tipping:** worst lateral 4.57 m/s² (the Ranger Mini was 3.65). The 1.5 m/s² tipping limits keep a safety factor of at least 2 in every arm pose; SS1 stop SF 3.07.
- **Speed:** SLS bands 0.3 / 0.8 / 1.2 / 1.5 m/s. Rotation on the spot up to 105°/s with the arms parked. Swept radius 440 mm.
- **Protective field:** 251 / 535 / 894 / 1240 mm at 0.3 / 0.8 / 1.2 / 1.5 m/s. Rotate-in-place field R 762 mm.
- **Accel / decel per band (scan plane ≤ 200 mm at the field edge):** 1.50/1.08, 1.22/1.00, 1.00/0.92, 0.81/0.86 m/s².
- **Thresholds:** sharp ≤ 10 mm at any speed; 10–20 mm only bevelled ≤ 1:2 at ≤ 0.3 m/s.
- **Runtime:** OpenArm logistics 14.9 h, barista 6.6 h. With certified Kassow arms, 6.7 / 3.0 h.
- **Charging:** 20 → 90 % takes **4.93 h** with the NPB-750-48 (11.3 A); the NPB-1700-48 option (C48 barista only) 1.89 h.
- **Deck:** 31 MPa and 0.44 mm under 2 g + braking (limits 160 MPa, 0.55 mm). Tower roof at the 815 N bump-stop load: 51 MPa.

## Operating rules that come from the design (go into the manual and the safety configuration)
1. Drive in reverse only at ≤ 0.3 m/s (SDI + SLS), which is used for docking. The cat-0 brake stop is grip-limited, with a safety factor of 1.31 against tipping in the driving poses, so use SS1 for every stop except power loss.
2. Never drive with the arms extended to the side or rear. Rotate on the spot only with the arms parked.
3. Objects travel in the tray or a form-fit cradle, not held by friction (CALC §8).
4. OpenArm variant: the arms move only while the protective field is clear. Hand-over happens through the tray.
5. Accel/decel limits per speed band (above) in the motion profile; scan plane checked with the test object at every field edge (184.5 ± 5 mm).
6. Floor: sharp thresholds ≤ 10 mm; 10–20 mm only bevelled ≤ 1:2 at ≤ 0.3 m/s. Castor preload 76 N per corner, set on a scale.

## Cost (`INDUSTRIALIZATION.md`, `bom_amr.csv`; mostly ESTIMATE)
| Variant | 1 unit | 10 units | 50 units |
|---|---|---|---|
| AMR alone incl. dock, materials + assembly | ≈ €25.0k | ≈ €21.1k | ≈ €18.6k |
| Giorgio R&D (OpenArm), materials + assembly | ≈ €37.2k | ≈ €32.1k | ≈ €28.5k |
| Giorgio with certified arms, materials + assembly | ≈ €90.6k | ≈ €81.3k | ≈ €74.0k |

The certified safety parts dominate the cost: 2 SICK nanoScan3 Pro I/O scanners (€2,394.95 each excl. VAT from a German distributor,
checked 2026-10-05) plus 2 system plugs NANSX-AAACZZZZ1 (€265.73 each), the Pilz PNOZmulti 2 station (B0 + 2 × EF 4DI4DOR + ES ETH,
€1,812.45 net + ≈ €90 terminals) and 2 safety wheel drives (€2.3k each). The castor parts (Blickle L-ALST 80K, HIWIN MGN15R/MGN15H)
have no published price: they are tagged QUOTE in `bom_amr.csv`. One-off CE and engineering costs (NRE) are on top: see `INDUSTRIALIZATION.md`.

## CE (`ce/`)
The route is **module A** (self-assessment, no notified body) under the Machinery Regulation (EU) 2023/1230, which applies from
20 Jan 2027. This holds as long as no machine-learning model performs a safety function.

Harmonised standards that apply:
- EN ISO 12100
- EN ISO 3691-4:2023 (base)
- EN ISO 10218-1/-2:2025 (arms)
- EN ISO 13849-1
- EN 60204-1
- EN ISO 13482 for the barista robot serving the public

Other legislation: RED (Wi-Fi) with EN 18031-1, EMC, and the Battery Regulation.

**Main blocker:** OpenArm has no brakes, which breaks MR Annex III 1.2.6(d). Fix it with brakes or spring balancing on J2/J4, or
switch to certified DC arms. The other gaps are listed in `ce/GAPS.md`.

## Folder map
| Path | What |
|---|---|
| `amr_params.py` | all dimensions, each tagged with its source |
| `amr_cad.py` | CadQuery model → `out/step`, `out/stl`, `out/dxf` (flat parts), `out/exploded`, `out/parts.json`; keep-outs → `out/keepout`, `out/keepouts.json`; checks → `out/interference.json` |
| `integrate.py` | checks the superstructure (`../cad/out/stl`) on the base → `out/integration.json` |
| `amr_calc.py` → `CALC.md` | mass, tipping, drives, energy, charging, safety fields, structure |
| `render_amr.py` → `renders/` | Blender renders: views, exploded, cables, dock, parts sheet |
| `electrical/` | netlist, single-line and safety diagrams, cable schedule, DIN layout, safety functions, checks |
| `ce/` | technical-file skeleton: risk assessment, essential requirements, test plan, DoC draft, manual outline, gaps |
| `INDUSTRIALIZATION.md`, `bom_amr.csv` | Italian suppliers, costs @1/@10/@50, timeline |
| `datasheet/` | product datasheet (HTML) |
| `CONTEXT.md` | shared assumptions for all work streams |
| `CAD_REV_B3.md` | rev B3: castor suspension in the CAD, DIN layout = electrical, LYNK II real size, K0V/XD3 part numbers, checks |
| `CASTOR_SUSPENSION.md` | castor suspension design (sources, stack-ups, loads) |
| `CAD_REV_B2.md` | rev B2 CAD changes and keep-out checks (installation rules of the batteries and converters) |
| `archive/rev_A/` | rev A (with the waist joint), kept for reference |
| `archive/rev_B1/` | rev B1 `amr_cad.py` / `amr_params.py`, before the rev B2 installation-rule rework |
| `archive/rev_B2/` | rev B2 files (.py, .md, BOM, electrical/, ce/) before rev B3 |

Run everything:
```bash
cd ~/giorgio_sim/amr
../cad/.env/bin/python amr_cad.py && ../cad/.env/bin/python integrate.py && ../cad/.env/bin/python amr_calc.py
python3 electrical/check_amr.py
~/tools/blender-4.5.9-linux-x64/blender -b -P render_amr.py -- --view hero --out renders/amr_hero.png
```

## Before pre-production (rev B3: no open supplier question)
1. **Price quotes:** Blickle L-ALST 80K (+ STEP), HIWIN MGN15R L190 / MGN15H, and the ESTIMATE rows of `bom_amr.csv`.
2. **Vendor CAD:** replace the ESTIMATE envelopes with vendor STEP files (SWD 125, castor, DIN modules) and re-run the checks; tight spots in `CAD_REV_B3.md` §1.
3. **Drawings:** 2D drawings with tolerances and holes for every bolted joint (the CAD carries the interfaces as notes). The M6 threads into the deck need ≥ 9 mm engagement.
4. **Prototype type tests:** TP-01…TP-23 (`ce/TEST_PLAN.md`), incl. TP-05/05b (scan plane static and while accelerating) and TP-23 (castor preload and suspension).
5. **Arms decision:** brakes on OpenArm, or certified DC arms.
