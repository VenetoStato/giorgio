# AMR CAD rev B2: the manufacturers' installation rules, modelled and checked (2026-10-05)

Rev B2 makes the CAD follow the installation rules that `VERIFICATION.md` found in the manufacturers' documents:
- **Discover 805-0027 Rev N §9.2:** the pack may lie down but never upside down; keep ≥ 50 mm free above the top cover; use over-the-top hold-downs.
- **Mean Well DDR-120/240/480 and DRDN20/40 installation manuals:** mount vertically with the input terminals at the bottom; keep 40 mm free above, 20 mm below and 5 mm left and right.

Each rule is modelled as an invisible **keep-out solid** (`category = 'keepout'`, `group = 'keepout'`, 0 kg). Keep-outs are not exported as parts
and not rendered. They are written to `out/keepout/*.stl` and `out/keepouts.json`. Each one is checked against every solid except
its owner. Two keep-outs may overlap, because both are only free air.

Backup of rev B1: `archive/rev_B1/amr_cad.py`, `archive/rev_B1/amr_params.py`.

## Result

| Check | Result |
|---|---|
| Solid interferences (robot, harness excluded as before) | **0** |
| Keep-out violations (14 keep-outs × all non-owner robot solids, 1,554 pairs) | **0** |
| Keep-outs vs superstructure (`integrate.py`, `keepout_hits_superstructure`) | **0** |
| Dock (docked position) vs robot: **new check** | **0**. Rev B1 had 3 hits: the dock guide rails overlapped A01, K02 and K05. |
| Battery slide-out paths (x 80 → 420, \|y\| ≤ 90, z 40…300) | **empty** except the pack itself, its keep-out and the removable end cover K01/K02 (with its K05 edge length) |
| Superstructure collisions (`integrate.py`) | **none** (only the deck contact faces, as before) |
| Scan plane | 184.5 mm, unchanged |
| Parts | 114 → **130** (+14 keep-outs, not counted) |
| Base mass (CAD, without dock) | 110.9 → **111.2 kg** |
| CALC | 44 PASS / 7 WARN / 1 FAIL (same count as before rev B2). Worst lateral tip 4.69 → 4.62 m/s², because the standing packs raise the CoG slightly. Robot mass 158.4 kg empty. |

## 1. Batteries (B01, B02, B03 + 2 keep-outs)
- Each pack lies on its side.
  - Pack height axis (254) along x; top cover facing **outward**.
  - Width 180 along y; length 260 vertical.
  - Front pack: x 80…334. Rear pack: x −334…−80. Both: |y| ≤ 90, z 40…300.
  - The EPDM pad B02 sits under each pack. Its top face may be PTFE-faced for sliding (ESTIMATE).
  - New params: `BATT` Lx/Wy/H = 254/180/260, `BATT_X_IN` 80, `BATT_Z0` 40, `BATT_TOP_KO` 50.
- **Keep-out `KO_B01_F/R_top_cover_50mm`:** x 334…384 (or −384…−334), over the full cover face (180 × 260).
  - It ends 4 mm inside the cover inner face (|x| 388).
  - Nearest part: pan 3 mm below (front); collector E01 2 mm beside it (rear).
- **Hold-downs B03:** 2 straps per pack at |x| 120 and 230, z 300…303, spanning between the spine inner faces (|y| 131) with bent M6 tabs.
- **Service:** remove the end cover with its rubber edge length (K05 is now specified as clipped to the cover skirts) and the 2 straps, then slide the pack out along x.
  - `slide_paths()` in `amr_cad.py` proves the path is free.
  - The posts moved, so they are no longer in the path.
- The pack terminals are on the outward top cover. H01/H02 leave through the keep-out; a connection cable is the only thing the manual expects there.
  - They are routed beside the pack at |y| 96, clear of the posts, then through the x = ±200 spine windows to F0 at x = 0.
  - **H01 and H02 are mirror images:** equal length and gauge (805-0027 §9.7).
  - The harness is not part of the solid check (centre lines, as in rev B).

