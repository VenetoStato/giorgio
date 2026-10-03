# Giorgio — manufacturing notes and assembly sequence

All part numbers refer to `model.py` (names in `out/bom_parts.csv`). Prototype quantity 1–5 sets; the "series" column
says what changes at 50+ units. Fastener list: `out/bom_fasteners.csv` (generated, with torque/preload in VALIDATION.md).

## Process per part

| Part | Material | Prototype process | Series | Notes |
|---|---|---|---|---|
| P01 base adapter plate | EN AW-6082-T6, 10 mm | waterjet / fibre-laser cut, CNC drill + tap (M5/M6/M8), 90° countersinks for the 16 rail screws | same, laser | deburr, black anodise. Flatness 0.3 mm over the column footprint. Lightening windows only where nothing is fixed. |
| W01 column sleeve weldment | 6082-T6 flange 12 mm + EN AW-6060-T66 tube 100×100×5 (EN 755-2) + 2 boss blocks | TIG weld (4043/5356 filler), **then** machine: flange face, 4 inner liner seats, M10 clamp threads, M16×1.5 plunger thread | same, or a cast/extruded sleeve | HAZ reduces 6082 to ~50% Rp0.2: stresses in the weld are < 5 MPa (see README), fine. Clear anodise after machining, mask threads. |
| S01 column profile | item Profil 8 80×80 leicht 0.0.265.80 | buy cut to 370 mm; drill 7× Ø8.5 index holes at 25 mm pitch; tap core M12 × 30 | same | core bore Ø ESTIMATE 10.2 — check on delivery. |
| P13/P14/P15 liners, gib, guide pads | POM-C 4.8 mm | CNC from sheet | same | bonded (3M DP490) — trapped between tube and profile; gib strip floats under the M10 clamp screws. |
| P02 column-to-torso bracket | 6082-T6, 20 mm | 3-axis CNC: 80×80 spigot pocket (H8 fit on the profile), M12 counterbore, 8× Ø6.6, 4× M4 | same | the spigot gives location + shear; the M12 gives clamp. |
| P03 battery tray | EN AW-5754-H22, 2 mm | laser + press brake (8 bends, flanges outward) | same | EPDM pads (P04) on the floor and on the side walls (10 mm gap). |
| P05 battery hold-down bars (2) | 5754-H22, 3 mm | laser + 2 bends | same | M5 + ISO 4032 nut through the tray wall. |
| P06/P07/P08 electronics plates | 5754-H22, 3 mm | laser, PEM nuts M4 (components) | same | pre-wired on the bench, dropped in as modules (4× M5 each). |
| P09 scanner pod brackets (2) | 5754-H22, 3 mm | laser + bends (U-cradle, back plate, top flange) | same | 4× M5 into the nanoScan3 side threads (max 7.5 mm insertion, SICK). Alignment: slotted top flange recommended after first fit (SICK alignment kit 2a 2111769 as alternative). |
| P10 charging-collector bracket | 5754-H22, 4 mm | laser + 1 bend | same | Roboteq RPCOL90-100 on 4× M4 (74×56 pattern; vertical pitch to be confirmed on the real part). |
| P11 skirt standoffs (6) | 6082-T6 Ø14 | lathe, M5 male stud bottom / M5 tapped top | same | lengths differ per position (see BOM). |
| SH01 base skirt | prototype: SLS PA12 3 mm in 4 segments bonded with internal splice strips; series: vacuum-formed ABS/PC 4 mm on a CNC mould | — | thermoform | 750×660×250 mm does not fit any SLS/MJF bed (EOS P396: 340×340×600, HP 5200: 380×284×380). Open bottom, scanner-pod cut-outs, open scan slots (no window in front of a safety scanner). |
| P12 bumper | EPDM D-profile | buy by the metre, bond | same | |
| SH02 fixed column cover, SH03 waist cover, SH04 torso shell, SH05 head shell, SH06 coffee housing | PA12 | SLS/MJF 2.5–3 mm, each split in 2 halves (front/rear or left/right) to fit 380×284×380 bed and to assemble around the arms/column; Kerb Konus 860 M4 heat-set inserts in bosses | RIM PU or injection-moulded ABS for >200 units | vapour smoothing + primer + paint (warm white soft-touch, accent bands). Min wall around inserts 2.5 mm (Kerb Konus). |
| P16 head neck plate | 5754-H22, 3 mm | laser | same | |
| P17 Insta360 mast | 6082-T6 | CNC: Ø14 rod + 56×66×8 foot in one piece, 1/4"-20 stud at top | same | |
| P18 Gemini bracket | 5754-H22, 2.5 mm | laser + 3 bends | same | M4 into the camera back: **max 4 mm insertion, 0.4 N·m** (Orbbec). |
| P19 tray carrier | 5754-H22, 3 mm | laser + bends | same | 4× M6 into T-nuts in the OpenArm post front slot (slot type ASSUMED). |
| P20 tray halves L/R | PA12 MJF | MJF (309×98×72 fits the bed) | injection-moulded POM for series | 3 pockets 60×60, 16 mm 45° lead-in. Located by 2 ISO 7379 Ø8 shoulder screws (S06) each + 1 GN 617 spring plunger: lift-off quick release. |
| P21 coffee shelf | 6082-T6, 6 mm | waterjet + drill/tap M3/M4 | laser | |
| P22 coffee uprights (2) | 5754-H22, 3 mm | laser + 4 bends (C-channel with feet) | same | pass through slots in the skirt top. |
| P23 rail riser | 6082 flat 20×4 | saw + drill | same | MGN12 rail (S08) on top. |
| P24 shuttle cup carrier | PA12 MJF | MJF | same | cup cradle ring Ø72, arm to the MGN12H carriage, lug for the actuator rod end. |
| P25 actuator rear bracket | 5754-H22, 3 mm | laser + 1 bend | same | |
| P26 cup-stack holder | PA12 MJF | MJF, 3 inserts M4 in a 14 mm foot | same | |

