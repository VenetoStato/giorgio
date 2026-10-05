# Giorgio CE technical file (skeleton), design rev B - 2026-10-05

Rev B (owner decision 2026-10-05): **no waist yaw joint**. The superstructure is bolted to the fixed top deck (z 353 mm);
2 SICK nanoScan3 Pro I/O kept; every component chosen to be certifiable. All waist hazards, safety functions and tests
of rev A are removed and the IDs renumbered (SF1-SF17, H01-H44, TP-01-TP-22). SF1-SF16 are identical to
`../electrical/SAFETY_FUNCTIONS.md` rev B2 (TP-01b, TP-03a/b and TP-19b added in rev B2); SF17 (supervisory watchdog) is CE-only and not yet in the electrical package.
Safety controller rev B2: **Pilz PNOZmulti 2** (PNOZ m B0 + 2 × EF 4DI4DOR relay modules + ES ETH; C48 adds an EF 8DI4DO). Rev B2 applies the design changes of `../VERIFICATION.md` (93 items checked against official documents): no supplier answer is needed any more for the base.

## Executive summary
- **Route**: Giorgio (own AMR base + two arms + head + coffee module + dock) is one *machine*. It is not in Annex I of
  the Machinery Regulation (EU) 2023/1230 as long as **no safety function is performed by ML/AI** -> **module A**
  (internal production control, Art. 25(4), Annex VI), no notified body. Before 20 Jan 2027 Directive 2006/42/EC applies
  (same outcome: self-assessment, Annex VIII). We design and declare directly to the Regulation.
- **Fastest variant**: certified DC cobot arms (Kassow Edge / UR e-Series + DC OEM box). The OpenArm variant (no brakes,
  no STO) is CE-capable only with brakes or gravity compensation plus external safety (gap G1, MR Annex III 1.2.6(d));
  until then it is R&D only (exclusion Art. 2(2)(m)) or shown at fairs with a non-conformity sign (Art. 4(2)).
- **Other legislation**: RED 2014/53/EU for Wi-Fi (safety Art. 3(1)(a) with no voltage threshold, EMC 3(1)(b), radio 3(2),
  cyber 3(3)(d)(e)(f) via EN 18031-1), Battery Reg. (EU) 2023/1542, RoHS, WEEE, food-contact materials (coffee module),
  AI Act Art. 50 (transparency), CRA from 11 Dec 2027.
- **Timeline** (ESTIMATE): cobot variant ~16-20 weeks from design freeze if suppliers deliver documents; OpenArm variant
  +8-12 weeks (brakes + drop tests + SSM validation). Rev B removes the waist validation from the critical path.
- **Main blockers**: OpenArm without brakes (G1), ez-Wheel supplied from DC-DC (G2 CLOSED in rev B2: supply interface fully specified, 27 V clamps mandatory), coffee
  module without DoC or food-contact declaration (G5), Wi-Fi module not chosen (G6), coffee-stop PLr b to be
  confirmed (G14, safety controller now frozen: Pilz PNOZmulti 2), ML kept outside the safety path (G4). Details in `GAPS.md`.

## Files in this folder
| File | Annex IV Part A item |
|---|---|
| README.md (this) | (a) description, (e)/(f) standards, (k) supplier DoCs |
| RISK_ASSESSMENT.md + risk_assessment.csv | (b) risk assessment, residual risks |
| ESSENTIAL_REQUIREMENTS.md | (b)(i)(ii) EHSR list + measures |
| TEST_PLAN.md | (g) tests, calculations; (n) sensor-system limits |
| DoC_draft.md | Annex V Part A |
| manual_outline.md | (i) instructions for use, marking |
| GAPS.md | open items blocking fast CE |
| To add later | (c)(d) drawings/schematics (`../out/`, `../electrical/`), (h)(l) production control plan, (m) safety SW source on request, safety-controller project + report, SISTEMA files |