## 2. Parts moved out of the battery keep-outs
| Part | Rev B1 | Rev B2 |
|---|---|---|
| E01 RoboPad collector | rear, y −45…45 | rear, **y −182…−92** (`PAD_Y` −137), z 120. Stays inside the rear chamfer (|y| ≤ 185). Cover cut-out moved. |
| E41 reset / key selector / M12 socket | rear, z 280 (inside the keep-out) | rear, **z 318** (303…333, above the pack and its keep-out). Cover holes moved. |
| A04 end posts | (±360, ±155) | **(±320, ±115)**: 10 mm from the packs and keep-outs in y; clear of the towers (\|y\| ≥ 138) and of A06. |
| E40 rear exhaust fans | y ±105, z 243…303 | **y ±150, z 235…295**. Cover cut-outs moved. |
| E40_fan_Cin front intake | front cover, inside the front keep-out | **deleted**. The centre bay is fed through the spines (§4). |
| Dock X02 RoboPad base, X03 pad mount | y 0 | **y −137** (aligned with E01) |
| Dock guide rails (X01) | \|y\| 150…230, under the robot | **\|y\| 292…296** straight along the robot body (8 mm play; robot incl. rubber edge \|y\| ≤ 284), plus a lead-in flare to \|y\| 350 on a floor strip. AprilTag X06 stays on the robot centre line, because it locates the body; the collector offset is a fixed transform in the Nav2 dock plugin. |
| Dock X05 / X07 | – | unchanged and checked. **X08 added:** 59 V DC overvoltage relay (VERIFICATION M12), inside X07 next to X05. |
| Harness H06 | from y 0 | from the collector at y −137, between post RR and tower RR, to U8 |

## 3. Converters: vertical, input down, keep-outs 40 above / 20 below / 5 left and right
Every DDR and DRDN now has a `KO_<part>` solid: the module box grown by 5 mm in x, 40 mm up and 20 mm down, minus the module.

**Why the layout had to change:**
- Rev B1 upper-rail converters at z 248 (top z 310.6) had only 27 mm to the deck underside (z 338), against 40 mm required.
- Rev B1 lower-rail DRDN modules sat under upper-rail modules.

**Side-bay rail concept (rev B2):**
- **LOW rails z 120**, |x| 98…218, beside the SWD housing: converters only.
  - DDR-480 occupies z 57.4…182.6, and its keep-out z 37.4…222.6. The pan top is at 37.
  - The request said z ≈ 115. At 115 the 20 mm keep-out below would reach z 32.4 and enter the 5 mm pan, so the rail is at 120.
- **HIGH rails z 275:** non-converters only, z ≥ 220, above every converter keep-out.
- **MID rail z 245**, left bay, |x| ≤ 95, above the SWD housing (top z 180): tall non-converters plus one DRDN40, whose 20 mm keep-out below ends exactly on the SWD envelope.
- **Corner rails** above the two castor towers that carry no scanner: front-left (on the new bracket A06) and rear-right.

