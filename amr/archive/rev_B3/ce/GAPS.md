# Gaps blocking fast CE (module A) - design rev B3, 2026-10-05

Effort = engineering effort ESTIMATE (person-days, pd) + calendar time; cost ESTIMATE where relevant.
SF IDs as in `RISK_ASSESSMENT.md` §3: SF1-SF16 = `../electrical/SAFETY_FUNCTIONS.md` rev B2, SF17 CE-only.
Rev B2: `../VERIFICATION.md` (93 items checked against official documents in `../../docs/fonti/`) closed every supplier
question; the base no longer depends on any supplier answer. Rows closed by it are marked CLOSED with the VERIFICATION IDs.

## Open gaps

| ID | Gap | Why it blocks | Fix | Effort |
|---|---|---|---|---|
| G1 | **OpenArm 2.0: no brakes, no STO, no safety-rated speed/force** | **MR Annex III 1.2.6(d)** "no moving part of the machinery or piece held by it shall fall" on power loss; 1.3.9; EN ISO 10218-1 stopping/braking; arm drop (H10) and collision (H08) residual R=6 | Fast: ship variant C48 (Kassow Edge DC / UR e-Series + DC OEM) for CE. Variant OA: add spring-applied brakes or gravity compensation on shoulder + elbow, stop cat 1 then contactor; SSM by scanners (SF7); keep OA as R&D (Art. 2(2)(m)) / fairs with non-conformity sign (Art. 4(2)) until done | C48: 10 pd integration. OA: 30-50 pd + 8-12 wk, motor/brake redesign |
| G3 | Safety requirements spec + PL calculations missing | no evidence for 1.2.1 / EN ISO 13849-1 | write SRS per SF1-SF17, SISTEMA (Pilz + SICK + Siemens libraries; ez-Wheel PFHd published in the manual), PNOZmulti Configurator program (free), validation per 13849-2. Rev B2 inputs now SOURCED: PNOZ B0/EF 4DI4DOR PFHd, SWD PFHd per function, PNOZ reaction time 54 ms, "one SC output + 2 contactors = PL e" | 15-20 pd |
| G4 | **ML must not be safety-relevant** | if any SF relied on ML -> Annex I Part A -> notified body | architecture rule: all SF in certified HW; ML outputs bounded; no in-field learning; document in Annex IV (n); TP-20 fault injection | 3 pd docs + review gate on every release |
| G5 | **Coffee module (24 V truck machine) has no DoC / food-contact declaration** | MR 2.1 + Reg. 1935/2004; EN 60335-2-15 evidence missing | buy a 24 V machine with CE DoC + food-contact declaration (with its own cover interlock), or an OEM vending module; thermal fuse + SF15 (KI4/K4) | 5 pd + sourcing 4-6 wk |
| G6 | **Wi-Fi module not chosen** | RED + EN 18031-1; the dock handshake now also runs over Wi-Fi/Ethernet (RoboPad has no wireless CAN) | pre-certified M.2/USB module with RED DoC + reports; EN 18031-1 on host SW; handshake authenticated (EN 18031-1 secure comms) | 2 pd choice; 10-15 pd 18031 docs; lab ~4-8 kEUR (ESTIMATE) |
| G7 | MR citation of harmonised standards | presumption under MR only for standards cited under MR | check OJ before signing; otherwise list as other specs | 1 pd, recheck at signing |
| G9 | Edges/stairs not detectable (2D scanner) | H22 S4 residual | site requirement + manual; optional safety-rated cliff sensors later | 1 pd docs |
| G10 | Supervisory function (3.2.4) and watchdog SF17 not implemented | MR 3.2.4 | fleet/tablet app: state, alerts, stop/start/park only; heartbeat | 10 pd SW |
| G11 | Dock as separate product | needs own LVD/EMC/RoHS DoC, enclosure, RCD guidance | **rev B2: NPB-750-48 (EMC Class B, IEC 60335-2-29) + OV relay (rev B3: Carlo Gavazzi DUB01CD48500V at 58.5 V)** -> no charger EMC test needed; certified enclosure; EN 62368-1 check for the controller. Only the C48 barista option with NPB-1700 (Class A radiated) needs the dock EMC test TP-19b | 5 pd (+ TP-19b only for the NPB-1700 option) |
| G12 | Safety software logging (1.1.9, 1.2.1(f)) | SW version + intervention log 5 y | log on Jetson + config CRC readout of PNOZ / SWD signatures (3058h, 6699h) / scanners; tamper-evident storage | 5 pd |
| G13 | Producer registrations | Battery Reg. EPR (IT register), WEEE, CRA vulnerability reporting (since 11 Sep 2026) | register company; publish security contact + support period | 3 pd admin |
| G15 | **SF15 PLr b to confirm (H13)** | if H13 is rated S2 -> PLr c | rev B2 fallback costs €0: KI4 on a free B0 safe SC output (O1) + U7 remote OFF as diverse channel | 0.5 pd |
| G16 | **SS1-t ramp-failure residual** (new rev B2) | the non-safe quick-stop ramp is not monitored (SS1-t, IEC 61800-5-2); on a ramp fault the stop is bounded by the SWD SLS-STO at 1.0 s and exceeds the field (CALC §7 info) | accept as residual H03 with TP-01b evidence, or upgrade later to a drive with safety-rated SS1-r when ez-Wheel releases it ("UNDER DEVELOPMENT" in the 2025 catalogue) | 1 pd + TP-01b |

