# AMR CAD rev B3: sprung D80 castors, one DIN layout with the electrical package, real-size LYNK II (2026-10-05)

Rev B3 implements `CASTOR_SUSPENSION.md` (P1–P8) in `amr_params.py` / `amr_cad.py`. It also reconciles the DIN layout so that
CAD = `electrical/din_layout.md` = `electrical/netlist_amr.yaml`, places the LYNK II gateway at its real size, and gives part
numbers for K0V and the dock over-voltage relay. Backup of rev B2: `archive/rev_B2/` (all .py/.md/.csv files, electrical/, ce/).

## Result

| Check | rev B2 | **rev B3** |
|---|---|---|
| Solid interferences (robot, harness excluded) | 0 | **0** |
| Keep-out solids | 14 | **22** (+8 castor swivel keep-outs) |
| Keep-out violations (keep-out × all non-owner robot solids) | 0 of 1,554 pairs | **0 of 3,086 pairs** |
| Castor carriage travel −2.5 / +17 mm vs fixed solids and keep-outs (**new check**) | – | **0 overlaps** |
| Dock (docked) vs robot | 0 | **0** |
| Battery slide-out paths | empty | **empty** |
| Superstructure collisions / keep-outs hit by the superstructure (`integrate.py`) | none / 0 | **none / 0** |
| Tower roof top / scan plane | 134 / 184.5 mm | **134 / 184.5 mm** (unchanged) |
| Parts (exported) | 130 | **160** (44 custom, 106 purchased, 10 harness centre lines) |
| Base mass (CAD, without dock and harness) | 111.2 kg | **113.3 kg** |
| CALC (`amr_calc.py`) | 44 PASS / 7 WARN / 1 FAIL | **54 PASS / 6 WARN / 1 FAIL** (the FAIL is still "cup held by friction", rule: tray) |
| Electrical (`electrical/check_amr.py`) | 244 PASS / 0 FAIL | **252 PASS / 0 FAIL** (+ new §CAD consistency rows) |

## 1. Castor suspension (CASTOR_SUSPENSION.md §5–§6, at all 4 corners)

| # | Item | Implementation (`amr_cad.py`: `chassis()`, `casters()`) |
|---|---|---|
| P1 | Castor axis | `CASTER_XY` (280, 198) → **(275, 180)**. Castor **Blickle L-ALST 80K** (D80 × 30, H 102, plate 100 × 85, offset 38; 0.7 kg), wheel trailing inward |
| – | Guide, springs | **C07** HIWIN MGN15R L190 on the spine inner face (x 177.5…192.5 at FL, z 40…230); **C08** 2 × MGN15H (z 82…140.8 / 147…205.8, modelled with the rail channel); **C04** 2 × Gutekunst D-313J-02 (z 80…131.2) between the carriage shelf and **C05** spring bracket (slotted ±3 mm); **C06** rubber droop stop (top z 69.5) |
| – | Carriage | **C02** weldment: carriage plate z 102…108 on the castor plate, tongue through the spine notch, mast bolted to the blocks, shelf with spring seats. **C03** PU pad 30 × 30 × 3 (top z 111 → 17 mm to the roof) |
| P2 | Spine notches | both spines, both ends: \|x\| 202…262, z 37…128 (`SPINE_NOTCH`) |
| P3 | Pan corner cut | circle r 86 about each castor axis (`PAN_CUT_R`) |
| P4 | Posts A04 | **(±360, ±106)** at FL, FR, RL (30 × 30, \|y\| 91…121). Deviation from ±110: the RL post hit the rear exhaust fan (fans moved to y ±152, cover holes too). **No post at RR**: at (−360, −106) it hits the RoboPad collector E01 (y −182…−92, a conflict the castor study missed); new bracket **A07** (spine extension x −340…−262, z 134…338) carries the RR deck corner and roof |
| P5 | E5B L/R, E16 R1a/R1b | out of the spine/battery gaps → deck underside above the packs (z 303…338, between the straps) |
| P6 | E34 U8 | out of the RR swivel space → RR corner rail above the roof (§3) |
| P7 | Tower legs removed | **A05_tower_roof_\*** 6 mm, z 128…134, no legs; carried by the spine stub above the notch (y 137 edge), A06 (FL) / A07 (RR), the post tab (FL, FR, RL). Scanner corners keep the roof out to the cover; FL/RR roofs end at \|x\| 340 (clear of E01) |
| P8 | RR tongue vs rail | right LOW rear rail now x −193…−98 (tongue at \|x\| ≥ 220): 27 mm |
| – | Cover edge trim | the swept swivel envelope (r 84.1 at z 62) reaches 1.5 mm past the inner chamfer face: local notch in the cover bottom edge **z 62…70 (8 mm, ~50 mm long)** at the 4 chamfers. 2 mm (CASTOR_SUSPENSION P1) leaves 64 mm³ inside the 5 mm margin; 8 mm is the minimum with 0 |
| – | Keep-outs | `KO_C01_swivel_<corner>`: solid of revolution r(z) = hypot(38 + √(40² − (z − 40)²), 15) for the wheel, r 50 for the fork, swept over −2.5…+17 mm, +5 mm, z 32…116 (r 84.4 max). Owners: castor, carriage, pad, springs, blocks (they move with it). `KO_C01_swivel_vs_carriage_<corner>`: unswept, +3 mm, owner = castor only (checks the carriage parts) |
| – | Travel check | `travel_check()`: castor, carriage, pad, blocks translated to −2.5 and +17 mm vs every fixed solid and keep-out: 0 (end-stop contacts are faces: pad/roof at +17, shelf/buffer at −2.5) |