| Bay / rail | Module (CAD id) | x | z | Keep-out (owner) |
|---|---|---|---|---|
| Left LOW F | U1 DDR-480C-24 (E13) | 105…190.5 | 57.4…182.6 | KO_E13 |
| Left LOW R | U2 DDR-480C-24 (E14) | −190.5…−105 | 57.4…182.6 | KO_E14 |
| Left MID | K0 SW80B (E11) −93…−23, F0 NH (E10) −20…20, **U3 DRDN40-24 (E30) 25…80** | | U3 200…290 | KO_E30 (below = SWD top z 180) |
| Left HIGH F | E31 F8L/R 98…133, E32 T24 135…159, E19 0 V block 161…188 | | | – |
| Left HIGH R | E17 K0T −256…−238.5, E12 K0P −236.5…−219, E18 branch fuses −217…−107 | | | – |
| Left corner FL (A06) | **U7 coffee DDR-480C-24 (E54)** (moved out of the centre bay) | 205…290.5 | 154.4…279.6 | KO_E54 (below = tower roof z 134; at x 295.5 the cover chamfer leaves y ≤ 276.3 ≥ 273.7) |
| Right LOW R | U8 DRDN40-48 (E34) −213…−158, U4 DDR-240C-24 (E15) −153…−113, KS relay E37 −106…−99.8 | | | KO_E34, KO_E15 |
| Right LOW F | **arm R DDR-480C-24 (E50R)** (moved out of the centre bay) | 105…190.5 | 57.4…182.6 | KO_E50R |
| Right corner RR | **U5 DDR-120C-12 (E2G)** (FJ fuse split off as E2H) | −254…−222 | 157.4…282.6 | KO_E2G |
| Right HIGH (x −217…261) | SC1 ES ETH −215, SC0 B0 −192.5, SX1 EF 8DI4DO −147.5, **SX3 EF 4DI4DOR (E2J) −125, SX4 EF 4DI4DOR (E2K) −102.5**, [SX2 C48 reserve −80…−57.5, kept free], E2F −56.5, NET1 E25 −3, F7 E33 38, RSIG/X0R E35 56.5, XS24 E27 79.5, K1 E2C 150.5, K2 E2D 196.5, **FJ E2H 242.5…260** | | 224…326 | – |

**Moved to the centre bay HIGH rails:** CAN1 gateway E36 and LYNK II gateway E38. This frees the right LOW front rail for E50R.

**Moved into the battery/spine gaps:** the traction DSR 50/5 pair E16 (R1a, R1b).

**Scanners:** the housings (z 134…214.5) are below every HIGH-rail module (z ≥ 220). The rail ends are therefore limited only by the spine (x ±262) and the towers. The right HIGH rail holds all modules plus **2 × PNOZ m EF 4DI4DOR** (VERIFICATION change 1), with the C48 SX2 slot kept free.

## 3b. Centre bay (x −78…78, between the pack inner faces at |x| 80 and the spine inner faces at |y| 131)
**Rule:** the DIN rails sit on the spine inner faces (front faces |y| 123.5). Modules facing each other at the same x and z sum to ≤ 247 mm.

**Capacity proof.** Only **one** DDR-480 fits here:
- Two side by side need 2 × 85.5 + 5 = 176 mm of x, and the bay has 156 (168 if the packs moved to the 388 cover limit).
- Facing each other they need 2 × 129.2 = 258.4 > 247 mm.
- Stacked vertically they need 2 × 125.2 + 20 + 40 + 40 = 310 > 301 mm (pan 37 to deck 338).
- Hence **arm R E50R → right bay LOW front** and **coffee U7 E54 → front-left corner**.
- The lying E50s on tray P10 / shelf P11 are deleted.

| Rail | Module | x | depth → reaches y | Facing module (depth sum ≤ 247) |
|---|---|---|---|---|
| LOW left (z 120) | **E50L DDR-480C-24** (KO) | −73…12.5 | 129.2 → −5.7 | E52R 100 (229.2), U6 54.5 (183.7) |
| | **E52L DRDN40-24** (KO) | 17.5…72.5 | 100 → 23.5 | U6 54.5, FCF 70 (170) |
| LOW right (z 120) | **E52R DRDN40-24** (KO) | −73…−18 | 100 → −23.5 | E50L (229.2) |
| | **E58 U6 DDR-60L-5, 52.5 mm** (KO) | −13…39.5 | 54.5 | E50L / E52L |
| | E56 FCF fuse | 44.5…62 | 70 | E52L (170) |
| HIGH left (z 274) | E57 FAL/FAR −76…−41, E59 JR1 −39…−26.6, E5A XC −24.6…5.4, **E36 CAN1 gateway 7.4…52.4** | | ≤ 90 | ≤ 30–80 opposite |
| HIGH right (z 274, rail x −77…5) | E55 K4 −76…−58.5, **E5C K4 interposing relay PLC-RSC 6.2 mm −56.5…−50.3**, **E38 LYNK II gateway** (panel, x 10…75, z 239…309) | | ≤ 80 | E36 90 + E38 30 = 120 |
| Battery/spine gaps (41 mm, \|y\| 96…131) | **E5B arm-bus DSR 50/5 L and R** (x 165…259, z 100…141), **E16 R1a/R1b traction DSR** (rear-left, x −259…−165, z 100…141 / 150…191) | | 35 | outside the pack slide path \|y\| ≤ 90 |