## 1. Route
1. **Legal basis**: Reg. (EU) 2023/1230 (MR) applies from 20 Jan 2027 (per corrigendum; original OJ text: 14 Jan 2027).
   Units placed on the market before that date: Directive 2006/42/EC, Annex II 1.A DoC, Annex VIII self-assessment.
   Design to MR now (superset for our case: 1.1.9, 1.2.1 self-evolving, 3.2.4, 3.3.3 autonomous, 3.5.1 auto-charging).
2. **Product = one machine**: base + arms + head + coffee module + dock. We, as Giorgio's manufacturer, are responsible
   for the whole; supplier products enter as components (DoC) or partly completed machinery (DoI).
3. **Annex I check** (MR Annex I Part A items 5/6): only safety components / embedded systems with **self-evolving
   behaviour using ML that ensure safety functions**. Giorgio: all safety functions are in certified hardware
   (SICK nanoScan3, Pilz PNOZmulti 2 safety controller, ez-Wheel drive safety, Siemens 3SU1 E-stops, safety contactors, cobot safety
   controller). ML (navigation, VLA policies, speech) is non-safety and frozen in the field -> not Annex I ->
   **module A per Art. 25(4), Annex VI**. Kept true by design (GAPS G4) and documented (Annex IV (n)).
4. **Harmonised standards caveat**: standards cited under 2006/42/EC do not automatically give presumption under MR.
   Before signing an MR DoC, check the OJ list under MR; if a standard is not yet cited, apply it anyway and list it
   in the DoC as "other technical specification" (module A stays allowed for non-Annex-I machinery).
5. **Other Union legislation on the same DoC** (MR Annex V point 6 allows a single DoC): RED 2014/53/EU (the host with
   integrated Wi-Fi is radio equipment; RED covers safety and EMC objectives, so LVD/EMCD are not applied separately to
   the robot), RoHS 2011/65/EU (see note), Battery Reg. 2023/1542 (separate obligations, not a DoC item).
   The **dock** is a separate 230 V product: LVD 2014/35/EU + EMCD 2014/30/EU (+ RoHS), own DoC.

Note RoHS: Giorgio could be argued out of scope as "non-road mobile machinery made available exclusively for professional
use" (RoHS Art. 2(4)(g)); barista use in public makes that fragile -> declare RoHS anyway from supplier declarations
(ASSUMED low effort, all modules are commercial CE parts).

## 2. Legislation and standards matrix
H = harmonised (presumption, verify OJ under MR), S = state of the art / other spec.

