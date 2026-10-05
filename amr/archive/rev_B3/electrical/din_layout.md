# DIN layout: Giorgio own AMR (rev B3, 2026-10-05) - ONE position table with the CAD

Rev B3 replaces the two diverging rev B2 tables (this file: rails at z 248/118 from the rev B CAD; `../CAD_REV_B2.md` §3: rails at
z 120/245/275) with **one table generated from `../out/parts.json`** (the CAD is the geometry master; this file and `netlist_amr.yaml`
follow it). `check_amr.py` → `CHECKS_AMR.md` §CAD verifies that every netlist device with a `cad:` id exists in the CAD and that its
`loc` code equals the CAD position (0 mismatches), and reads the Mean Well keep-out result of `../amr_cad.py` (0 violations).

Frame: base frame, mm, x forward, y left, z up. Spines A03 at |y| 131…137, rail front faces at |y| 144.5 (outer) / 123.5 (inner).
Deck underside z 338. Pan top z 37. SWD housing x −95…95, |y| 141…207, z 45…180 (ESTIMATE envelope). Castor swivel keep-outs
r ≤ 84.4 about (±275, ±180), z 32…116 (`../CASTOR_SUSPENSION.md` §4).

## 0. Rev B3 changes (relative to rev B2 of both files)

1. **Mean Well installation rule as CAD keep-outs, at the true heights.** DRDN40 is **55 × 125.2 × 100** (DRDN40-SPEC, the rev B2
   CAD had 90 mm) and DDR-240 is **40 × 125.2 × 113.5** (DDR-240-SPEC). Each DDR/DRDN has a keep-out solid (module + 5 mm left/right,
   **40 mm above, 20 mm below**, vertical, input terminals down); 0 violations. The rev B2 conflicts of §6 (upper-rail DDRs with
   32 mm above, DRDN40 under U1 with < 20 mm below) are gone: **no converter is on an upper rail any more**, and no module sits in
   any converter keep-out.
2. Converter slots (only places with ≥ 185.2 mm of free height): LOW rails z 120 at |x| 100…190.6 (between the SWD housing and the
   castor swivel keep-out), the FL and RR corners above the tower roofs (z ≥ 134, no scanner there), the centre-bay LOW rails, and the
   left MID rail above the SWD for the 90 mm DDR-60 only. Allocation: U1/U2 left LOW, UAR + U5 + U4 right LOW, U7 FL corner,
   **U8 RR corner** (out of the RR swivel space), **U3 centre bay** (its 125.2 mm keep-out no longer fits above the SWD), UAL + UOL/UOR
   centre bay, **U6 left MID**.
3. **E5B (RAL/RAR) and E16 (R1a/R1b) DSR 50/5 clamps** left the spine/battery gaps (now the castor spring columns): they sit on the
   deck underside above the packs (z 303…338, between the battery straps, outside the slide path z ≤ 300).
4. **PNOZmulti 2 station** (Pilz: ES ETH left of the B0, expansions right, contiguous): SC1 | SC0 B0 | **SR1** | **SR2** EF 4DI4DOR |
   (SX2 slot 226.2…248.7 kept free, C48 only). The rev B1 EF 8DI4DO (SX1, CAD E22) is deleted in the CAD too.
5. **KI4** (Phoenix PLC-RSC 6.2 mm, `E2J`) and **K0V** (Carlo Gavazzi DUB01CD48500V, 22.5 × 80 × 99.5 mm, `E2K`) on the right HIGH rail;
   the rev B2 CAD relay E5C in the centre bay is deleted (KI4 is the same function).
6. **E2F WF1–3** on the left HIGH rail rear end next to F2/E18 (rail extended to x −298 on bracket A08, above the RL scanner).
7. **G01 LYNK II at its real size 120 × 135 × 44 mm** (sell sheet 885-0035, VERIFICATION D15) on bracket E38b hung from the deck,
   against the right side cover above the SWD (x −92.5…42.5, z 214…334). The HIGH-rail modules in front of it are ≤ 85.5 mm deep
   (terminals, fuses, KI4). LYNK cable W20 to the packs ≈ 0.8 m (≤ 1.4 m). The right E-stop moved to x +60 (its contact block is
   modelled), the left one too (symmetry).