**Jetson E51:** moved onto the deck at the rear (x −318…−208, y −78…32, z 353…413) under the new **K06 cover**.
- K06: 2 mm 5754, powder coated, louvre slots, 0.22 kg.
- Jetson cables pass a 40 × 30 deck hole under K06 into the space above the rear pack (z 303…338).
- Clearances from `integrate.py`, for K06 / E51:
  - P22 coffee upright 15.0 / 20.0 mm;
  - P29 column foot 63 / 68 mm;
  - SH06 coffee housing 53 / 62 mm;
  - S01 column 103 mm.

## 4. Centre-bay cooling (amr_cad.py `centre_bay()` docstring)
**Losses** (from `electrical/din_layout.md` §6, regrouped for the rev B2 contents):
- E50L ~6.1 W; 2 × DRDN40-24 4.8 W; U6/K4 ~4 W; gateways ~4 W; relays/fuses ~2 W.
- Total **≈ 21 W**, down from 52 W in rev B1: the Jetson (20 W), UAR (6.1 W) and U7 (11 W) have moved out.

**Air path:**
1. The side intake fans E40_*in (moved to the side covers above the wheel arch, x −30…30, z 150…210, clear of the low converters) feed the side bays.
2. 2 × 40 mm fans **E42_gap_fan_L/R** sit in new 38 × 38 spine cut-outs at x = +140, z 186…224, on the inner face. They blow into the front battery/spine gaps (41 mm, open to the centre bay).
3. The air crosses the centre bay over the converters.
4. It leaves through the rear battery/spine gaps to the open gap ends at x −262.
5. The rear exhaust fans E40_*out remove it.

2 × ~8 m³/h effective ≈ 5.3 W/K gives ≈ +4 K at 21 W (ESTIMATE). Keep the NTC in the bay, read by the Jetson. The SWD connector window in the spines was lowered to z 42…97, below the centre LOW rail.

## 5. Electrical rev B2 DIN additions
- 2 × Pilz PNOZ m EF 4DI4DOR (E2J, E2K) on the right HIGH rail.
- K4 interposing relay E5C (centre HIGH right).
- 59 V overvoltage relay X08 at the dock.
- U5 / FJ split (E2G / E2H).
- E-stop text changed to Siemens 3SU1 (EA1); ED250B-L.

## 6. Castors
`amr/CASTOR_SUSPENSION.md` did not exist when rev B2 was finished. **The castors (C01) and towers (A05) are unchanged.**

## Parts added / removed (rev B1 → B2)
- **Removed:** P10_centre_tray, P11_centre_shelf, E40_fan_Cin, E16_R1_maxon_DSR50-5_x2 (now E16_R1a/R1b), E52_arm_ORing_DRDN40-24_x2 (now E52 L/R), E2G_U5_DDR120C12_FJ (now E2G + E2H), E0C_L/R_din_rail, E0L_din_rail_upper.
- **Added:**
  - structure: A06_corner_bracket_FL;
  - rails: E0C_L/R_din_rail_low/high, E0L_din_rail_mid / upper_F / upper_R / corner_FL, E0R_din_rail_corner_RR;
  - DSR clamps: E16_R1a/R1b, E5B_arm_clamp_L/R;
  - converters: E50_dcdc_arm_R (now a side-bay module), E52 L/R, E2G_U5_DDR120C12;
  - DIN additions: E2H_FJ, E2J/E2K PNOZ EF 4DI4DOR, E5C_K4_interposing_relay;
  - fans: E42_gap_fan_L/R;
  - covers and dock: K06_jetson_cover, X08_dock_OV_relay_59V.
