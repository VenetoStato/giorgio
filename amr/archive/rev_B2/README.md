# Giorgio AMR: our own mobile base (design rev B2, 2026-10-05)

Giorgio's own mobile base. It is built from certified safety modules plus laser-cut, bent and bolted parts. It turns on the spot,
carries and powers the whole robot, and docks to charge by itself. **Rev B has no waist joint** (owner decision): the 15 mm top deck
is the superstructure flange, at the same height as before (z = 353 mm). Everything above it is unchanged: torso, arms, head, coffee
module and tray.

Status: **design, not built.** The CAD (rev B2, `CAD_REV_B2.md`) has 130 parts and 0 interferences. 14 keep-out volumes
(battery top covers, Mean Well converters) are checked against every part, and 0 are violated. The superstructure fits without collisions.
Calculations: 44 PASS / 7 WARN / 1 FAIL. The only FAIL is "OpenArm holding a cup by friction while driving", so objects travel in
the tray or a form-fit cradle. Electrical checks are in `electrical/CHECKS_AMR.md`. Values tagged ESTIMATE/ASSUMED must be closed
with suppliers before any order (see the end of this file).

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
| Kinematics | Differential drive: 2 rigid drive wheels at the centre (track 464 mm) + 4 spring-loaded castors D100. Rotates on the spot. |
| Body | 780 × 560 mm with 45° corners, ground clearance 32 mm. 15 mm deck = superstructure flange at z 353. |
| Drives | 2× ez-Wheel SWD 125 (4:1, brake). Integrated STO SIL3/PL e; SBC, SLS, SDI SIL2/PL d; safe encoder. 24 V. |
| Battery | 2× Discover AES PRO DLP-GC2-48V in parallel: LFP 51.2 V, 3.07 kWh, IEC 62619 / UN 38.3 / CE. Each pack is under 2 kWh, so no EU battery passport is needed. Rev B2: each pack lies on its side with the top cover facing outward and 50 mm free in front of it (Discover manual 805-0027). Over-the-top straps hold it down, and it slides out at the front or rear. |
| Safety | 2× SICK nanoScan3 Pro I/O (PL d) on the front-right and rear-left castor towers; scan plane 184.5 mm, continuous 40 mm slot all round. Safety controller: see `electrical/ELECTRICAL.md` (rev B, lowest-cost certified option). 3 E-stops, key service disconnect, reset, enabling-pendant socket. |
| Power | B48 bus 40–58.4 V: 100 A NH00 fuse, SW80B contactor + precharge. Traction 24 V from 2× DDR-480C-24 in parallel with ORing and a 27 V clamp. S24 always on. All DDR/DRDN converters are mounted vertically with their keep-outs. The centre bay has room for one arm DC-DC only, so the second arm DC-DC and the coffee DC-DC are in the side bays. The Jetson is on the deck at the rear, under cover K06. |
| Dock | Roboteq RoboPad at the rear (z 120, off-centre at y −137, clear of the rear battery keep-out). The dock holds an NPB-1700-48 charger (reprogrammed to ≤ 56.8 V), a DC contactor and a controller; the pads stay dead until the Hall sensor and the CAN handshake both confirm docking. AprilTag + reflector, Nav2 Docking Server. |
| Cooling | 2 IP54 60 mm fans with filters per DIN bay: intake on the side covers above the wheel arch, exhaust high on the rear cover (y ±150). The centre bay is fed by 2 × 40 mm fans in the spine cut-outs, through the gaps beside the batteries. |

