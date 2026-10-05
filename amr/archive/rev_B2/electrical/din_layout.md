# DIN layout: Giorgio own AMR (rev B2, 2026-10-05)

Basis: the rev B CAD (`../out/parts.json`, `../amr_cad.py → din_bays()/centre_bay()`, read 2026-10-05 15:03). Spines A03 sit at
|y| = 131…137. The upper rails E0L/E0R are TS35 at **z 248, x −258…+258** (516 mm), the lower rails at **z 118, x ±(98…218)**.
Module depth ≤ 128 mm (cover inner face at |y| = 278). Deck underside at **z 343**.
x positions are module start…end in CAD coordinates. **Bold** = change against the current CAD (the CAD stream owns
`amr_cad.py`/`amr_params.py` and places the modules; this file lists what must go where).

## 0. Rev B2 changes in one list (for the CAD stream)

1. **Right upper rail:** add **2 × Pilz PNOZ m EF 4DI4DOR (772143)**, 22.5 × 101.4 × 120 mm each, directly right of the B0
   (`E2H_SR1_PNOZ_m_EF_4DI4DOR` at x −189.5…−167, `E2I_SR2_PNOZ_m_EF_4DI4DOR` at x −167…−144.5). The rev B1 EF 8DI4DO
   (`E22_SX1`) is **deleted** (its I/O moved to the B0 and the relay modules). The C48 slot `E28_SX2` moves to −144.5…−122.
   Add **KI4** (6.2 mm) and **K0V** (22.5 mm). Full sequence in §3.
2. **E2F (WF1–3 AUX48 fuses, 52.5 mm) moves to the left upper rail** (rear end), which needs the left power modules shifted
   forward by 14.5 mm and U2/K0T re-spaced for the 5 mm Mean Well side clearance (§1).
3. **Every DDR-xxx and DRDN40 vertical**, input terminals at the bottom, **5 mm left/right, 40 mm above, 20 mm below free**
   (Mean Well DDR installation manual, VERIFICATION M1). On a horizontal TS35 rail on a vertical spine face this is the normal
   orientation; lying on a tray (rev B1 E50 on P10) is not allowed. See §6 for the clearance conflicts the CAD must resolve.
4. `E58_U6_DDR60L5` width **40 → 52.5 mm** (DDR-60-SPEC, V:M9). `E38_G01_LYNK_II_gateway` envelope **65 × 70 × 30 →
   120 × 135 × 44 mm** (LYNK II sell sheet, V:D15): it no longer fits at x 152…217 on the right spine face (§4).
5. Batteries lie on their side with **≥ 50 mm free in front of the top cover** (Discover 805-0027 §9.2, V:D1); H01 = H02 in
   length (V:D2). Being done by the CAD stream (plan 254 × 180, height 260, top cover facing ±x).
6. RoboPad collector `E01` = **RPCOL90-100** at the rear right (y ≈ −135, z ≈ 120, CAD stream): H06a to U8 ≤ 2 m.

## 1. Left spine, upper rail: POWER (x from rear to front) - rev B2

| # | CAD id | Module | Width mm | x from…to | Notes |
|---|---|---|---|---|---|
| – | end stop | | ~7 | −258…−251 | |
| 1 | **E2F (moved here)** | WF1 6 A, WF2 12 A, WF3 2 A 10×38 gPV holders (AUX48, fed from F2 by an in-bay jumper) | 52.5 | **−251…−198.5** | from the right rail; WF1 → U5 via WW2 (1.1 m, under the deck) |
| 2 | E10 | F0 Siemens 3NA3830 **NH000** 100 A gG link in an NH00 base | 40 | **−196.5…−156.5** | +20 mm |
| 3 | E11 | K0 Albright SW80B…A (24 V continuous coil, blowouts, aux) on a plate; **D0 diode on the coil spades** | 70 | **−154.5…−84.5** | M8 studs up when mounted vertically |
| 4 | E12 | K0P Finder 22.32 (Arcol HS50 47 Ω on the spine below the rail) | 17.5 | **−82.5…−65** | |
| 5 | E18 | F1 6 A, F2 16 A ‖ F3 20 A, F4 20 A, F5L 16 A, F5R 16 A | 110 | **−63…+47** | |
| 6 | E13 | U1 DDR-480C-24 (vertical) | 85.5 | **+52…+137.5** | 5 mm gap each side |
| 7 | E14 | U2 DDR-480C-24 (vertical) | 85.5 | **+142.5…+228** | was 133.5 (2 mm gap to U1 < 5 mm) |
| 8 | E17 | K0T Finder 80.01 on-delay timer 0.6 s | 17.5 | **+233…+250.5** | |
| – | end stop | | ~7.5 | +250.5…+258 | |

## 2. Left spine, lower rails (unchanged in position)