- **Keep-outs (14, not parts):** KO_B01_F/R_top_cover_50mm, KO_E13, KO_E14, KO_E15, KO_E30, KO_E34, KO_E2G, KO_E50 L/R, KO_E52 L/R, KO_E54, KO_E58.

## Keep-out checks (all 0 mm³ overlap; nearest non-owner solid, 0.0 = shared face)
| Keep-out | Owner | Volume (mm) | Nearest solid (mm) |
|---|---|---|---|
| B01_F_top_cover_50mm | B01_battery_F | x 334…384, y −90…90, z 40…300 | 3.0 (A01 pan) |
| B01_R_top_cover_50mm | B01_battery_R | x −384…−334, y −90…90, z 40…300 | 2.0 (E01 collector) |
| E50 arm L DDR-480 | E50L | x −78…17.5, y −5.7…123.5, z 37.4…222.6 | 0.0 (own rail face) |
| E52 ORing L DRDN40 | E52L | x 12.5…77.5, y 23.5…123.5, z 55…205 | 0.0 (rail) |
| E52 ORing R DRDN40 | E52R | x −78…−13, y −123.5…−23.5, z 55…205 | 0.0 (U6 side face) |
| E58 U6 DDR-60 | E58 | x −18…44.5, y −123.5…−69, z 55…205 | 0.0 (E52R side face) |
| E13 U1 DDR-480 | E13 | x 100…195.5, y 144.5…273.7, z 37.4…222.6 | 0.0 (rail) |
| E14 U2 DDR-480 | E14 | x −195.5…−100, y 144.5…273.7, z 37.4…222.6 | 0.0 (rail) |
| E30 U3 DRDN40 | E30 | x 20…85, y 144.5…244.5, z 180…330 | 0.0 (SWD housing top, **ESTIMATE envelope**) |
| E54 U7 DDR-480 | E54 | x 200…295.5, y 144.5…273.7, z 134.4…319.6 | 0.0 (rail) |
| E34 U8 DRDN40-48 | E34 | x −218…−153, y −244.5…−144.5, z 55…205 | 0.0 (U4 side face) |
| E15 U4 DDR-240 | E15 | x −158…−108, y −244.5…−144.5, z 37.4…222.6 | 0.0 (rail) |
| E50 arm R DDR-480 | E50R | x 100…195.5, y −273.7…−144.5, z 37.4…222.6 | 0.0 (rail) |
| E2G U5 DDR-120 | E2G | x −259…−217, y −246.5…−144.5, z 137.4…322.6 | 0.0 (right HIGH rail end) |

## Open points for other streams
- **`electrical/din_layout.md` / `ELECTRICAL.md` §9 / `netlist_amr.yaml`:** positions as above (electrical stream). The new and moved cable runs are W28 (U5 is now at the rear-right corner) and the U7 / E50R feeds (now side bay to E53). Also update CALC §5 text "both arm DC-DCs in the centre bay".
- **BOM:** add A06, K06, 2 × 40 mm fans, 2 × EF 4DI4DOR, PLC-RSC relay, X08, plus extra DIN rail segments. Delete P10/P11 and one 60 mm fan.
- **E38 LYNK II gateway:** the CAD envelope is still the rev B ASSUMED 65 × 70 × 30. The sell sheet gives 120 × 135 × 44 (VERIFICATION D15), and that does not fit at z 239…309 on the spine inner face. Re-place it when the electrical stream confirms whether a remote panel mount is acceptable.
- **SWD 125 STEP (VERIFICATION E13):** U3's 20 mm keep-out below ends exactly on the ESTIMATE SWD housing top (z 180). Re-run the keep-out check with the vendor STEP.
- **Tight spots to confirm with vendor STEP files:** U7 at the front-left chamfer (2.6 mm); the right HIGH rail is 467 of 478 mm used.
