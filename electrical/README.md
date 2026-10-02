# electrical/: Giorgio power and safety design

| File | What |
|---|---|
| `ARCHITECTURE.md` | The design: single-line diagram, voltage domains, loads with sources, budget and autonomy, battery protection, precharge, regen, safety (PL, stop categories), charging and dock, grounding and EMC, coffee decision, arm certification, open issues |
| `netlist.yaml` | Machine-readable netlist and BOM: parts, MPNs, ratings, prices, branches, fuses, contactors, profiles, safety chains. `assumed: true` marks values that are not verified. |
| `calc.py` | Validation. Run `python3 calc.py` (needs only PyYAML). It writes `CHECKS.md` and exits with 1 if anything FAILs. |
| `CHECKS.md` | Latest result: **156 PASS, 1 FAIL, 9 INFO** |
| `diagram.py` | Draws `power_safety_architecture.svg/.png` (1920×1080) from the netlist. Run `~/IsaacLab/env_isaaclab/bin/python diagram.py`, which needs matplotlib. |

**The one FAIL is real and deliberate.** Safety function SF3 (base stop) has no rated element: the AgileX Tracer 2.0 documents no external safety input. See ARCHITECTURE §8.6.

**Coffee options.** Options A and B appear as INFO rows. Option A (230 V inverter) would fail the pack-current and main-fuse checks without an interlock. Default C (brewing at the dock) passes.

## Key decisions (short)
1. **Battery:** 15s1p LFP 40 Ah (48 V nominal, 37.5–54.75 V, 1.92 kWh ≤ 2 kWh), bought as an IEC 62619 / UN 38.3 certified pack with CAN BMS.
2. **Arm power:** each arm on a regulated 24 V bus (Mean Well DDR-480C-24: 20 A, 30 A for 5 s), because Damiao J4310/J4340P have OVP at 32 V.
   - Safety contactors K1 + K2 (mirror contacts) with precharge on the 48 V feed.
   - ORing plus a 27.5 V shunt clamp on each arm bus for regen.
3. **Protection:** class T main fuse (20 kA DC) and gPV 10×38 branch fuses, because the pack's prospective short-circuit current is about 5.8 kA. Automotive 58 V fuses (1–2 kA) are not adequate on the 48 V bus.
4. **Safety logic:** PNOZmulti 2 with 2 × nanoScan3 and 2 × E-stop. Arms stop with SS1-t (category 1, 0.5 s), then power is removed. Arms have no brakes, so they park on mechanical rests and there is no hand-to-hand handover.
5. **Dock:** 1.2 kW CC/CV at 54.0 V. Contacts are live only after the pilot plus wireless handshake. Robot contacts are dead when undocked (ideal diode). The Tracer battery is charged by an onboard isolated Orion-Tr 48/24 at 10 A.
6. **Coffee:** DEFAULT is brewing at the docking station with a stock 230 V machine. That means no mains on the robot and no load on the pack.
7. **Arms for a certified collaborative product:** UR3e with the OEM DC control box (19–72 V DC, PL d Cat 3, brakes) on the same 48 V backbone. OpenArm is OK only guard-only, without handover.

## Proposed changes to the simulation (not applied; owner to decide)

### `giorgio_v5.py`, energy model (lines ~35 and ~631–669)
| Item | Now | Proposed | Why |
|---|---|---|---|
| `--bat_wh` default | `2400.0` | **`1920.0`** | 15s1p 40 Ah = 48.0 V × 40 Ah (≤ 2 kWh) |
| `P_ELEC` | `40 + 2*4.5 + 5 + 4 + 5 + 6 + 8 + 15` = 92 W | **`102.5`** W at the pack | S24 (2 × 3.9 scanners + 5 PNOZ + 27 contactor coils + 2 beacon) / 0.91 = 45.9. C12 (35 Jetson + 3 Gemini + 6 Insta360) / 0.895 = 49.2. L5 (3 + 1.5 + 2) / 0.875 = 7.4. The Tracer's own 15 W electronics move to the Tracer battery (below). |
| Arm power | `p_arm` straight from the pack | **`p_arm / 0.92`** (`ETA_ARM_DCDC = 0.92`) | DDR-480C-24 efficiency |
| `K_CU` | `0.04` for all joints | **per joint**: J1, J2 (DM-J8009P) **0.135**; J3, J4 (DM-J4340P) **0.088**; J5–J7 (DM-J4310) **0.677** W/(N·m)² | P_cu = 1.5·R_ph·(τ/K_t)², with K_t = rated torque / rated current (1.0, 3.6, 1.2 N·m/A) and R_ph = 0.090 / 0.76 / 0.65 Ω (docs.openarm.dev motor table). This is an approximation [A]. |
| `P_ARM_IDLE` | `10.0` per arm | keep `10.0` [A] | 8 drivers at about 1.2 W |
| `P_CHARGE`, charge efficiency | `960.0`, × 0.92 | **`P_CHARGE = 1134.0`**, × **0.98** | Dock charger delivers 21 A × 54.0 V at the contacts. 0.98 covers the ideal diode and cable. The charger's mains-side efficiency is not on the robot. |
| Status text | `"IN CARICA 960 W"` | `"IN CARICA 1134 W"` | |
| Traction | `p_drv / ETA_DRIVE` taken from `BAT` (48 V pack) | take it from a new **`BAT_TR = {"E": soc*768, "cap": 768}`** (Tracer 24 V 30 Ah) together with **15 W** Tracer electronics | The Tracer has its own battery |
| Energy balancing | none | when docked and (`soc() > 0.80` or `BAT_TR` SoC < 0.30): `BAT_TR += 284 W`, `BAT -= 326 W` | Orion-Tr 28.4 V × 10 A at η 0.87 |
| Coffee, if default C (at the dock) | `P_HEATER = 1260/0.92` from the robot | **heater not charged to `BAT`**; move the coffee module to the charger post | No mains and no heater on the robot |
| Coffee, if option B (on the back) | `P_HEATER = 1369.6`, `BREW_X = 30/8` | **`P_HEATER = 326.0`** (300 W / 0.92), **`BREW_X = 180/8 = 22.5`** | 24 V 300 W machine at about 3 min per cup, about 16 Wh from the pack |