Tight spots (vendor STEP to confirm): U1, U2, UAR, U5 start/end at \|x\| 190.5/190.0 vs the swivel keep-out at 190.57 (the keep-out already
holds 5 mm); swivel keep-out vs the trimmed cover 0 mm (5 mm real); A04 posts 1 mm from the battery top-cover keep-outs.

## 2. Spine windows, fans, E-stops
- Harness windows x ±200 → **±230** (the MGN15R rails sit at \|x\| 177.5…192.5); x −140 unchanged. H01/H02 re-routed (still mirror images, 0.75 m each in the netlist).
- Rear exhaust fans y ±150 → **±152** (RL post).
- E-stops x 0 → **x 60** on both sides, with the contact-block envelope (30 × 40 × 40) modelled behind the cover: the right side cover above the SWD carries the LYNK II.

## 3. DIN layout = electrical/din_layout.md (one table, generated from `out/parts.json`)
Sourced envelope corrections: **DRDN40 55 × 125.2 × 100** (DRDN40-SPEC; rev B2 CAD had 90 mm height), **DDR-240 depth 113.5**,
**Siemens 3RT2026 depth 107**, **PNOZ m B0 45 × 101.4 × 120** (B0 manual), **DUB01 22.5 × 80 × 99.5**, **LYNK II 120 × 135 × 44**.
With the true DRDN40 height the rev B2 U3 position (left MID rail above the SWD) violates its keep-out (deck and SWD), so converters
are only where ≥ 185.2 mm is free.

| Zone | Modules (CAD id) |
|---|---|
| Left LOW z 120 | U1 E13 (105…190.5), U2 E14 (−190.5…−105) |
| Left MID z 245 | K0P E12, K0 E11 (+D0), F0 E10, **U6 E58 DDR-60** (42.5…95, keep-out 180…330) |
| Left HIGH z 275 | front: F8L/R E31, T24 E32, 0 V E19; rear (rail to −298 on **A08**): **WF1–3 E2F**, E18, K0T E17 |
| Left corner FL z 217 | U7 E54 |
| Right LOW z 120 | UAR E50R (105…190.5); rear: **U5 E2G** (−190…−158), U4 E15, KS E37 |
| Right HIGH z 275 (−202…261) | K1, K2, FJ **E2L**, F7, RSIG, XS24 (+RB1–7), **KI4 E2J**, NET1, **K0V E2K**, SC1, SC0, **SR1 E2H**, **SR2 E2I**, (SX2 C48 slot 226.2…248.7 free) |
| Right corner RR z 220 (A07) | **U8 E34** (−262…−207) |
| Right bay, bracket E38b | **G01 LYNK II E38** (x −92.5…42.5, y −276…−232, z 214…334); modules in front of it ≤ 85.5 mm deep |
| Centre LOW z 120 | UAL E50L, UOL E52L; UOR E52R, **U3 E30**, FCF E56 |
| Centre HIGH z 274 | FAL/FAR E57, JR1 E59, XC E5A, CAN1 E36; K4 E55 |
| Deck underside above the packs | **R1a/R1b E16**, **RAL/RAR E5B** (DSR 50/5) |