| Part | Legislation | Standards (main clauses) |
|---|---|---|
| Whole machine | MR Annex III Part 1, 2.1 (food), 3 (mobility) | EN ISO 12100:2010 (H, risk assessment cl. 5-6); EN ISO 13849-1:2023 (H, PLr Annex A, cl. 4-6) + EN ISO 13849-2 (validation); EN 60204-1:2018 (H, cl. 7 protection, 9 control, 10 E-stop, 16 marking); EN ISO 13850 (E-stop); EN ISO 13857/13854 (gaps, reach); EN ISO 13732-1 (hot surfaces); EN ISO 7010 / ISO 3864 (signs) |
| Base (AMR) | MR 3.3.2, 3.3.3, 3.3.5, 3.4.1, 3.2.4, 1.3.1 | EN ISO 3691-4:2023 (H, Decision 2024/1329): cl. 4 (braking, speed control, automatic battery charging, stability, operating modes, personnel detection/protective fields, warning systems; required PL per safety function), cl. 5 verification (test pieces, stopping and stability tests), cl. 6 information for use. Sub-clause numbers to be filled from the purchased standard. ISO/TS 3691-8 informative. EN IEC 61800-5-2 (drive safety functions, supplier side) |
| Arms - cobot variant | MR 1.3.7, 1.2.1 | EN ISO 10218-1:2025 (supplier, robot), EN ISO 10218-2:2025 (H via Decision (EU) 2026/2015; our application: PFL biomechanical limits annex ex ISO/TS 15066, SSM, layout), EN ISO 13849-1 |
| Arms - OpenArm R&D | MR 1.2.6(d), 1.3.7, 1.3.9 | As above, but we become the robot manufacturer: EN ISO 10218-1:2025 clauses on stopping, braking, axis limiting; stop cat 0/1 per EN 60204-1 9.2.2 |
| Public service use | MR 1.1.6 (f)(g), 1.3.7, 1.7.4.1(b) | EN ISO 13482:2014 (H; mobile servant robot: battery, stability, physical contact, travel, autonomous decisions) where 3691-4 does not cover public/untrained persons |
| Dock + charging | MR 3.5.1 (auto charging), 1.5.1; dock: LVD + EMCD | EN IEC 60335-2-29 (charger, supplier SOURCED: NPB-750-48, EMC Class B; NPB-1700 only as the C48 barista option with a dock EMC test); EN IEC 61851 not applicable (not EV); EN ISO 3691-4 cl. 4 (automatic battery charging); EN 62368-1 for the dock controller box (ASSUMED); EN IEC 61000-6-1/-6-3 |
| Battery | Reg. 2023/1542 (Art. 13 labelling via Discover, Art. 11 removability by professionals, Art. 55-56 EPR registration in IT); MR 3.5.1, 3.5.2 | IEC 62619 (SOURCED by Discover), UN 38.3, EN IEC 62485-6 (guidance), UL 2271 (SOURCED) |
| 48 V DC system | MR 1.5.1 (LVD not applicable < 75 V DC), RED 3(1)(a) | EN 60204-1 cl. 6.4 PELV, 7.2 overcurrent, 13 wiring; EN IEC 62368-1 for ICT parts (Jetson, Wi-Fi) |
| Coffee module | MR 2.1, 1.5.5, 1.3.8.2; Reg. (EC) 1935/2004 + 2023/2006 (food contact) | EN 60335-2-15 (as spec), EN ISO 14159 (S), EN 1672-2 (S) |
| Electronics / EMC | RED Art. 3(1)(b) | EN 301 489-1/-17, EN IEC 61000-6-1 + -6-3 (public), EN IEC 61000-6-2 (industrial sites), IEC 61000-6-7 / IEC 61326-3-1 (immunity of safety functions, S) |
| Radio (Wi-Fi) | RED Art. 3(2), 3(1)(a) | EN 300 328, EN 301 893, EN 62311 / EN 50663 |
| Software / cyber | MR 1.1.9, 1.2.1; RED 3(3)(d)(e)(f) via Delegated Reg. (EU) 2022/30; CRA (from 11 Dec 2027; reporting from 11 Sep 2026) | EN 18031-1 (H from 1 Aug 2025; -2 likely applies: cameras + microphone process personal data); IEC 62443-4-1/-4-2 (S); EN ISO 13849-1 software requirements |
| AI / ML | AI Act (EU) 2024/1689 Art. 50 (voice agent says it is an AI); high-risk route via MR only if AI is a safety component with third-party assessment (not our case); machinery obligations shifted to 2 Aug 2028 by Digital Omnibus 2026/1744 | MR 1.2.1 self-evolving clauses as design rules |
| Lasers | MR 1.5.12 | EN 60825-1 class 1 (nanoScan3, Orbbec Gemini 336L IR projector - SOURCED from supplier manuals) |
| Noise | MR 1.5.8, 1.7.4.2(u) | EN ISO 3744 / EN ISO 11201 |
| Data / privacy (not CE) | GDPR, Data Act 2023/2854 Art. 3 | - |