8. K1/K2 Siemens 3RT2026 depth **107 mm** (Siemens data sheet), CAD updated.

## 1. Position table (generated from `../out/parts.json`, rev B3)

x/y/z = module envelope in the base frame. Keep-out = the Mean Well free space (x range / z range; y = the module's y range).

### LL: Left LOW rails z 120 (x 100..195 front / -195..-100 rear)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E14_U2_dcdc_DDR480C24 | U2 | -190.5…-105.0 | 144.5…273.7 | 57.4…182.6 | -195.5…-100.0 / 37.4…222.6 |
| E13_U1_dcdc_DDR480C24 | U1 | 105.0…190.5 | 144.5…273.7 | 57.4…182.6 | 100.0…195.5 / 37.4…222.6 |

### LM: Left MID rail z 245 (x -95..95, above the SWD housing)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E12_K0P_precharge_relay | K0P | -94.0…-76.5 | 144.5…214.5 | 200.0…290.0 | – |
| E11_K0_contactor_SW80B_on_plate | K0, D0 | -74.5…-4.5 | 144.5…239.5 | 190.0…300.0 | – |
| E10_F0_fuse_NH00_100A | F0 | -2.5…37.5 | 144.5…234.5 | 182.5…307.5 | – |
| E58_U6_DDR60L5 | U6 | 42.5…95.0 | 144.5…199.0 | 200.0…290.0 | 37.5…100.0 / 180.0…330.0 |

### LU: Left HIGH rails z 275 (front x 100..195, rear x -298..-97 on spine + A08)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E2F_WF1-3_AUX48_fuses | FW | -296.0…-243.5 | 144.5…214.5 | 234.0…316.0 | – |
| E18_branch_fuses_10x38_x6 | FH, FL | -241.5…-131.5 | 144.5…214.5 | 234.0…316.0 | – |
| E17_K0T_timer_Finder80 | K0T | -129.5…-112.0 | 144.5…214.5 | 230.0…320.0 | – |
| E31_F8LR_SWD_fuses | FH (F8L, F8R) | 101.0…136.0 | 144.5…214.5 | 234.0…316.0 | – |
| E32_T24_terminals | T24 terminals | 138.0…162.0 | 144.5…194.5 | 245.0…305.0 | – |
| E19_0V_block | E19 | 164.0…191.0 | 144.5…194.5 | 245.0…305.0 | – |

### LC: Left corner rail FL z 217 (x 202..298, spine end + A06)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E54_U7_DDR480C24_coffee | U7 | 205.0…290.5 | 144.5…273.7 | 154.4…279.6 | 200.0…295.5 / 134.4…319.6 |

### RL: Right LOW rails z 120 (front x 100..195, rear x -193..-98)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E2G_U5_DDR120C12 | U5 | -190.0…-158.0 | -246.5…-144.5 | 57.4…182.6 | -195.0…-153.0 / 37.4…222.6 |
| E15_U4_dcdc_DDR240C24_S24 | U4 | -153.0…-113.0 | -258.0…-144.5 | 57.4…182.6 | -158.0…-108.0 / 37.4…222.6 |
| E50_dcdc_arm_R_DDR480C24 | UAR | 105.0…190.5 | -273.7…-144.5 | 57.4…182.6 | 100.0…195.5 / 37.4…222.6 |
| E37_KS_signature_relay | KS | -106.0…-99.8 | -214.5…-144.5 | 75.0…165.0 | – |

### RU: Right HIGH rail z 275 (x -202..261)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E25_NET1_switch_FL1008N | NET1 | 47.2…87.2 | -234.5…-144.5 | 220.0…330.0 | – |
| E20_SC1_PNOZ_m_ES_ETH | SC1 | 113.7…136.2 | -264.5…-144.5 | 224.3…325.7 | – |
| E21_SC0_PNOZ_m_B0 | SC0 | 136.2…181.2 | -264.5…-144.5 | 224.3…325.7 | – |
| E2H_SR1_PNOZ_m_EF_4DI4DOR | SR1 | 181.2…203.7 | -264.5…-144.5 | 224.3…325.7 | – |
| E2I_SR2_PNOZ_m_EF_4DI4DOR | SR2 | 203.7…226.2 | -264.5…-144.5 | 224.3…325.7 | – |
| E2C_K1_contactor_3RT2026 | K1 | -200.0…-155.0 | -251.5…-144.5 | 232.5…317.5 | – |
| E2D_K2_contactor_3RT2026 | K2 | -153.0…-108.0 | -251.5…-144.5 | 232.5…317.5 | – |
| E2L_FJ_fuse_Jetson12V | FW (FJ 8 A) | -106.0…-88.5 | -214.5…-144.5 | 234.0…316.0 | – |
| E33_F7_charge_fuse | FH (F7 32 A) | -86.5…-69.0 | -214.5…-144.5 | 234.0…316.0 | – |
| E35_RSIG_X0R | RSIG | -67.0…-45.0 | -194.5…-144.5 | 245.0…305.0 | – |
| E27_XS24_terminals_RB1-7 | XS24, RB | -43.0…37.0 | -194.5…-144.5 | 245.0…305.0 | – |
| E2J_KI4_interposing_relay | KI4 | 39.0…45.2 | -224.5…-144.5 | 230.0…320.0 | – |
| E2K_K0V_LVCO_relay_DUB01CD48500V | K0V | 89.2…111.7 | -244.0…-144.5 | 235.0…315.0 | – |

### RC: Right corner rail RR z 220 (x -265..-203, spine end + A07)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E34_U8_ideal_diode_DRDN40-48 | U8 | -262.0…-207.0 | -244.5…-144.5 | 157.4…282.6 | -267.0…-202.0 / 137.4…322.6 |

### RW: Right bay, bracket E38b against the side cover

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E38b_LYNK_bracket | (bracket) | -95.0…45.0 | -276.0…-230.0 | 210.0…338.0 | – |
| E38_G01_LYNK_II_gateway | G01 | -92.5…42.5 | -276.0…-232.0 | 214.0…334.0 | – |

### CB: Centre bay, rails on the spine inner faces (LOW z 120, HIGH z 274)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E50_dcdc_arm_L_DDR480C24 | UAL | -73.0…12.5 | -5.7…123.5 | 57.4…182.6 | -78.0…17.5 / 37.4…222.6 |
| E52_arm_ORing_R_DRDN40-24 | UOL (UOR) | -73.0…-18.0 | -123.5…-23.5 | 57.4…182.6 | -78.0…-13.0 / 37.4…222.6 |
| E30_U3_ORing_DRDN40-24 | U3 | -13.0…42.0 | -123.5…-23.5 | 57.4…182.6 | -18.0…47.0 / 37.4…222.6 |
| E52_arm_ORing_L_DRDN40-24 | UOL | 17.5…72.5 | 23.5…123.5 | 57.4…182.6 | 12.5…77.5 / 37.4…222.6 |
| E56_FCF_fuse | FC (FCF) | 47.0…64.5 | -123.5…-53.5 | 79.0…161.0 | – |
| E36_CAN1_PCAN-Ethernet_gw | CAN1 | 7.4…52.4 | 33.5…123.5 | 224.0…324.0 | – |
| E57_FAL_FAR_fuses | FC | -76.0…-41.0 | 53.5…123.5 | 233.0…315.0 | – |
| E55_K4_Finder22 | K4 | -76.0…-58.5 | -123.5…-53.5 | 229.0…319.0 | – |
| E59_JR1_relays | JR1 | -39.0…-26.6 | 43.5…123.5 | 229.0…319.0 | – |
| E5A_XC_deck_terminals | XC | -24.6…5.4 | 73.5…123.5 | 244.0…304.0 | – |

### CD: Deck underside above the packs (z 303..338, between the straps)

| CAD id | netlist ref | x from…to | y from…to | z from…to | Mean Well keep-out (x / z) |
|---|---|---|---|---|---|
| E16_R1a_traction_clamp_DSR50-5 | R1 | -191.0…-150.0 | 2.0…96.0 | 303.0…338.0 | – |
| E16_R1b_traction_clamp_DSR50-5 | R1 (R1b) | -191.0…-150.0 | -96.0…-2.0 | 303.0…338.0 | – |
| E5B_arm_clamp_L_DSR50-5 | RAL | 150.0…191.0 | 2.0…96.0 | 303.0…338.0 | – |
| E5B_arm_clamp_R_DSR50-5 | RAL (RAR) | 150.0…191.0 | -96.0…-2.0 | 303.0…338.0 | – |

Free / reserved: right HIGH x 226.2…248.7 = **SX2 PNOZ m EF 8DI4DO (C48 only)**; right HIGH x 248.7…261 spare (12 mm); left HIGH front
x 191…195 spare; centre HIGH right x −56…78 is used by the arm cable runs to the grommet.

## 2. Rules that produced this table

| Rule | Source | How it is met |
|---|---|---|
| DDR/DRDN vertical, input terminals down, 5 mm left/right, 40 mm above, 20 mm below | Mean Well DDR-120/240/480 installation manual p.2; DRDN20/40 manual (VERIFICATION M1) | keep-out solids in `amr_cad.py`, 0 violations (3,086 pairs) |
| Module depth ≤ cover inner face (|y| 278) / ≤ 247 mm summed for facing centre-bay modules | CAD | max y 273.7 (DDR-480); facing sums ≤ 229.2 |
| PNOZmulti 2: communication module left of the base unit, ≤ 6 expansions right, contiguous | Pilz catalogue p.20–23 | SC1 113.7 | SC0 136.2 | SR1 181.2 | SR2 203.7 | (SX2) |
| Castor swivel space r 84.4 about (±275, ±180), z 32…116 | `../CASTOR_SUSPENSION.md` §4 | keep-outs KO_C01_swivel_*, 0 violations; U1/U2/UAR/U5 start/end at |x| 190.5/190.0 |
| Battery top-cover 50 mm free + slide-out path | Discover 805-0027 §9.2 | unchanged rev B2 keep-outs, slide paths empty |
| H06a ≤ 2 m (RoboPad) | RoboPad datasheet v1.3 | collector → U8 0.6 m |
| W20 LYNK cable ≤ 1.4 m from both packs | Discover LYNK II | ≈ 0.8 m |

## 3. Heat per bay and cooling verdict (from `CHECKS_AMR.md`, rev B3 contents)

Model: losses at **typical** duty, closed box, outer surface h = 8 W/m²K [ASSUMED], 40 °C ambient, 55 °C limit.

| Bay | Main losses | Total W | Passive at 40 °C | With fans |
|---|---|---|---|---|
| Left (power) | U1+U2 13 W, U7 11 W, K0/K0P/K0T coils 13 W, fuses 3.5 W, contacts 3 W, U6 2.4 W | 45.9 | not sufficient | 44 °C PASS (2 × 60 mm) |
| Right (safety) | PNOZ station 14 W, K1+K2 11.8 W, U4 10.7 W, U5 6.7 W, UAR 6.1 W, K0V 3 W, NET1 3 W, G01 2 W, bleed 1.8 W | 61.4 | not sufficient | 45 °C PASS |
| Right, docked | + U8 9 W, F7 2 W | 72.4 | not sufficient | 46 °C PASS |
| Centre | UAL 6.1 W, 3 × DRDN40 8.1 W, DSR 3.3 W, K4/fuses/JR1 3 W, CAN1 2 W | 22.5 | not sufficient | 44 °C PASS (2 × 40 mm E42, 5.3 W/K ESTIMATE) |

Fans are needed in every bay and **for S24 they are safety-relevant** (DDR-240 maximum ambient 50 °C, V:M7): NTC on each rail and in the
centre bay, read by the Jetson, parks the robot on fan failure / over-temperature. The upper-rail wiring duct must not run directly
above any converter keep-out (it now never does: converters are on LOW/corner/MID rails only).