| Segment | CAD id | Module | Width mm | x |
|---|---|---|---|---|
| front 98…218 | E30 | U3 DRDN40-24 (ORing T24), **vertical; CAD height 90 → 125.2 mm** (DRDN40-SPEC) | 55 | 100…155 |
| | E31 | F8L, F8R 10×38 gG 20 A (SWD feeds) | 35 | **160…195** (5 mm from U3) |
| | E32 | T24 +/0 V PTPOWER terminals | 24 | **197…221** → check against the 218 rail end, else 20 mm terminals |
| rear −218…−98 | E16 | R1a + R1b maxon DSR 50/5 (27 V) on a plate (no DIN statement, V:MX1) | 70 | −215…−145 |
| | E19 | 0 V block (single 0 V–chassis bond W15) | 27 | −130…−103 |

## 3. Right spine, upper rail: SAFETY (x from rear to front) - rev B2

PNOZmulti 2 rule (Pilz catalogue p.20–23, SOURCED): the communication module (ES ETH) sits **left** of the B0; up to 6
expansion modules sit **right** of it, contiguous (jumper on the back). Rev B2 uses 2 (OA) / 3 (C48).

| # | CAD id | Module | Width mm | x from…to | Notes |
|---|---|---|---|---|---|
| 1 | E20 | SC1 Pilz PNOZ m ES ETH (Modbus TCP, non-safe) | 22.5 | −257…−234.5 | unchanged |
| 2 | E21 | SC0 Pilz PNOZ m B0 | 45 | −234.5…−189.5 | unchanged |
| 3 | **E2H (new)** | **SR1 Pilz PNOZ m EF 4DI4DOR** (STO_1/2, INSafe_1/2 relays) | 22.5 | **−189.5…−167** | replaces E22 SX1 (delete E22) |
| 4 | **E2I (new)** | **SR2 Pilz PNOZ m EF 4DI4DOR** (scanner CI1–CI3 relays) | 22.5 | **−167…−144.5** | |
| 5 | **E28** | SX2 Pilz PNOZ m EF 8DI4DO (**C48 only**; OA: keep empty) | 22.5 | **−144.5…−122** | was −167 |
| 6 | E25 | NET1 Phoenix FL SWITCH 1008N | 40 | **−120…−80** | was −89.5 |
| 7 | E15 | U4 DDR-240C-24 (S24), vertical | 40 | **−75…−35** | 5 mm gaps |
| 8 | E27 | XS24: S24 fuse terminals + PNOZ field terminals, **incl. RB1–RB7 bleed resistors 2.2 kΩ 1 W in double-level component terminals** | **80** | **−30…+50** | +10 mm for RB1–7 |
| 9 | **E2J (new)** | **KI4** Phoenix PLC-RSC-24DC/21 interposing relay (K4 coil) | 6.2 | **+52…+58.2** | |
| 10 | **E2K (new)** | **K0V** DC voltage-monitoring relay, under-voltage 48.0 V (K0 chain) | 22.5 | **+60.2…+82.7** | senses U4 input (B48_RAW via F1) |
| 11 | E2C | K1 Siemens 3RT2026-1BB40 + diode/Zener suppressor | 45 | **+84.7…+129.7** | coil wire W30 |
| 12 | E2D | K2 Siemens 3RT2026-1BB40 + diode/Zener suppressor | 45 | **+131.7…+176.7** | coil wire W31 (separate cable) |
| 13 | E2G | U5 DDR-120C-12 (32, vertical) + FJ 8 A gG holder (17.5) | 32 + 5 + 17.5 | **+181.7…+236.2** | 5 mm gaps around U5 |
| – | end stop | | ~21.8 spare | +236.2…+258 | |
| | | **Total incl. gaps (C48)** | **≈ 493** | of 516 | |

The PNOZ modules are 101.4 mm high, 120 mm deep (fit the 128 mm depth), 0–60 °C.

## 4. Right spine, lower rails

| Segment | CAD id | Module | Width mm | x | Notes |
|---|---|---|---|---|---|
| rear −218…−98 | E33 | F7 10×38 gPV 32 A | 17.5 | −215…−197.5 | |
| | E34 | U8 DRDN40-48 ideal diode (single input used), vertical, **height 125.2** | 55 | **−192.5…−137.5** | 5 mm gaps |
| | E35 | RSIG 10 kΩ + X0R 0 V block | 22 | **−132.5…−110.5** | |
| | E37 | KS Finder 38.51 interface relay (dock signature) | 6.2 | **−108.5…−102.3** | |
| front 98…218 | E36 | CAN1 PEAK PCAN-Ethernet Gateway DR | 45 | 100…145 | now only CAN-T + CAN-E (BMS) |
| | **E38** | G01 Discover LYNK II gateway, **120 × 135 × 44 mm**, screw-mounted (not DIN) | 120 | **does not fit at 150…215** | CAD: candidate spots = the spine outer face of the right bay above the battery strap, or the inside of the right side cover (K04) next to the fan; must stay ≤ 1.4 m (W20 LYNK cable) from both packs |