## Key numbers (`CALC.md`)
- **Mass:** base 111.2 kg (CAD, incl. 28 kg batteries, which also serve as ballast). Robot 158.4 kg empty, 166.5 kg loaded.
- **Tipping:** worst lateral 4.62 m/s² (the Ranger Mini was 3.65). The 1.5 m/s² limits (accel, decel, lateral) keep a safety factor of at least 2 in every arm pose.
- **Speed:** SLS bands 0.3 / 0.8 / 1.2 / 1.5 m/s. Rotation on the spot up to 105°/s with the arms parked. Swept radius 440 mm.
- **Protective field:** 232 / 484 / 817 / 1144 mm at 0.3 / 0.8 / 1.2 / 1.5 m/s. Rotate-in-place field R 711 mm.
- **Runtime:** OpenArm logistics 17.5 h, barista 7.2 h. With certified Kassow arms, 7.3 / 3.1 h.
- **Charging:** 20 → 90 % takes 1.9 h at 25 A.
- **Deck:** 31 MPa and 0.44 mm under 2 g + braking (limits 160 MPa, 0.55 mm).

## Operating rules that come from the design (go into the manual and the safety configuration)
1. Drive in reverse only at ≤ 0.3 m/s (SDI + SLS), which is used for docking. The cat-0 brake stop is grip-limited, with a safety factor of 1.21 against tipping, so use SS1 for every stop except power loss.
2. Never drive with the arms extended to the side or rear. Rotate on the spot only with the arms parked.
3. Objects travel in the tray or a form-fit cradle, not held by friction (CALC §8).
4. OpenArm variant: the arms move only while the protective field is clear. Hand-over happens through the tray.

## Cost (`INDUSTRIALIZATION.md`, `bom_amr.csv`; mostly ESTIMATE)
| Variant | 1 unit | 10 units | 50 units |
|---|---|---|---|
| AMR alone incl. dock, materials + assembly | ≈ €24.0k | ≈ €20.3k | ≈ €17.8k |
| Giorgio R&D (OpenArm), materials + assembly | ≈ €36.2k | ≈ €31.2k | ≈ €27.7k |
| Giorgio with certified arms, materials + assembly | ≈ €89.6k | ≈ €80.4k | ≈ €73.2k |

The certified safety parts dominate the cost: 2 SICK nanoScan3 Pro I/O scanners (€2,394.95 each excl. VAT from a German
distributor, checked 2026-10-05; €4.0k at DigiKey) plus 2 system plugs
(€265.73 each, P/N to confirm), the Pilz PNOZmulti 2 safety controller (PNOZ m B0 + EF 8DI4DO + ES ETH, €1,375 net +
≈ €90 terminals; it replaces the €2,000 placeholder), and 2 safety wheel drives (€2.3k each). One-off CE and engineering costs (NRE) are on top of these figures:
see `INDUSTRIALIZATION.md`.

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
| `CAD_REV_B2.md` | rev B2 CAD changes and keep-out checks (installation rules of the batteries and converters) |
| `archive/rev_A/` | rev A (with the waist joint), kept for reference |
| `archive/rev_B1/` | rev B1 `amr_cad.py` / `amr_params.py`, before the rev B2 installation-rule rework |

Run everything:
```bash
cd ~/giorgio_sim/amr
../cad/.env/bin/python amr_cad.py && ../cad/.env/bin/python integrate.py && ../cad/.env/bin/python amr_calc.py
python3 electrical/check_amr.py
~/tools/blender-4.5.9-linux-x64/blender -b -P render_amr.py -- --view hero --out renders/amr_hero.png
```

## Before pre-production
1. **Written answers from suppliers:**
   - ez-Wheel: 24 V supply from a DC-DC, regen energy, brake torque, PFHd values.
   - Discover: lying mounting, paralleling, short-circuit current.
   - SICK: field sets, whether a system plug is needed.
   - Castor maker: spring k ≈ 30–48 N/mm, ≥ 90 kg.
   - Siemens: K1/K2 DC breaking.
2. **Vendor CAD:** replace the ESTIMATE envelopes with vendor STEP files (SWD 125, castors, DIN modules) and re-run the interference check.
3. **Drawings:** 2D drawings with tolerances and holes for every bolted joint (the CAD carries the interfaces as notes). The M6 threads into the deck need ≥ 9 mm engagement.
4. **Prototype tests:** build one prototype and run TP-01…TP-22 (`ce/TEST_PLAN.md`).
5. **Arms decision:** brakes on OpenArm, or certified DC arms.