Deleted: E22 SX1 (rev B1 EF 8DI4DO, already removed electrically in B2), E5C (rev B2 centre K4 relay = KI4, now E2J), old E2H/E2J/E2K
ids (renamed to the netlist ids). Netlist `loc` codes LL/LM/LU/LC/RL/RU/RC/RW/CB/CD are checked against the CAD by `check_amr.py`
(§CAD: 0 mismatches); Mean Well keep-out result, LYNK and DUB01 envelopes are CHECKS_AMR rows too.

## 4. Purchased-part numbers added
- **K0V and dock XD3: Carlo Gavazzi DUB01CD48500V** (datasheet `docs/fonti/CarloGavazzi_DUB01-PUB01_datasheet_2025-03-03.pdf`):
  ranges 5–50 V (max 350 V) and 20–200 V (max 600 V), level 10–110 % FS, delay 0.1–30 s, hysteresis 0–30 %, UV/OV and normally-energised
  by DIP, DC13 2.5 A @ 24 V, 24–48 V insulated supply, UL/CSA/CCC, EN 60255-6. K0V: 48.0 V, 5 s. XD3: **bench-set 58.5 V** (±1.0 V
  repeatability on the 200 V range stays between CV 56.8 V and the RoboPad 60 V). DigiKey USD 177.65 → €163 (SECONDARY). CAD X08 renamed `X08_dock_OV_relay_DUB01`.

## 5. Calculations (CALC.md)
- Supports at (±275, ±180), trail 38 (SOURCED): worst lateral a_tip 4.62 → 4.57 m/s²; SS1 SF 3.07.
- Springs k 28.34 N/mm (SOURCED), F_inst 76 N: drive share 40.3 % each (flat, min over poses); k ≤ k_max 33.7 N/mm; bump-stop spring force
  279 N per spring ≤ Fndyn 301 N; MGN15H 1.35 kN per block at the bump stop (C0 9.11 kN).
- Thresholds (new model, body pitch about the drive axle): a sharp 10 mm step is climbed (traction 1.86 ≥ 0.88 needed); a sharp 20 mm step
  is **not** (0.65 < 1.73) → rule: **sharp ≤ 10 mm at any speed, 10–20 mm only bevelled ≤ 1:2 at ≤ 0.3 m/s**.
- Cat-0 tip check made over the driving poses (rule 2): SF 1.31 (WARN, rev B2 1.20); with the arms to the rear it would be 1.15 (info).
- **§7b scan plane vs pitch (new):** plane z = 184.5 + x·tan θ; budget 200 − 184.5 − 5 mm mounting tolerance = 10.5 mm at the field edge;
  ×1.2 dynamic amplification. Per-band accel / decel limits (m/s²): **0.3: 1.50 / 1.08; 0.8: 1.22 / 1.00; 1.2: 1.00 / 0.92; 1.5: 0.81 / 0.86**
  (at 1.5 m/s² the plane would reach 211 mm at the 1.5 m/s front field edge). Added to the limits table, the manual and TP-05/05b.
- §9 tower roof under 815 N at the bump stop with the new support (lever 43 mm to the spine stub edge): roof 51 MPa, flange bolts 31 MPa,
  spine stub 0.7 MPa, spring bracket 27 MPa (limits 237 / 448 / 92 / 237 MPa). The pan no longer carries castor loads.

## Residuals (only type tests and price quotes)
- **Price quotes:** Blickle L-ALST 80K, HIWIN MGN15R L190 / MGN15H (prices not published; ESTIMATE values tagged QUOTE in `bom_amr.csv`),
  plus the long-standing ESTIMATE rows (INDUSTRIALIZATION §8).
- **Type tests:** castor swivel radius 79.4 mm (calculated; TP-23 checks 360° clearance at droop/nominal/bump; Blickle STEP with the quote),
  pitch dynamic amplification (TP-05b), static plane 184.5 ± 5 mm at the field edges (TP-05), carriage friction and per-corner preload
  (TP-23), threshold climbing (TP-01), castor rolling resistance and use at 5.4 km/h (TP-22), centre-bay fan conductance (TP-11), plus the
  12 VERIFICATION residuals (SWD reaction time, cat-0 distance, etc.).
- Vendor STEP envelopes (SWD 125, DIN modules) still to be swapped in before release; the tight spots listed in §1 are the first to recheck.