## 3. What we need from each supplier
| Component | Documents to request | Status |
|---|---|---|
| ez-Wheel SWD 125 (x2) | EU DoI or DoC; INERIS certificate for STO/SBC/SLS/SLSa/SMS (SLSa permanent activation for SF5) + PL/SIL, PFHd per function; safety manual; PFHd per function (manual p.89-90); EMC report; DC-DC supply: interface specified (VERIFICATION E1) | INERIS DoC SOURCED; DC-DC CLOSED |
| SICK nanoScan3 Pro I/O (x2) | EU DoC (safety component + EMC + RoHS), type-examination certificate (IEC 61496-3 Type 3, PL d), PFHd, response time, laser class | standard SICK docs |
| Safety controller Pilz PNOZmulti 2: PNOZ m B0, 2 × EF 4DI4DOR, ES ETH (`../electrical/`) | EU DoC, TÜV certificate (PL e / SIL CL 3), PFHd per module (published: B0 manual p.48, catalogue p.216), PNOZmulti Configurator project report | frozen 2026-10-05; PFHd and "one SC output + 2 contactors = PL e" to request from Pilz |
| Siemens 3SU1 E-stops (3SU1400-1AA10-1CA0), Eaton M22 reset + key selector; enabling pendant | DoC, B10D, EN ISO 13850 / IEC 60947-5-8 conformity | standard |
| Safety contactors K1/K2 (arm cut-off), SR1 safety relay | DoC, B10D, mirror contacts per EN 60947-4-1 Annex F | selected (`../electrical/`) |
| Pilz PSEN cs3.1 arm-rest sensors (OpenArm, separate input pairs) | DoC, PL e / ISO 14119 type 4 certificate | standard Pilz docs |
| Discover AES PRO DLP-GC2-48V (x2) | DoC (EMC/RoHS), IEC 62619 + UN 38.3 summary, UL 2271, Battery Reg. label data/DoC (Art. 18), BMS protection limits, lying mounting + parallel use: documented in the installation manual 805-0027 (VERIFICATION D1/D2) | CLOSED |
| Mean Well DDR-480C-24 / DDR-240C-24 / DRDN40 | DoC, CB/IEC 62368-1, EMC | standard |
| Mean Well NPB-750-48 (dock) | DoC (LVD/EMC/RoHS), EN IEC 60335-2-29 CB report, EMC Class B | SOURCED (data sheet in ../../docs/fonti) |
| Roboteq RoboPad | DoC, current rating, contact material, IP | to request |
| Albright SW80B / ED250B, main fuse | datasheets, DC breaking capacity at 58 V | catalogue |
| Jetson Orin NX + carrier | DoC (EMC/RoHS), carrier board DoC | to request |
| Wi-Fi module | RED DoC + test reports (EN 300 328, 301 893, 301 489-17, 62311), antenna list, integration guide | NOT CHOSEN (G6) |
| Orbbec Gemini 336L, fisheye USB cams | DoC (EMC/RoHS), laser class 1 statement | to request |
| Kassow Edge / UR e-Series + DC OEM | EU DoI, ISO 10218-1 certificate, safety functions PL d table (PFL, SLS, SLP, SS1/SS2), stopping distance/time tables, DC supply limits | cobot variant |
| Enactic OpenArm 2.0 + Damiao motors | no CE documents (ASSUMED); motor datasheets (torque, back-drive, encoder), any EMC report | R&D variant: we take full responsibility |
| Coffee machine 24 V | DoC (EMC/RoHS), EN 60335-2-15 report, food-contact declaration (Reg. 1935/2004) | seller states none -> G5 |
| Actuonix P16, HIWIN MGN12 | datasheets | catalogue |
| Castors, PA12 shells, tray | flammability (UL 94), food contact for tray | to request |

## 4. Timeline (ESTIMATE, weeks from design freeze, cobot variant)
| Wk | Activity |
|---|---|
| 0-2 | Freeze design; risk assessment v1 (this folder); supplier document requests; choose Wi-Fi module (safety controller chosen: Pilz PNOZmulti 2) |
| 2-6 | Safety requirements spec; SISTEMA per SF; safety-controller program + field sets; arm safety config |
| 4-8 | Prototype build; EMC pre-scan; stability calculation |
| 8-12 | V&V tests (TEST_PLAN.md): stopping, fields, stability, E-stop, PFL/SSM, dock, endurance start |
| 10-14 | Accredited lab: EMC + RED radio + RF exposure; EN 18031-1 assessment |
| 12-16 | Instructions, labels, DoC; production control plan; technical file freeze; sign DoC |
| 16-20 | Buffer for retests / supplier delays |

OpenArm variant: add brake/gravity-compensation retrofit, drop tests, SSM validation (+8-12 wk, ESTIMATE).
Placing on the market before 20 Jan 2027 is unrealistic for the full file -> plan the first DoC under MR.