## Closed by rev B2 (`../VERIFICATION.md`) and rev B3 (`../CAD_REV_B3.md`)

| ID | Was | Closed by |
|---|---|---|
| G17 | Mean Well clearances in the CAD (DDR 40 mm above / 20 mm below; upper rails 32 mm, DRDN40 under U1) | **CLOSED rev B3**: keep-out solids at the true module heights, 0 violations (3,086 pairs); no converter on an upper rail; one DIN position table CAD = `din_layout.md` = netlist (`CHECKS_AMR.md` §CAD) |
| – | Castor suspension (VERIFICATION CA1): no spring castor ≥ 90 kg fitted under the 134 mm roof; scan plane must stay ≤ 200 mm | **CLOSED rev B3**: Blickle L-ALST 80K on MGN15 guides + D-313J-02 springs in the spine gaps (`../CASTOR_SUSPENSION.md`), roof top 134 / plane 184.5 unchanged, swivel keep-outs 0 violations, travel check 0 |
| – | Scan plane vs body pitch (SICK OI p.40 ≤ 200 mm everywhere) | **CLOSED rev B3** by design limits: per-band accel/decel (CALC §7b) in the motion profile + manual; verified by TP-05/05b |
| – | K0V and dock OV relay without P/N | **CLOSED rev B3**: Carlo Gavazzi DUB01CD48500V (datasheet SOURCED, docs/fonti), XD3 bench-set 58.5 V, K0V 48.0 V |
| G2 | ez-Wheel at 24 V from a DC-DC needs supplier approval; regen | **CLOSED** [E1]: the SWD supply is specified only by voltage/current thresholds (UV 16/14 V, OV 32/34 V, OC 25/30 A); no battery required. Design rule: the 27 V DSR 50/5 clamps are mandatory (FW ≥ 1.1.4 disables phase-short braking if the source cannot accept current). Regen energy bounded by physics (½·m·v²). Verified by TP-03/TP-14 |
| G8 | Battery lying mounting / paralleling / BMS PL | **CLOSED** [D1, D2, D13]: lying allowed (only upside down forbidden), ≥ 50 mm at the top cover, hold-downs; up to 20 in parallel, same model, ≤ 50 mV at ≥ 95 % SoC, equal cables. BMS PL: none published -> no PL credit, independent layers (F0, K0 with LYNK NO "energised = OK", K0V 48 V, charger CV preset, dock OV relay) |
| G14 | Safety controller not frozen | **CLOSED** (rev B1), updated rev B2: PNOZ m B0 + 2 × EF 4DI4DOR + ES ETH (€1,812 net); C48 + EF 8DI4DO |
| – | PNOZ PFHd, "one SC output + 2 contactors = PL e", licence price, module order | **CLOSED** [P1-P13]: PFHd SOURCED; PL e with feedback loop and separate multicore cables; Configurator free; ES left, EF right, ≤ 6 |
| – | SWD test-pulse tolerance, scanner input pulse rejection | **REPLACED** [E6, S4]: positive-guided relay contacts (EF 4DI4DOR) + 2.2 kΩ bleed |
| – | SLSa permanent, asymmetric, mirrored wheels; SBU on INSafe | **CLOSED** [E7, E8] |
| – | 1-of-n field switching; system plug P/N | **CLOSED** [S1, S6] |
| – | PSEN cs3.1 series connection | **REPLACED** [P16]: separate input pairs |
| – | Eaton E-stop positive opening | **REPLACED** [EA1]: Siemens 3SU1400-1AA10-1CA0 |
| – | RoboPad wireless CAN, 75 A, 60 V limit, charger EMC class | **CLOSED / REPLACED** [R1, R5, R6, M12, M13]: RPCOL90-100 60 A, handshake over Wi-Fi/Ethernet, 59 V OV relay, NPB-750 Class B |
| – | K1/K2 DC breaking, SW80/ED250 ratings, F0 DC rating | **CLOSED** [SI1-SI5, AL1-AL3] |