Tolerances (general): ISO 2768-mK for machined parts, ISO 2768-m + DIN 6935 bend radii for sheet; spigot pocket P02 80 H8;
liner bore after welding 90.0 +0.2/0; clearance holes ISO 273 medium; tapped holes 6H.

## Assembly sequence (one robot)

1. **Bench sub-assemblies**: electronics plates P06/P07/P08 with DC-DCs, PNOZ (DIN rail), contactors, Jetson, charger, pre-wired and tested; battery in tray P03 with EPDM pads and hold-down bars P05; scanner pods (nanoScan3 + P09); collector + P10; coffee module (shelf P21 + uprights P22 + rail/riser + carriage + cup carrier + actuator + bracket + cup holder; machine last).
2. **Column**: bond POM liners in the sleeve top (W01) and guide pads on the profile bottom (S01); insert the profile from the top; fit gib strip, M10 clamp levers and the GN 617 index plunger (lock at lift 0).
3. **Adapter plate**: bolt W01 foot flange to P01 (8× M8×25, 20 N·m) on the bench. Slide 16 M5 T-nuts into the Tracer rails, lay P01 on the rails, 16× M5×20 countersunk, **0.6 N·m** (T-nut allowable is ASSUMED, see README).
4. Fit battery tray (6× M6), electronics plates (12× M5), scanner pods (4× M6), collector bracket (2× M6), skirt standoffs (6, screwed in by the stud), coffee uprights (4× M6). Wire everything (48 V bus, scanners → PNOZ, CAN).
5. **Skirt** halves/segments over the base, 6× ISO 7380 M5 into the standoffs; bumper strip; fixed column cover SH02 (2 halves, M4 inserts) around the sleeve.
6. **Torso**: P02 onto the profile (M12×30 DIN 7984, 70 N·m), waist cover SH03 halves hung on P02 (4× M4). Lift the OpenArm body_link0 + arms (≈26 kg: two people or a hoist) onto P02, 8× M6×30 from below (8.4 N·m).
7. Post T-nuts: tray carrier P19 (4× M6), Gemini bracket + camera (2× M6, 2× M4 at 0.4 N·m); tray halves drop onto their pins.
8. Head: Insta360 mast foot + neck plate onto the top of body_link0 (4× M4×18 — ASSUMED holes), head shell (4× M4 into inserts), Insta360 on the 1/4"-20 stud.
9. Torso shell halves (around arms and post), coffee shelf on the uprights (4× M4 from below), coffee housing (3× M4 from below), machine + cups.
10. Commissioning: scanner field teach (contour learned at standstill), docking contact height check (140 mm), column index position recorded in software, payload test 2 × 4.1 kg.
