# EHSR checklist - Reg. (EU) 2023/1230 Annex III (verified against EUR-Lex text) - draft rev B (no waist joint), 2026-10-05

A = applicable, N/A = not applicable (reason given). Evidence: RA = RISK_ASSESSMENT.md/csv row, TP = TEST_PLAN.md,
MAN = manual_outline.md, SRS = safety requirements spec (to write), DWG = drawings in `../out/`.
SF/H/TP IDs as in RISK_ASSESSMENT.md section 3: SF1-SF16 = `../electrical/SAFETY_FUNCTIONS.md` rev B2 numbering (same IDs as B1);
SF17 (supervisory watchdog) is CE-only, not yet in the electrical package. Safety controller: Pilz PNOZmulti 2.

## Part 1 - General
| EHSR | A? | How Giorgio meets it | Evidence |
|---|---|---|---|
| 1.1.2 Principles of safety integration | A | 3-step method; misuse listed; safety functions testable by user (1.1.2(e)): daily E-stop/field test routine | RA, MAN ch.7 |
| 1.1.3 Materials | A | Al alloys, steel, PA12; food-contact materials per 2.1 | supplier datasheets |
| 1.1.4 Lighting | A | not needed for operation; service light in base compartment optional | RA |
| 1.1.5 Handling | A | lifting points, mass on plate, transport locks for arms | DWG, MAN ch.3 |
| 1.1.6 Ergonomics incl. (f)(g) autonomy HMI | A | refill points 0.8-1.2 m; light ring + voice to signal intent and state; stops/explains when blocked | RA H38-H39, TP-20 |
| 1.1.7 Operating positions / 1.1.8 Seating | N/A | no operating position on machine, no ride-on | - |
| 1.1.9 Protection against corruption | A | safety config (Pilz PNOZmulti 2 project, nanoScan3, drives incl. permanent SMS/SLSa, cobot) not writable from the network, password + CRC shown in HMI; signed SW updates; list of safety-relevant SW versions readable in HMI; log of interventions and SW changes | TP-21, SW config list |
| 1.2.1 Safety and reliability of control systems | A | all SF in certified hardware PL d (EN ISO 13849-1); (f) safety SW version log kept 5 y; **self-evolving**: no in-field learning; ML outputs only setpoints bounded by SF3/SF4/SF7/SF16 ("defined task and movement space"); decision log of safety logic (PNOZmulti diagnostics via ES ETH) kept 1 y; wireless loss -> stop | SRS, SISTEMA, TP-12, TP-20 |
| 1.2.2 Control devices | A | E-stops red/yellow, key selector, reset button outside hazard zone, HMI tablet; enabling pendant for manual | DWG, TP-12 |
| 1.2.3 Starting | A | start only by deliberate action; automatic mode restarts only if fields clear (permitted for automatic mode); manual reset after E-stop (SF13) | TP-12 |
| 1.2.4.1-.3 Normal/operational/emergency stop | A | normal stop cat 1/2; E-stop cat 1 (base) and cat 0/1 arms; E-stop in all modes | SF1, TP-09, TP-12 |
| 1.2.4.4 Assembly | A | E-stop also stops coffee module (K4, SF15 PLr b to confirm) and dock charging (KS drops, station opens) | SF1, SF15, SF10, SF11 |
| 1.2.5 Modes | A | key selector auto/manual/service; manual: reduced speed + enabling pendant | SF14 |
| 1.2.6 Power / network failure | A | spring-applied brakes on the drive wheels engage; no restart on return; **arms: requirement (d) "no moving part shall fall" NOT met by OpenArm** -> GAPS G1; cobot arms have brakes | TP-03, TP-09 |
| 1.3.1 Stability | A | stability calc + tilt/brake/push tests; config-dependent speed | TP-04, H15-H16 |
| 1.3.2 Break-up | A | structural calc (deck = superstructure flange, column foot, arm mounts) | calc note (to write) |
| 1.3.3 Falling/ejected objects | A | items carried in tray with holders; gripper hold on stop (cobot); OpenArm G1 | H10, H12 |
| 1.3.4 Surfaces, edges | A | chamfers 95 mm, radii >= 2 mm on shells | DWG |
| 1.3.5 Combined machinery | N/A | no multi-function combination requiring separate use | - |
| 1.3.6 Variation in operating conditions | A | public mode vs industrial mode parameters | SF3 |
| 1.3.7 Moving parts + coexistence/interaction | A | PFL/SSM for the arms (SF7, SF16); rotation in place only with arms parked (SF4, SF8); reverse <= 0.3 m/s (SF5); never drive with arms extended to the side/rear (manual) | H06, H08-H11, TP-07-08 |
| 1.3.8 / 1.3.8.1 / 1.3.8.2 Choice of protection | A | transmissions under fixed guards; process moving parts (arms) protected by protective devices (scanners) | DWG, SF2/SF7 |
| 1.3.9 Uncontrolled movements | A | drive brakes (SBC), STO; arms G1 | SF1, SF6, G1 |
| 1.4.1 / 1.4.2.1 Guards | A | fixed guards (shells) need tool to remove | DWG |
| 1.4.2.2 / 1.4.2.3 Interlocking / adjustable guards | A (coffee cover) / N/A | coffee cover interlock: appliance-internal (EN 60335-2-15, G5) or a cover switch on a spare PNOZ input; power cut by K4 (SF15) | TP-11 |
| 1.4.3 Protective devices | A | nanoScan3 Type 3 PL d; field design per ISO 3691-4 test pieces; scan plane ≤ 200 mm everywhere (SICK OI p.40) incl. body pitch: per-band accel/decel limits (CALC §7b, rev B3) | TP-05, TP-05b |
| 1.5.1 Electricity supply | A | 48 V PELV, EN 60204-1; fuses; dock is separate 230 V product (LVD) | TP-14 |
| 1.5.2 Static electricity | A | conductive castor option for ESD sites (info) | MAN |
| 1.5.3 Other energy | N/A | no hydraulics/pneumatics (gas springs if G1: stored energy info) | - |
| 1.5.4 Errors of fitting | A | keyed connectors for battery, dock, arm buses | DWG |
| 1.5.5 Extreme temperatures | A | coffee surfaces, motors; EN ISO 13732-1 | TP-12 |
| 1.5.6 Fire | A | LFP, fusing, materials | H24-H25, H43 |
| 1.5.7 Explosion | N/A | not for ATEX; LFP venting limited | - |
| 1.5.8 Noise | A | low noise; measure and declare | TP-16 |
| 1.5.9 Vibration | N/A | no hand-held / ride-on | - |
| 1.5.10 / 1.5.11 Radiation | A | Wi-Fi RF exposure EN 62311; immunity to external RF | TP-17, TP-18 |
| 1.5.12 Laser | A | class 1 devices only | supplier docs |
| 1.5.13 Hazardous substances | A (minor) | coffee steam only; no emissions | - |
| 1.5.14 Trapped in machine | N/A | - | - |
| 1.5.15 Slip/trip/fall | A | dock flat and marked | H42 |
| 1.5.16 Lightning | N/A | indoor | - |
| 1.6.1-1.6.5 Maintenance, access, isolation, intervention, cleaning | A | key service disconnect (lockable, LOTO), service points outside hazard zones with power off, cleaning instructions | MAN ch.8 |
| 1.7.1 / 1.7.1.1 / 1.7.1.2 Information & warning devices | A | HMI messages in user language; beacon + buzzer; warning devices self-check at start | TP-12 |
| 1.7.2 Residual risks warnings | A | pictograms (ISO 7010) at coffee, battery bay, rotation/crushing zone | MAN marking |
| 1.7.3 Marking | A | nameplate per Art. 10(5)(6) + 1.7.3 + 3.6.2 (see manual_outline.md) | label |
| 1.7.4 / 1.7.4.1 / 1.7.4.2 Instructions | A | manual per outline; non-professional public considered (1.7.4.1(b)) for safety info | MAN |