## The 12 RESIDUAL items of VERIFICATION (no supplier answer needed)

| VERIFICATION ID | Item | Kind | How it is handled |
|---|---|---|---|
| E2 | SWD internal regen chopper not documented | type test | external clamps absorb all regen; TP-03 / TP-14 worst-case regen |
| E3 | SWD parking-brake torque | type test | TP-03a cat-0 stopping distance, TP-03b 6 % slope holding (0.76 Nm per motor) |
| E9 | SWD STO / ramp reaction time | type test | t_drive 40 ms ASSUMED in the fields; TP-01 measures SFRT, keep ≥ 2 × margin |
| E10 | SWD peak-torque duration | type test (performance) | not safety-relevant; drive acceleration test |
| D6 | battery prospective short-circuit current | design bound | every B48 device ≥ 20 kA DC (F0 25 kA); TP-14 fuse coordination |
| D12 | battery vibration rating | type test | hold-downs + prototype bump/vibration test (TP-22 endurance) |
| D13 | BMS PL / PFHd | no PL credit | independent layers (SF12); IEC 62619 CB certificate |
| P15 | PNOZ timer element for SS1-t | free download | PNOZmulti Configurator (free); B0 documented for E-stop with delay |
| P17 | Pilz prices | price | SECONDARY distributor prices used |
| X1 | prices of purchased parts | price | quotes replace ESTIMATE rows (`../INDUSTRIALIZATION.md` §8); rev B3: Blickle L-ALST 80K, HIWIN MGN15R/MGN15H prices are not published → QUOTE rows in `../bom_amr.csv` |
| X2 | Kassow Edge DC power | outside the base (C48 arms) | size C48 feeds on F5L/F5R ratings |
| X3 | OpenArm gripper force, arm stopping time | outside the base (OA arms) | measure (EN ISO 13855 stopping time); tray-carry rule |

**Critical path (variant C48)**: G3 -> TP core tests (TP-01/01b/03a/03b/05/05b/06/23); G6 + G5 sourcing in parallel.

**Rev B3 type-test residuals (no supplier answer needed):** castor swivel radius 79.4 mm calculated (verified in TP-23 over 360°; Blickle STEP when the quote comes), pitch dynamic amplification 1.2 (TP-05b), castor rolling resistance and 5.4 km/h use (TP-22), threshold climbing μ 0.5 (TP-01), centre-bay fan conductance (TP-11 heat-run).
Variant OA adds G1 (longest item).
