# Risk assessment - Giorgio (EN ISO 12100:2010) - v0.4 draft, design rev B2, 2026-10-05

Hazard register: `risk_assessment.csv` (44 rows). This file gives limits, method, safety functions and the summary.
Status: DRAFT by design review, no tests yet. All numeric limits marked ASSUMED are proposals to be fixed in the SRS.
Rev B: no waist joint. The rev A waist hazards (rotating superstructure, waist-plate shear gap, twisterband/ring-bearing
entanglement) no longer exist and were deleted; hazard and SF IDs were renumbered.

## 1. Limits of the machinery (ISO 12100 cl. 5.3)
- **Intended use**: autonomous mobile bimanual service robot: transport of light items (2 x 3 kg in hands, 2.1 kg tray),
  barista service (24 V capsule coffee module), pick/place on tables/counters; indoor, flat floors.
- **Users**: trained operator/supervisor (professional), maintainer (trained by manufacturer); exposed persons =
  public incl. children, elderly, persons with reduced mobility or sight (barista variant).
- **Space**: indoor, slope <= 3 % travel (ASSUMED, ISO 3691-4 site requirement), dry floor, 0-40 C, no ATEX, no
  outdoor. Footprint 780 x 560 mm; swept radius when rotating in place ~440 mm with arms parked (base ~432 mm ESTIMATE,
  superstructure 440 mm from CAD `../out/integration.json`).
- **Mass**: ~146 kg empty (base 102.2 kg + superstructure 43.7 kg, rev B CAD), ~155 kg loaded.
- **Time**: 8-10 h/day, battery 3.07 kWh; life 5 years (ASSUMED); maintenance intervals in manual.
- **Variants**: C48 = certified DC cobot arms (CE-fast); OA = OpenArm 2.0 (R&D, external safety only).
- **Foreseeable misuse**: pushing/leaning/climbing, children touching gaps, handing objects directly to hands,
  driving with items in grippers, operation outdoors/wet floors, tampering with fields, use without supervisor.

## 2. Method
- Life-cycle phases: transport, installation/commissioning, operation (auto travel, rotate in place, manipulation,
  barista, docking), manual/service mode, cleaning, maintenance, decommissioning.
- Risk estimate: S (1 first aid, 2 reversible lost-time, 3 irreversible, 4 fatal) x O (1 improbable, 2 remote,
  3 occasional, 4 likely) = R. R <= 3 low (accept); 4-6 medium (accept only if ALARP + information); >= 8 not acceptable.
  S0/O0 = before measures, S1/O1 = residual.
- PLr per EN ISO 13849-1:2023 Annex A graph (S1/S2, F1/F2, P1/P2), cross-checked with the PL table of
  EN ISO 3691-4:2023 cl. 4 and EN ISO 10218-2:2025; the higher value wins.
- Three-step method (ISO 12100 cl. 6): inherent design -> safeguards/complementary measures (SF) -> information.

## 3. Safety functions (rev B2, same IDs as B1, used in the CSV and in all `ce/` files)
**SF1-SF16 are the electrical numbering** of `../electrical/SAFETY_FUNCTIONS.md` rev B2 (same IDs, same order; devices,
PFHd and stop categories live there). SF17 is CE-only: there is no matching function in the electrical package (closest
item: the Jetson heartbeat, which is non-safety), so it keeps its ID and must be added to the electrical stream as a
functional (non-safety-rated) requirement. Safety controller rev B2: **Pilz PNOZmulti 2** (PNOZ m B0 + 2 x EF 4DI4DOR
relay modules + ES ETH; C48 adds one EF 8DI4DO). The SWD STO/INSafe inputs and the scanner control inputs are driven by
positive-guided relay contacts with bleed resistors (`../VERIFICATION.md` E6/S4).