### `giorgio_model.py`, `pw_*` parts (lines ~172–180)

Sizes are half-extents in m. DDR sizes come from Mean Well datasheets; the others are [A]. Note that several DIN parts are 125 mm tall: check that they fit under the base shell.

| Part | Now (half-extents) | Proposed |
|---|---|---|
| `pw_battery` | (0.20, 0.11, 0.040) | **(0.23, 0.09, 0.075)**: 460 × 180 × 150 mm, about 19 kg [A]. Keep the bottom face at z = 0.205, so the centre is at z = 0.280. 40 Ah prismatic LFP cells are 100 mm or more tall, so 80 mm is not realistic. |
| `pw_bms` | (0.035, 0.07, 0.012) | remove (integrated in the pack) or keep as the pack's CAN/connector box |
| `pw_dcdc0` | (0.035, 0.045, 0.022) | **2 × DDR-480C-24 side by side: (0.086, 0.065, 0.063)** (171 × 129 × 125 mm, 2.75 kg) |
| `pw_dcdc1` | (0.035, 0.045, 0.022) | **DDR-120C-24 + DDR-120C-12 + DDR-60L-5: (0.059, 0.051, 0.063)** (117 × 102 × 125 mm, 1.24 kg) |
| `pw_contactor` | (0.025, 0.05, 0.022) | **2 × Siemens 3RT2036 + K3: (0.050, 0.065, 0.065)** [A] |
| `pw_pnoz` | (0.02, 0.045, 0.022) | **PNOZ m B0 + EF 4DI4DOR: (0.034, 0.050, 0.060)** [A] |
| `pw_charger` | (0.05, 0.05, 0.022) | **Victron Orion-Tr Smart 48/24-16: (0.065, 0.093, 0.040)** [A] |
| `pw_jetson` | (0.05, 0.05, 0.020) | keep (AGX Orin dev kit is about 110 × 110 × 72 mm, so the half-height should be 0.036) [A] |
| new `pw_fuses` | n/a | class T holder + 8 × 10×38 DIN holders + busbar: (0.09, 0.045, 0.04) [A] |
| new `pw_oring_clamp` | n/a | 2 × DRDN40-24 + 2 × HS100 resistors on the base plate: (0.06, 0.04, 0.03) [A] |
| new `pw_msd` | n/a | SB120 service disconnect, reachable from a service flap: (0.03, 0.04, 0.02) [A] |
| new `pw_estop` × 2 | n/a | Ø40 mushroom buttons on the back of the column at about 1.1 m and on the base rear |

The charger post in the sim (`charger_post`, `charger_plate`, `charger_lamella*`) matches the 3-pole design. Add a third, **shorter pilot lamella** (first-break, last-make) and, for coffee option C, the coffee machine on the post.

## BOM summary (from `netlist.yaml`, EUR excl. VAT, indicative)
| Group | EUR |
|---|---|
| Battery pack 15s 40 Ah certified (BMS included) [A] | 1,400 |
| DC-DC converters (2 × DDR-480C-24, DDR-120C-24, DDR-120C-12, DDR-60L-5) | 410 |
| Chargers (dock IC1200-class 650 + Orion-Tr 230) | 880 |
| Safety (2 × nanoScan3 4,600, PNOZ m B0 + EF 800, E-stops + reset 90) | 5,490 |
| Contactors, precharge, ORing, clamps, fuses + holders, MSD, connectors (incl. dock contacts 250), wire, busbar, EMC filter, isolated CAN | 1,580 |
| **Total** | **≈ 9,760** |

Compared with the v7 BOM in `../README.md`:
- The "2× SICK + PNOZ + E-stop" line was €4,800; it becomes **€5,490**.
- There was **no line for the 48 V battery pack and DC-DCs**: about €1,800 to add.
- "Cablaggi e alimentazione" was €600; it becomes **about €1,580** for protection, switching and wiring.
- "Stazione di ricarica" €900 stays about the same: charger €650 + contacts €250, with enclosure and controller to add.
- Net change to the v7 cost: about **+€3.5k**. The coffee machine moves to the station (cost unchanged).

## Caveats
- Web research was capped. Pilz, Siemens, Littelfuse (current site), Victron, Delta-Q and Blue Sea pages could not be fetched, so their key values are flagged `assumed`. Verify them first (ARCHITECTURE §13–14).
- The PFHd values (except the SICK nanoScan3) are placeholders. Run SISTEMA with the manufacturer libraries.
- This design has not been reviewed by a certified electrical or functional-safety engineer.
