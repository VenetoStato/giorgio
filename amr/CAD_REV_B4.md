# AMR CAD rev B4: documented SWD size, drive tunnels, centre bay rearranged, deck doubler (2026-10-05)

Rev B4 implements the CAD part of the `CERTAINTY.md` fixes (findings F1–F5, GAPs G-04/G-19/G-24, BOM ↔ CAD mismatches M1–M13).
Backup of rev B3: `archive/rev_B3/` (all .py/.md/.csv, electrical/, ce/, datasheet/, parts/keep-out/interference/integration json).

## Result

| Check | rev B3 | **rev B4** |
|---|---|---|
| Solid interferences (robot, harness excluded) | 0 | **0** |
| Keep-out solids | 22 | **24** (+2 SWD connector keep-outs) |
| Keep-out violations | 0 of 3,086 pairs | **0 of 3,608 pairs** |
| Castor carriage travel −2.5 / +17 mm | 0 overlaps | **0 overlaps** |
| Dock (docked) vs robot | 0 | **0** |
| Battery slide-out paths | empty | **empty** |
| Superstructure collisions / keep-outs hit (`integrate.py`) | none / 0 | **none / 0** |
| Parts (exported) | 160 | **170** (50 custom, 110 purchased, 10 harness centre lines) |
| Base mass (CAD, without dock and harness) | 113.3 kg | **117.1 kg** (SWD +2.0 kg, tunnels, cheeks, doubler 2.1 kg) |

## 1. SWD 125 at its documented size (F4)

Source: SWD user manual v2.0.2 p.27–28 (`docs/fonti/ezwheel_SWD_user_manual_v2.0.2_EN.pdf`): 1-stage gearbox with external brake,
"Dim L 196 mm", "Weight 7 kg"; wheel width 49.7 mm (fig. 11); connectors on the inboard end face (p.20, fig. 5).

- The SWD is a **coaxial hub drive**: wheel D125 × 49.7 at |y| 207.2…256.9 and a coaxial body to **|y| 60.85** (L 196 from the wheel
  outer face). Rev B3 modelled an ESTIMATE box 190 × 66 × 135 above the axle, which hid that the body reaches through the spine into the
  centre bay. Body cross-section modelled as D 118 (end-view height on p.27; below the D 125 tyre, so the tyre meets any step first).
  Ground clearance under the body: 3.5 mm (SICK Z_F still 150 mm: B_F ≤ 50 mm).
- Mass 7.0 kg (`SWD_MASS`, SOURCED) in CAD and CALC.
- Mounting: two 8 mm 6082 cheek plates **D02_swd_cheek_{L,R}{F,A}** per drive on the gearbox fixing points (M6, 50 × 100, p.28),
  bolted to the pan and to the spine (positions ESTIMATE until the vendor STEP).
- **KO_D01_connectors_{L,R}**: 40 mm axial keep-out in front of the upper half of the end face (angled M12 plugs + bend).
- Pan: slot |x| ≤ 62, |y| 22…200 (body + tunnel inlet); the rev B3 pan drain holes at (0, ±60) are gone (the slots drain).
- Spines: drive notch |x| ≤ 73, z 37…130 (replaces the rev B3 connector window); spine section above it 6 × 208 mm, CALC §9: 5.1 MPa (limit 160).

## 2. Drive tunnels: the SWD out of the bay air (F3)

The SWD is rated "Temperatures 0 to +40 °C" (datasheet 07/2024, manual §3.3); the rev B3 side bays were computed at 44–46 °C.

- **E43_swd_tunnel_{L,R}** (2 mm 5754): roof z 127…129 over |x| ≤ 72, side walls on the pan, inboard end cap at |y| 18…20, outboard
  baffle at |y| 205…207 sealing around the body (D 121 hole + lip). Inlet = the pan slot under the inboard end (|y| 22…100, room air
  from under the robot; the slot outboard of |y| 100 carries an EPDM brush strip). Outlet = **E44_tunnel_fan_{L,R}** (San Ace
  9WPA0624S4001, 60 mm, on the roof at |y| 140…200) into the side bay, ahead of the bay exhaust fan.