| ID | Safety function | Implementation (summary) | PLr | electrical rev B1 | electrical rev A1 |
|---|---|---|---|---|---|
| SF1 | Emergency stop (3 x Siemens 3SU1 with 2 x 3SU1400-1AA10-1CA0 NC: ES1+ES2 base in series, ES3 torso) | PNOZ m B0 -> SR1 relays -> SWD SS1-t (SLS request at once, STO+SBC at 1.2 s after a complete 1.5 m/s2 ramp); arms: K1/K2 with mirror-contact EDM (OA) or cobot E-stop input (C48); coffee K4 off | d | SF1 | SF1 |
| SF2 | Protective stop on person detection | 2x nanoScan3 Pro I/O OSSD1 -> PNOZ -> SWD STO+SBC, arm stop | d | SF2 | SF2 |
| SF3 | Speed-dependent protective field switching | 3 field sets (FS1 FAST / FS2 SLOW + arm field / FS3 DOCK) selected 1-of-3 through SR2 relay contacts (single contact fault -> invalid code -> OSSD off); SLS request first, field change after 1.1 s (t_SLS 1.0 s) | d | SF3 | SF3 |
| SF4 | Safe limited speed per mode | SWD SMS 1.2 m/s permanent; SLS 0.3 m/s in SLOW/DOCK/MANUAL/arms not parked; STO in SERVICE | d | SF4 | SF4 |
| SF5 | Safe limited reverse speed | **reverse <= 0.3 m/s as a permanent SLSa in each SWD** (forward <= 1.2 m/s); no controller channel; replaces the rev A SDI | d | SF5 | SF5 (SDI) |
| SF6 | Safe standstill of the base while the arms work | K1/K2 close only with traction STO + SBC (spring-applied brakes) | d | SF6 | SF6 |
| SF7 | Arms move only with the arm protective field clear (OA) / protective stop of certified arms (C48) | scanner OSSD2 (arm field in FS2) -> K1/K2 SS1-t (OA) or arm safeguard-stop input via SX2 (C48); SSM distance per EN ISO 13855 | d | SF7 | SF7 |
| SF8 | Carry mode: FAST travel only with arms parked (and de-energised for OA) | 2 Pilz PSEN cs3.1 arm-rest sensors, each on its own PNOZ input pair + K1/K2 EDM (OA) / arm "stopped" output (C48) | d | SF8 | SF8 |
| SF9 | Docking field (reduced rear field shaped to the dock, no muting) | FS3 only with SLS 0.3 m/s active, arms off | c | SF9 | SF11 |
| SF10 | Charging contacts dead unless docked | ideal diode (no back-feed) + station contactor closes only with Hall + signature + Wi-Fi/Ethernet handshake (RoboPad has no wireless CAN); dock OV relay 59 V (RoboPad <= 60 V under fault); robot-side KS relay on a PNOZ auxiliary output (functional) | c | SF10 | SF12 |
| SF11 | No traction while charging is permitted | PNOZ holds SWD STO while KS is energised | c | SF11 | SF13 |
| SF12 | Battery protection | Discover BMS (IEC 62619 CB, main relay) primary; independent layers without PL credit: F0 3NA3830 100 A gG; K0 opened by the G01 LYNK II relay R1 NO "energised = OK" (fail-safe) and by K0V at 48 V; charger CV DIP preset 56.8 V | d (no BMS PL published: no PL credit, VERIFICATION D13) | SF12 | SF14 |
| SF13 | Manual reset, no automatic restart after E-stop | blue reset button SB1 with view of the robot, edge-evaluated in the PNOZ | d | SF13 | SF15 |
| SF14 | Mode selection (AUTO/MANUAL/SERVICE) and manual mode | key selector SK1; MANUAL = SLS 0.3 m/s + 3-position enabling pendant SE1; SERVICE = STO + arm/coffee power off | d | SF14 | SF16 |
| SF15 | Coffee module stop | KI4 interposing relay on a PNOZ auxiliary output -> K4 (Cat B) with aux read-back, off on E-stop and in SERVICE; cover/tilt interlock see H13 | **b (to confirm, H13; was c)** | SF15 | SF17 |
| SF16 | Collaborative hand-over / PFL (C48 only) | cobot PL d functions (PFL, SLS, SLP, SS1/SS2) + SSM (SF7); impossible with OpenArm | d | SF16 | SF18 |
| SF17 | Supervisory/communication watchdog (MR 3.2.4) | heartbeat loss -> protective stop + safe park (non-safety software on the Jetson) | b | **not yet in the electrical package** | - (CE only) |

Removed in rev B: electrical rev A1 SF9 (waist safe limited speed) and SF10 (waist safe limited position); rev A CE SF5
(waist safe motion) and SF6 (superstructure/waist motion permit; its arm part is now SF7).

**Coffee stop PLr (SF15), argument to confirm in this assessment.** The relevant rows are H13 (thermal), H14 (shuttle
pinch) and H43 (fire). H13: hot water stays inside an EN 60335-2-15 appliance in the SH06 enclosure, the outlet is only
above the cup holder, the shuttle force is low -> risk-graph **S1** (slight, normally reversible burn), **F2** (barista
operation all shift), **P1** (heating and ejection are slow and visible, the person can withdraw) -> **PLr b**. H14:
S1 F1 P1 -> a. H43 is covered by the heater thermal fuse and FCF, not by a stop function. So SF15 PLr = b and K4 on a
standard output (Cat B, PL b) is sufficient. **If the assessment rates H13 as S2** (e.g. scald of a child's face or of a
seated person at the outlet height, or hot-water ejection when the cover is opened during brewing) -> PLr c -> fallback
from `../electrical/` rev B2: KI4 on a free B0 safe SC output (O1, €0) plus the U7 remote OFF as a diverse channel.
The rev A cover-open and tilt inputs are not in the rev B2 I/O list: either rely on the appliance's own cover interlock
(EN 60335-2-15 evidence, G5) or wire a cover switch to a spare PNOZ input (B0 + 2 EF 4DI4DOR has 28 inputs, 26 used; SR2 I2 reserved for it).

## 4. Summary of residual risks (from CSV)
| R1 | Rows | Comment |
|---|---|---|
| 6 (medium) | H08, H10 | OpenArm variant only: arm collision without PFL and **arm drop on power loss** -> not acceptable for public until GAPS G1 (brakes/gravity compensation, MR Annex III 1.2.6(d)) is closed; R&D/lab use only |
| 3 (low) + residual note | H03 | rev B2 SS1-t: a fault of the non-safe ramp is stopped by the SWD SLS-STO at 1.0 s (PL d) and the PNOZ STO at 1.2 s; the distance exceeds the field (CALC §7 info). Single fault of a non-safety part; evidence TP-01b; G16 |
| 4 (medium) | H04, H15, H22, H25, H27 | overhangs above scan plane, tip-over (S4), edges/stairs (site barriers required), battery fire (S4, O1), dock mains (S4, O1): accepted with information for use + site requirements |
| <= 3 | all others | acceptable |

Residual risks to state in the manual (Annex III 1.7.2, 1.7.4.2(l)): H04, H05, H12, H15, H16, H21, H22, H25, H37.

## 5. Next steps
1. SRS per SF (reaction time, stop category, PFHd budget) and SISTEMA calculation with the Pilz PNOZmulti 2 library
   (controller frozen 2026-10-05); confirm the SF15 PLr b argument (§3); add SF17 to the electrical package.
2. Fix ASSUMED numbers (speeds, slope) from TEST_PLAN results; re-score.
3. Re-run this assessment for each variant and after every design change (version + date in this header).