## 5. Centre bay (spine INNER faces) - requirement list, positions by the CAD stream

The CAD stream is moving the centre-bay DC-DCs to vertical rails. Requirements from the electrical side:

| CAD id | Module | Width mm | Height mm | Depth mm | Mean Well clearance | Notes |
|---|---|---|---|---|---|---|
| E50 L/R | UAL / UAR DDR-480C-24 (OA) | 85.5 | 125.2 | 129.2 | 5 / 40 above / 20 below | **vertical, input terminals down** (no lying on P10) |
| E52 | 2 × DRDN40-24 + 2 × DSR 50/5 | 2 × 55 + 2 × 41 | 125.2 / 94 | 100 | DRDN: 5 / 40 / 20 | |
| E54 | U7 DDR-480C-24 coffee | 85.5 | 125.2 | 129.2 | 5 / 40 / 20 | |
| E55 | K4 Finder 22.32 | 17.5 | 90 | 70 | – | coil driven by KI4 (right bay) through H10a |
| E56 | FCF 16 A holder | 17.5 | 82 | 70 | – | |
| E57 | FAL/FAR 25 A holders (OA) / K3 (C48) | 35 | 82 | 70 | – | |
| E58 | U6 DDR-60L-5 | **52.5** | 90 | 54.5 | 5 / 40 / 20 | was 40 (ASSUMED) |
| E59 | JR1 2 × PLC-RSC | 12.4 | 90 | 80 | – | |
| E5A | XC deck terminals | 30 | 60 | 50 | – | ES3, PSEN SP1 + SP2 (separate), HL1, coffee, head 5 V |

Vertical budget for a DDR on a centre rail: module top + 40 mm ≤ deck underside z 343 → **rail centre ≤ z 240** for the
125.2 mm DDR-480 (≤ z 258 for the 90 mm DDR-60). The rev B1 centre rails at z 274–276 leave only ~6 mm above U7: **not allowed**.

## 6. Clearance conflicts on the side rails (CAD stream to resolve)

| Item | Requirement | Current CAD | Status | Options |
|---|---|---|---|---|
| DDR on the upper rails (U1, U2, U4, U5): free above | 40 mm | top z ≈ 310.6 vs deck underside 343 → 32.4 mm | **short by ~8 mm** | (a) lower both upper rails to z ≤ 240 where the lower rails allow; (b) local rail step under the DDRs; (c) no wiring duct directly above the DDRs and a written airflow argument + heat-run (fans force the air: TP heat-run) |
| U1/U2 above the left lower front modules: free below | 20 mm | U1 bottom z 185.4 vs U3 DRDN40 top 180.6 (at the true 125.2 mm height) | **short** | move U3/F8/T24 terminals to the lower rear segment or lower the lower rail; or swap U1/U2 with E18 (fuses below are fine) |
| U4 / U5 above the right lower segments | 20 mm | right lower front: CAN1 (100 mm high) under U5? (x 100…145 vs U5 +181.7…+213.7: no overlap) | OK by x | keep G01 out of x +176…+241 below U5 |
| Upper-rail wiring duct 25 × 25 | not directly above DDR modules | duct runs the full rail | change | interrupt the duct over U1/U2/U4/U5 |

## 7. Heat dissipation per bay and cooling verdict (from `CHECKS_AMR.md`)

Model: losses at **typical** duty, closed box, outer surface h = 8 W/m²K [ASSUMED], 40 °C ambient, 55 °C limit.

| Bay | Main losses | Total W | Passive at 40 °C | With fans (+10 W/K) |
|---|---|---|---|---|
| Left (power) | U1+U2 13 W, K0+K0P+K0T coils 16 W, fuses/contacts 6 W, U3 3.3 W, shunt avg 2.8 W | 41.1 | not sufficient | PASS |
| Right (safety) | PNOZ station 14 W, bleed resistors 1.8 W, K1+K2 coils 11.8 W, U4 10.7 W (scanners at 15.9 W), U5 6.7 W, switch 3 W | 50.8 | not sufficient | PASS |
| Right, docked | + U8, F7, gateways | 63.8 | not sufficient | PASS |
| Centre | Jetson 20 W, UAL+UAR 12.2 W, U7 11 W, ORing 4.8 W, U6/K4 4 W | 52.0 | not sufficient | PASS |

Verdict: fans are needed in every bay, and **for S24 they are safety-relevant**: the DDR-240 is rated only to 50 °C ambient
(V:M7) against 45 °C bay air with fans. An NTC on each rail and in the centre bay, read by the Jetson, parks the robot on fan
failure / over-temperature (functional measure).