- Side cover wheel arch now ends at z 131 (wheel top 125, tunnel roof 129).
- Air at the SWD = room air + tunnel rise: 35.9 °C (logistics duty) / 37.9 °C (sustained 1.1 m/s on 6 %) at the **rated room
  ambient 0…+35 °C** (`electrical/CHECKS_AMR.md` Thermal). Both measures are used: separate air path and a lower rated ambient.
- TP-11 heat-run acceptance (`ce/TEST_PLAN.md`): SWD housing air ≤ 40 °C, tunnel outlet ≤ 40 °C, U4 bay ≤ 50 °C at 35 °C room.

## 3. Centre bay and right bay rearranged

The drive bodies + tunnels fill the centre bay below z 129, so:

| Zone | rev B3 | rev B4 |
|---|---|---|
| Centre bay | LOW rails z 120 (converters) + HIGH rails z 274 (small modules) | **one rail per spine face at z 213**: E50L, E52L (left), E52R, U3, FCF (right); keep-outs 130.4…315.6 (above the tunnels, below the doubler) |
| Right MID rails z 175 (new) | – | E57 FAL/FAR (x 35…70), E5A XC, E59 JR1 (x −93…−47.6); E44R fan in between |
| Right NET rail z 164 (new) | – | **E25 NET1 at its documented size 22.5 × 140.4 × 92.4** (too tall for the HIGH rail) |
| Right HIGH rail z 275 | −202…261, NET1 40 mm (ESTIMATE) | −202…**298** (bracket **A10_rail_bracket_FR**): K4 moved here, K0V right of the E-stop contact block, **SR3** (SLS[2]) after SR2, SX2 slot kept free (C48), **CAN1 at 22.5 × 99 × 114.5** (PEAK manual p.65) at the end |
| DSR clamps E16 | x −191…−150 | x −205…−164 (clear of the doubler) |

## 4. Deck doubler (G-19) and other parts

- **A09_deck_doubler**: 15 mm 6082-T6, x −160…34, |y| ≤ 131, under the deck at the column foot; the 8 foot M6 go through deck +
  doubler. CALC §9 now uses the lower-bound strip b = 62 mm (bolt pitch) and gives 0.36 mm (limit 0.55 mm), 25 MPa.
- **X04_charger_NPB750_48** at 230 × 158 × 67 mm (Mean Well NPB-750-SPEC; rev B3 modelled an NPB-1700-class box, M1).
- **X09_dock_OV_relay_DUB01** (rev B3 X08, ID clash with the BOM dock harness, M2).
- **X05_dock_controller_relay**: Finder OPTA 8A.04.9.024.8320 + Albright SW80B + 1N5408 (G-24).
- C06 droop stop: Ganter GN 351-20-15-M6 (20 × 15; the 20 × 10 size does not exist): the angle is 5 mm lower, same stop face.

## 5. Checks (all re-run)

`amr_cad.py`: 0 interferences, 0 keep-out violations (3,608 pairs), 0 castor-travel overlaps, docked dock 0, slide paths empty.
`integrate.py`: no collisions, 0 keep-outs hit. `amr_calc.py`: see `CALC.md`. `electrical/check_amr.py`: see `CHECKS_AMR.md`
(§CAD: every netlist CAD id exists and its loc matches, incl. the new RM code).

## Residuals

- Vendor STEP for the SWD 125 (cross-section, cheek/fixing-point positions, connector positions), the DIN modules and the Blickle castor.
- TP-11 heat-run (tunnel and bay temperatures, fan effective flow = 50 % of the San Ace free-air flow ASSUMED).
- The 3.5 mm clearance under the coaxial SWD body is inherent to the hub drive; the floor rule (sharp steps ≤ 10 mm) is unchanged
  because the tyre (r 62.5) always reaches a step before the body (r 59).