## Part 2 - Certain categories
| 2.1.1 / 2.1.2 Foodstuffs | A (barista) | coffee path materials compliant with Reg. 1935/2004 (supplier declaration); cleanable surfaces; drainage; cleaning instructions. Gap G5 | supplier DoC food |
| 2.2-2.4 | N/A | not hand-held, not impact, not wood | - |

## Part 3 - Mobility
| EHSR | A? | How met | Evidence |
|---|---|---|---|
| 3.1.1 Definitions | A | Giorgio = autonomous mobile machinery (autonomous mode); supervisor defined | MAN |
| 3.2.1 Driving position / 3.2.2 Seating / 3.2.3 Other persons | N/A | no ride-on | - |
| 3.2.4 Supervisory function | A | fleet/tablet supervision: receives state, position, alerts; allowed commands only stop / start / go to safe park; operation inhibited if supervision link absent (SF17, CE-only, non-safety software; to add to the electrical package) | TP-20 |
| 3.3 Control systems (unauthorised use, remote control, autonomous safety functions by itself) | A | key + login; remote commands bound to robot ID; all SF local in robot, independent of supervisor commands | TP-20, TP-21 |
| 3.3.1 Control devices | A (partly) | no driving position; manual jog via enabling device returns to neutral | SF14 |
| 3.3.2 Starting/moving (parts in travel position; area risks) | A | FAST travel only with arms parked and de-energised (SF8); objects travel in the tray; map zones per site risks | TP-10 |
| 3.3.3 Travelling (braking, emergency device, parking, obstacle detection (ii)) | A | ez-Wheel controlled braking + spring brakes (SBC); E-stop independent; parking brake; personnel detection (scanners, SF2/SF3); reverse speed <= 0.3 m/s permanent in the drives (SF5) | TP-01-03, TP-05, TP-06 |
| 3.3.4 Pedestrian-controlled | A (manual mode only) | hold-to-run, walking speed <= 0.3 m/s in manual (ASSUMED) | TP-12 |
| 3.3.5 Control circuit failure / steering failure autonomous | A | differential drive: steering by wheel speeds; any drive fault -> STO + brakes of both wheels (no single-wheel runaway) | TP-03 |
| 3.4.1 Uncontrolled oscillations of CoG | A | spring castors, accel limits, superstructure 43.7 kg with CoG ~911 mm checked in stability calc | TP-04 |
| 3.4.2-3.4.7 | N/A | no engine, no ride-on, no towing, no PTO (3.4.6 towing excluded in manual) | - |
| 3.5.1 Batteries incl. automatic charging | A | LFP sealed (no electrolyte ejection), easily accessible key disconnect, automatic charging with dead pads (SF10) and docking field (SF9), no traction while charging (SF11) | TP-13, TP-14 |
| 3.5.2 Fire | A | space/bracket for extinguisher not provided on robot (size) -> extinguisher class for Li-ion stated in manual (ASSUMED acceptable for small machine) | MAN |
| 3.5.3 / 3.5.4 | N/A | no hazardous substance application, indoor | - |
| 3.6.1 Signs, signals | A | beacon + sound when moving/rotating; warning devices monitored; signs readable from 1 m | TP-12 |
| 3.6.2 Marking (kW, kg) | A | nominal power kW and mass of usual configuration on nameplate | label |
| 3.6.3 Instructions (vibration, multiple uses) | A (partly) | vibration N/A declared; uses per variant | MAN |

## Other legislation (same technical file)
- RED Art. 3(1)(a) safety (no voltage limit; apply EN 62368-1 + EN 60204-1 + MR evidence), 3(1)(b) EMC, 3(2) radio,
  3(3)(d)(e)(f) cyber with EN 18031-1 (+ -2 for personal data) - TP-17-21.
- Battery Reg. 2023/1542: labels/DoC from Discover; our duties as producer (EPR registration in Italy, take-back, info).
- AI Act Art. 50: voice interface discloses AI.
