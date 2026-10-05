# Giorgio own AMR: electrical + safety package (rev B4, 2026-10-05)

Owner goal: our own AMR base, quickly CE-certifiable, built only from **certified off-the-shelf DIN/industrial modules,
with no custom PCB, at minimum cost**. Rev B follows the owner decision of 2026-10-05: **no waist yaw joint**. The top deck
(z 343…353) is the fixed superstructure flange. The electronics that sat on the rotating waist plate now live in the
**centre bay** of the base (CAD P10/P11/E50/E51/E52), and cables to the superstructure pass the deck grommet E53 at (62, 0).

| File | Content |
|---|---|
| `netlist_amr.yaml` | rev B2: every device (MPN, ratings, certificate, price + tag/source), DC-DC load tables, power circuits, safety I/O map (PNOZmulti 2), safety-controller options, field sets, PFHd inputs |
| `single_line.svg/.png` | power single-line: B48 → F0 → Q0 → K0 → branches, centre bay, dock path, BMS/CAN |
| `safety_diagram.svg/.png` | PNOZmulti 2 wiring overview generated from `safety_io` |
| `cable_schedule.csv` | 57 cables mapped to CAD harnesses H01–H10 (rev B names) |
| `din_layout.md` | rev B3: ONE position table generated from the CAD (`../out/parts.json`), rules, heat per bay |
| `SAFETY_FUNCTIONS.md` | SF1–SF16 (renumbered, no waist functions) with PLr reasoning, architecture, PL estimate |
| `check_amr.py` → `CHECKS_AMR.md` | **242 PASS, 0 FAIL** (rev B4), 11 OPEN rows (B48 branch fuses: Mersen HP10M IEC breaking capacity 10 kA DC vs the undocumented 20 kA Isc design bound → measure Isc in TP-14, CERTAINTY G-29) and INFO rows (BOM, options, passive cooling answered by fans, battery envelope, BMS without PL credit, regen with one DSR off, OpenArm regen) |
| `make_diagrams.py` | regenerates both drawings (`~/giorgio_sim/cad/.env/bin/python make_diagrams.py`) |

Tags: **SOURCED** (manufacturer document), **SECONDARY** (distributor listing, fetched 2026-10-05, or a project file),
**ASSUMED** (to verify). In rev B, 73 % of the package value is SOURCED/SECONDARY (rev A: 36 %).

## B4. Rev B4: CERTAINTY.md fixes (2026-10-05)

This section wins over B3, B2 and §0–14 where they disagree. Details: `../CAD_REV_B4.md`, `../CERTAINTY.md`, `din_layout.md`.

- **Speed bands (G-04):** SMS **1.1 m/s** = the published castor rating speed (Blickle 754464, 4 km/h); SLS[1] 0.3 m/s on INSafe_1/2
  (SR1), **SLS[2] 0.7 m/s on INSafe_3/4 through a third PNOZ m EF 4DI4DOR (SR3)**; SR2 O3 → CI4 = FS4 MEDIUM (1-of-4 code). Station:
  SC1 | SC0 | SR1 | SR2 | SR3 | (SX2, C48) = option P5 (€2,192.17 + terminal sets €115.23, eibabo net). 10 relay contacts with 2.2 kΩ
  Vishay PR01 bleed resistors.
- **Fields (F1/F2, CALC §7):** with Z_F 150 mm: 401 / 613 / 943 mm from the scanner, 357 / 407 / 457 mm beside the robot; rotation circle
  R 912 mm; arm field R 2472 mm with 50 mm resolution.
- **Regen (F5):** each DSR 50/5 sinks ≤ 5 A at 27 V (135 W); 2 units 270 W ≥ 200 W peak regen at 1.1 m/s; continuous 6.4 W each at
  43 °C clamp air. Over-temperature cut-out releases the clamp: DDR OVP / SWD OV then switch traction off (INFO row, RISK H20, TP-14).
  No CE statement in the maxon instructions (netlist "CE [ASSUMED]" removed).
- **Fuses (G-13):** Mersen HP10M gPV in CUS101HEL holders (Mersen datasheets): F1 6, F2 20, F3/F4 20, F5L/R 15 (OA) / 25 (C48), F7 32,
  F8L/R 20, WF1 6, WF2 12, WF3 2, FJ 4, FAL/FAR 25, FCF 15 A. The IEC 60269-6 breaking capacity is 10 kA DC (UL 2579 50 kA): new OPEN
  item G-29 (B48 prospective Isc to be measured, acceptance ≤ 10 kA).
- **Parts closed:** K3 12 Ω (G-11); K0P/K3 resistors Vishay Dale RH-50 (5 × rated power for 5 s, G-25); D0 = Vishay 1N5408 on the SW80
  coil + Siemens 3RT2926-1BB00 on K1/K2 (G-23); JR1 = 2 × Phoenix EMG 17-OV-TTL/24DC/2 driven by the Jetson 3.3 V GPIO (G-22); dock
  controller Finder OPTA 8A.04.9.024.8320 + Albright SW80B (G-24); NET1 FL SWITCH 1008N 1085256 (9–32 V, 28 mA); 0 V block WPD 100
  (101 A); T24 terminals Phoenix PT 16 N (76 A); E-stops Siemens 3SU1050-1HB20-0AA0 (B10 100 000); reset/key Eaton M22 (216931,
  216376, 216900); enabling switch Euchner ZSA2B4G02CC2322 + binder M12 5-pole socket; fans San Ace 9WPA0624S4001 / 9WPA0424H6001;
  Jetson Seeed reComputer J4012 (9–19 V, 10–25 W, FJ 4 A).
- **Layout (F4):** the coaxial SWD bodies fill the centre bay below z 129: one centre rail per face at z 213 (converters + FCF); E57,
  E5A, E59 on the right MID rails (loc RM, z 175), NET1 on its own rail (z 164), K4 and CAN1 on the right HIGH rail (to x 298, A10).
- **Thermal (F3):** rated room 0…+35 °C; SWD in tunnels with E44 fans (tunnel outlet 35.9 / 37.9 °C); bays ≤ 39 °C; centre 38 °C.

## B3. Rev B3: one layout with the CAD, castor suspension, K0V / XD3 part numbers (2026-10-05)

This section wins over B2 and §0–14 where they disagree. Details: `../CAD_REV_B3.md`, `din_layout.md`.

### B3.1 DIN layout = CAD
- One position table (`din_layout.md` §1, generated from `../out/parts.json`); `netlist_amr.yaml` `loc` codes are LL/LM/LU/LC,
  RL/RU/RC/RW, CB, CD and are checked against the CAD by `check_amr.py` (§CAD: 0 mismatches).
- Every DDR/DRDN has its Mean Well keep-out (40 above / 20 below / 5 sides) in the CAD at the **true module heights** (DRDN40
  125.2 mm, DDR-240 depth 113.5 mm): 0 violations. No converter on an upper rail any more (rev B2 §6 conflicts closed).
- Moves: U3 → centre bay LOW right (T24 ORing; W10/W11 0.7/0.6 m); U6 → left MID; U5 → right LOW rear; **U8 → RR corner rail** (out of
  the castor swivel space; H06a 0.6 m); E2F WF1–3 → left HIGH rear (next to F2/E18, as asked in B2); R1a/R1b and RAL/RAR (DSR 50/5)
  → deck underside above the packs; KI4 + K0V on the right HIGH rail; PNOZ station SC1 | SC0 | SR1 | SR2 | (SX2) contiguous;
  the rev B1 SX1 (CAD E22) is gone from the CAD as well.
- **G01 LYNK II 120 × 135 × 44 mm** on bracket E38b against the right side cover above the SWD (W20 ≈ 0.8 m ≤ 1.4 m).
- H01 = H02 = 0.75 m (CAD harnesses are mirror images; rev B2 netlist had 1.01 / 0.51 m).
- Heat per bay updated (left 45.9 W, right 61.4 W, docked 72.4 W, centre 22.5 W): all PASS with fans.

### B3.2 K0V and XD3: Carlo Gavazzi DUB01CD48500V (SOURCED)
Datasheet `../../docs/fonti/CarloGavazzi_DUB01-PUB01_datasheet_2025-03-03.pdf`
(https://www.gavazziautomation.com/fileadmin/images/PIM/DATASHEET/ENG/DUB01CB%20DS%20ENG.pdf):
> "DUB 01 C D48 500V" … "2 to 500 V AC/DC" (p.1); "5 to 50 V AC/DC >500 kΩ 350 V" and "20 to 200 V AC/DC >500 kΩ 600 V" (range, input
> impedance, max. voltage, p.1); "D48: 24 to 48 VAC/DC ± 15% … insulated" (p.2); "Voltage level setting on relative scale: 10 to 110% on
> full scale", "Setting of hysteresis on relative scale: 0 to 30% on set value", "Setting of delay on alarm time on absolute scale (0.1 to
> 30 s)" (p.3); "Monitoring function ON: Over voltage OFF: Under voltage", "Relay working mode ON: Normally De-Energized OFF: Normally
> Energized" (p.3); "Repeatability ± 0.5% on full-scale"; "DC 12 5 A @ 24 VDC", "DC 13 2.5 A @ 24 VDC"; "22.5 x 80 x 99.5 mm";
> "Approvals UL, CSA, CCC"; "Product standard EN 60255-6" (p.2).

| Function | Setting | Check |
|---|---|---|
| **K0V** 48 V application cut-off (K0 coil chain) | 50 V range, under-voltage, normally energised (drops on low voltage **and** on loss of its 24 V supply = fail-safe), level 96 % = 48.0 V, delay 5 s, hysteresis ~4 % (re-close ≈ 50 V) | ±0.25 V repeatability; bus max 58.4 V ≪ 350 V input max; contact 0.7 A ≪ DC13 2.5 A |
| **XD3** dock over-voltage (dock contactor coil) | 200 V range, over-voltage, normally energised, **bench-set 58.5 V**, delay 0.1 s | 58.5 ± 1.0 V (±0.5 % of 200 V) = 57.5…59.5 V: above CV 56.8 V, below the RoboPad 60 V; TP-13 calibrates and verifies |

Price: DigiKey 1864-1123-ND **USD 177.65** (1 pc, 2026-10-05) → €163 each (SECONDARY; replaces the €90 ASSUMED). Netlist, BOM and
`CHECKS_AMR.md` (§Charge rows for K0V/XD3, §CAD envelope row) updated. Other makes (Finder 71, Phoenix EMD, Dold, ABB CM-ESS) were not
retrievable in this session; the DUB01 meets every requirement with a downloaded datasheet, so no open item remains.

### B3.3 Castor suspension (affects only mechanics)
Sprung Blickle L-ALST 80K castors on MGN15 guides in the spine/battery gaps (`../CASTOR_SUSPENSION.md`): no electrical change except the
moves above. The E42 centre-bay fans stay; the gap air path now passes the spring columns.

## B2. Rev B2: design changes from `../VERIFICATION.md` (2026-10-05)

`../VERIFICATION.md` checked 93 items against official manufacturer documents (saved in `../../docs/fonti/`): 73 CLOSED,
8 REPLACE, 12 RESIDUAL. Rev B2 applies every REPLACE and every "design change" it found. Row IDs are quoted as [V:xx].
Sections 0–14 below are the rev B1 text; where they disagree with this section, **this section wins**.

### B2.1 Safety controller: relay interface (E6, S4, P6, P14)
- **2 × Pilz PNOZ m EF 4DI4DOR (772143)**, 22.5 mm each, right of the B0 on the right upper rail (x −189.5…−167 and
  −167…−144.5, `din_layout.md` §3). Positive-guided contacts, DC1 24 V 10 mA…6 A, 2-channel PL e PFH 7.52E-12 [pilz_cat].
  - **SR1** O0/O1 → SWD STO_1/STO_2, O2/O3 → SWD INSafe_1/2 (both drives in parallel): no test pulses reach inputs whose
    tolerance ez-Wheel does not publish.
  - **SR2** O0–O2 → nanoScan3 CI1–CI3 (both scanners), scanner input delay class "tactile controls (relays)" (OI p.89);
    O3 spare. Single-channel contacts are acceptable because the 1-of-3 code turns any single contact fault into an invalid
    code (OSSDs off).
  - **Bleed resistors RB1–RB7**: 2.2 kΩ 1 W per used contact (10.7 mA at S24 −2 % ≥ 10 mA minimum; 0.26 W), in double-level
    component terminals inside XS24.
- The rev B1 **EF 8DI4DO (SX1) is removed**: K1+K2 move to SC0 O0 (2 A SC output, two loads PL e with the feedback loop and
  **K1/K2 coil wires in separate multicore cables W30/W31**, B0 manual p.29); its inputs move to SR1/SR2. I/O: 26 of 28
  inputs, 1 SC + 7 relay outputs, 2 auxiliary outputs (KI4, KS). C48 adds SX2 EF 8DI4DO (3 modules right ≤ 6).
- Chosen option P4 = B0 + 2 × EF 4DI4DOR + ES ETH = **€1,812.45 net** (+€437.58 vs rev B1). It is the cheapest option with
  relay outputs (`CHECKS_AMR.md` → Safety ctrl options). Configurator: free (V11+). Terminal sets are accessories (€90 ESTIMATE).
- PFHd now SOURCED for the PNOZ (B0 CPU 4.74E-10, EF CPU 2.84E-10) and the SWD (STO 1.42E-9, SLS/SLSa/SBC3 2.29E-7).

### B2.2 Stop timing: SS1-t with STO at 1.2 s (E3, E4, P8, E9)
- **Decision: option A, STO delay ≥ 1.1 s → set 1.2 s.** At t = 0 the PNOZ drops INSafe_1/2 (SLS[1] 0.3 m/s, SWD t_SLS
  6691h = 1.0 s, violation → STO) and reports the stop to the Jetson; the SWD quick-stop ramp (1.5 m/s², non-safe) brings the
  robot to rest by 0.827 s from the 1.1 m/s SMS (rev B4); at 1.2 s SR1 opens STO_1/STO_2 (SBC).
- Why not option B (0.5 s, fields sized for STO mid-ramp): the tail would be a cat-0 phase-short stop with no published decel,
  so the field could not be computed, and the cat-0 tip margin is SF 1.23. The cost of A is the ramp-failure case: bounded
  by the SWD SLS-STO at 1.0 s (PL d), recorded as residual risk H03 and measured in TP-01b.
- t_logic 54 ms (SOURCED, relay path), t_drive 40 ms (ASSUMED 2 × 20 ms, measure). Fields (CALC §7 rev B4, incl. Z_F 150 mm): **401 / 613 / 943 mm**
  at 0.3 / 0.7 / 1.1 m/s (rev B3 without Z_F: 251 / 535 / 894 / 1240 mm at 0.3 / 0.8 / 1.2 / 1.5 m/s). Field switching waits t_SLS + 0.1 = 1.1 s.
- Type tests replace unpublished drive data: cat-0 stopping distance (TP-03a), 6 % slope holding, 0.76 Nm per motor
  (TP-03b), SWD reaction time (TP-01).

### B2.3 Traction T24 (E1)
- The two **maxon DSR 50/5 27 V clamps are mandatory**: SWD firmware ≥ 1.1.4 disables the phase-short brake if the source
  cannot accept current. Window 24 < 27 < 28.8 (DDR OVP min) < 32 V (SWD OV alert). No ez-Wheel approval is needed: the
  supply interface is fully specified by voltage/current thresholds.

### B2.4 K0 chain (D4, D10, M2)
- New coil chain: **S24 → G01 LYNK II relay R1 NO (pins 12→10) programmed "activated = no BMS alarm" (energised = OK) →
  K0V (DC voltage-monitoring relay, opens below 48.0 V, ~5 s delay) → K0P + K0T → K0 SW80B coil with freewheel diode D0**.
  Alarm, gateway power loss, wire break and low voltage all open K0. The NC contact of rev B1 was closed when de-energised.
  LYNK relay 5 A at ≤ 30 V DC ≫ 0.7 A coil load. K0P/K4 (Finder 22.32) have an internal varistor; K1/K2 get Siemens
  diode + Zener suppressors (fast drop-out keeps the SS1-t timing).
- **K0V = the 48 V application low-voltage cut-off** (Discover: program it at or above 48.0 V; the BMS itself cuts at 40 V
  and then needs a manual ON). K0V opens K0 (motion loads); the Jetson then logs, parks and switches the packs off over the
  LYNK remote ON/OFF so the always-on loads cannot drain them to the 40 V lock-out. P/N to select from a downloaded datasheet
  covering ≥ 65 V DC (same type as the dock XD3); ESTIMATE €90. Placed on the right upper rail (+60.2…+82.7), sensing U4's input.
- **DDR remote from a K0 NC auxiliary contact** (DDR: open = ON, short = OFF). SW80 order code: **SW80B…A** with a
  continuously rated 24 V DC coil (B = blowouts, polarity-sensitive; A = aux contact). If the A-suffix aux is NO-only on the
  Albright drawing at order, a 6.2 mm interface relay in parallel with the K0 coil gives the NC function.
- G01 LYNK II is **120 × 135 × 44 mm** (not 65 × 70 × 30): new mounting spot needed (`din_layout.md` §4).

### B2.5 Converters (M1, M3, M7, M9)
- All DDR-xxx and DRDN40 **vertical, input terminals down, 5 mm left/right, 40 mm above, 20 mm below**. E50 lying on P10 is
  not allowed (the CAD stream moves the centre-bay DC-DCs to vertical rails). The upper side rails leave 32 mm above the
  DDRs: CAD conflict listed in `din_layout.md` §6.
- DDR-480 efficiency 92 % (SOURCED). DDR-60L-5 is 52.5 mm wide. DDR-240 (S24) maximum ambient 50 °C → **the right-bay fans
  are required for S24**; NTC alarm → park.

### B2.6 Battery (D1, D2, D5, D8, D9, D11, D13)
- Ratings per pack (Discover 805-0027 Rev N): **15 A continuous** (5 back-to-back full cycles without over-temperature),
  **58 A for 1 h**, **90 A RMS for 10 s**, BMS trips > 58 A for 10 s; charge 15 A continuous / 29 A 1 h; internal fuse 58 V
  60 A; BMS switches with a main **relay** (not FETs). Pair: 30 A / 116 A / 180 A (linear, no share factor). The rev B1
  "116 A continuous" was the 1-hour rating.
- **Duty check (CALC §5):** profile averages 3–19 A, worst RMS 19.7 A (C48 barista) ≤ 30 A → PASS. Worst sustained envelope
  (2 arms continuous + drives S1 + coffee) **37.4 A at 48 V**: above the 30 A cycle rating, 32 % of the 116 A 1-hour rating
  and below one pack's 58 A; it is a transient envelope (it would empty the battery in 1.5 h). **Decision: no 3rd pack;** the
  Jetson energy manager keeps the 1-hour rolling average of the pack current (LYNK) ≤ 30 A by capping arm power first.
  All-peaks-at-once 91 A at 44 V = 46 A per pack < 58 A: the BMS never sees an over-current condition.
- Packs lie on their side (allowed; only upside down is forbidden), ≥ 50 mm free in front of the top cover, hold-downs;
  H01 = H02 in length and gauge; packs within 50 mV at ≥ 95 % SoC before connecting (commissioning).

### B2.7 Dock (M10–M14, R1–R6)
- **Charger: NPB-750-48 (decision).** EMC Class B (RoboPad requires an EN 61000-6-3 charger), IEC 60335-2-29, DIP 2 OFF /
  3 ON = "flooded" preset **56.8 / 53.6 V** = Discover bulk / float (no reprogramming; never the 58.4 V LiFePO4 preset).
  11.3 A CC → **20 → 90 % in 4.9 h** (NPB-1700: 1.9 h). Acceptable for single-shift use with overnight charging (≤ 8 h).
  The NPB-1700-48 stays an option only for the C48 barista configuration (911 W average > 460 W net charge power of the
  NPB-750) and then needs a dock EMC test (TP-19b).
- **Dock OV relay XD3 at 59 V** (rev B3: DUB01CD48500V bench-set 58.5 V, §B3.2) in series with the dock contactor coil (RoboPad: ≤ 60 V even under fault; NPB OVP 82–100 V).
- **RoboPad = RPCOL90-100** (no "C" wireless-CAN part exists; fully passive): 60 A continuous (75 A only 80 s on / 60 s off),
  ±5 mm, 60 V max. The dock handshake (docked, BMS charge enable, SoC) runs over the robot ↔ dock **Wi-Fi/Ethernet** link
  (Jetson ↔ dock controller); CAN-E now carries only the BMS gateway. **H06a ≤ 2 m.** U8 DRDN40-48 uses a single input.
  Collector at the rear right (CAD stream).

### B2.8 Field devices, order codes and data corrections (EA1, FI1, P7, P16, S6, S9, SI1–SI5, AL1–AL3)
| Item | rev B1 | rev B2 |
|---|---|---|
| E-stops ES1–ES3 | Eaton M22-K02 (datasheet not retrievable) | **Siemens 3SU1 E-stop + 2 × 3SU1400-1AA10-1CA0** (positive opening documented) |
| PSEN cs3.1 × 2 | in series | **separate input pairs** (SC0 I18/I19, SR1 I0/I1) |
| K4 coil (92 mA) | on a 75 mA PNOZ output | **KI4 Phoenix PLC-RSC-24DC/21 interposing relay** (6.2 mm, right upper rail) |
| K0 | SW80B-24V | **SW80B…A**, continuously rated 24 V DC coil, aux A, blowouts B |
| Q0 | ED250B | **ED250B-L** (lockable); switch only with K0 open |
| F0 | 3NA3830 "NH00" | **3NA3830 NH000** 100 A gG link in an NH00 base, 250 V DC, 25 kA DC |
| System plug | NANSX-AAACZZZZ1 ASSUMED | **NANSX-AAACZZZZ1 (2105107)** SOURCED |
| Scanner power | 3.9 W | **15.9 W at maximum output load** (S24 budget 1.33 A for two) |
| K1/K2 DC-1 | 20 A ASSUMED, "thin" | **35 A** with 2 poles in series at 60 V (SOURCED) vs 19.6 A worst break |
| Scanner price | €2,394.95 | **€2,394.95 excl. VAT (verified)** |
| Prospective Isc | 5 kA ASSUMED | unpublished → every B48 device ≥ 20 kA DC (F0 25 kA) |

### B2.9 Cost (package, `CHECKS_AMR.md` → BOM)
| Variant | rev B1 | rev B2 | Δ | Main items |
|---|---|---|---|---|
| OA | €19,751 | **€20,381** | +€630 | 2 × EF 4DI4DOR +€759, −EF 8DI4DO −€322, K0V +€90, XD3 +€90, D0 +€40, RB +€28, KI4 +€20, E-stops +€65, NPB-750 −€140 |
| C48 | €19,168 | **€19,799** | +€631 | same |

### B2.10 What is left (no supplier question)
The 12 RESIDUAL items of VERIFICATION are type tests or price items: SWD brake torque / cat-0 distance (TP-03a/b), SWD
reaction time (TP-01), regen without a documented chopper (TP-03/TP-14), peak-torque duration (traction performance),
battery short-circuit current (bounded by ≥ 20 kA devices), vibration (hold-downs + bump test), BMS PL (no credit, layers),
PNOZ timer element (free Configurator), prices, Kassow DC power and OpenArm data (outside the base). §14 below is closed.

## 0. What changed from rev A

- **Waist removed.** Gone: ACTILINK-JP25 (+F5, W07, W23), DFS60S safety encoder (W24), FX3-MOC1, the SL1/SL2 overtravel
  switches (W25), the twisterband torsion cables (igus CFROBOT) and the waist safety functions (rev A SF9/SF10).
- **Centre bay.** The Jetson (E51), the arm DC-DCs UAL/UAR (E50) and the arm ORing + DSR (E52) are fixed parts of the base.
  The rest of the old waist-plate electronics goes onto two new short DIN rails on the spine inner faces (U7 coffee DC-DC,
  K4, FCF, FAL/FAR, U6, JR1, XC terminals). WF1–3 and U5 (Jetson 12 V) move to the right upper rail, which has room
  now that the Flexi station is gone. All cables that crossed the joint become short H07Z-K / OLFLEX runs.
- **Safety controller re-optimised.** SICK Flexi Soft (CPU1 + GENT + 5 XTIO + MOC1) is replaced by **Pilz PNOZmulti 2:
  PNOZ m B0 + 1 × EF 8DI4DO + ES ETH (€1,375, SECONDARY)**. The cut was made possible by removing I/O: SDI replaced by a
  permanent SLSa in the drives, 3 field sets on 1-of-3 inputs, K1+K2 on one output, K0 sequence hard-wired, dock
  signature and coffee on standard outputs, E-stops and arm-park sensors in series. See §6.
- **Scanners kept** (2 × nanoScan3 Pro I/O). Price is now SECONDARY: €2,394.95 each new at vb-steuerungstechnik.de, plus a
  €265.73 system plug.
- **Cost: €24.6k → €19.8k (OA), €24.0k → €19.2k (C48)**, −19.6 %. See §12.
- Fuses renamed: the arm feeds are F5L/F5R (rev A F6L/F6R), and F5 ACTILINK is gone.

## 1. Architecture in one paragraph

Two Discover DLP-GC2-48V packs in parallel form **B48 (40–58.4 V)**. H01/H02 (25 mm²) meet at the main fuse **F0 100 A gG
NH00**, then the key-lockable **Albright ED250B** (Q0) gives **B48_RAW**. B48_RAW is live whenever the key is ON and feeds
only the always-on circuits:
- **S24** (DDR-240C-24 → PNOZ, scanners, coils);
- **AUX48** (F2 → right-bay fuses WF1–3 → U5 12 V Jetson, U6 5 V head, U7 24 V coffee).

The functional main contactor **Albright SW80B** (K0, with precharge K0P) gives **B48_SW** for the motion loads. K0 is
switched by a hard-wired chain (S24 → BMS alarm NC → 0.6 s on-delay timer K0T), not by the safety controller. B48_SW feeds:
- two **DDR-480C-24** in current-sharing parallel → **DRDN40-24** ORing → **T24** for the two ez-Wheel SWD 125, with two
  **maxon DSR 50/5** 27 V clamps for regen;
- the **two arm feeds** through the safety contactors **K1+K2** into the centre bay.

The dock path enters at B48_RAW through a **DRDN40-48 ideal diode** and F7, so the RoboPad pads are never back-fed.
Everything is PELV (≤ 58.4 V), with one 0 V–chassis bond at E19.

Safety: **Pilz PNOZ m B0 + EF 8DI4DO + ES ETH** with 2 × nanoScan3 Pro I/O, 3 E-stops, and hard-wired STO + SLS into the
SWDs (SMS and the reverse limit SLSa are permanent inside each SWD). K1/K2 with EDM handle the arms.

## 2. Voltage domains

| Bus | Voltage | Source | Switched by | Loads |
|---|---|---|---|---|
| B48_RAW | 40–58.4 V | packs → F0 → Q0 | key (Q0), BMS FETs | U4 (S24), AUX48, charge input, K0 line |
| B48_SW | same | K0 SW80B (precharged) | K0: key + BMS alarm NC + K0T (hard-wired) | U1/U2, arm feeds |
| T24 | 24 V (clamp 27 V) | U1‖U2 → U3 ORing | SWD STO (not the supply) | 2 × SWD 125 |
| S24 | 24 V | U4 DDR-240C-24 | always on | PNOZ, scanners, coils, switch, gateways, fans |
| AUX48 | 40–58.4 V | F2 → WF1/2/3 (right bay) | always on | U5 12 V (Jetson), U6 5 V (head), U7 24 V coffee |
| A48L/R | 40–58.4 V | F5L/F5R → K1 → K2 → centre bay | **PNOZ (safety)** | OA: arm DDR-480C-24 each; C48: arm DC boxes |
| A24L/R (OA) | 24 V (clamp 27 V) | DDR-480C-24 → DRDN40-24 → DSR 50/5 | via A48 | OpenArm L/R through E53 |
| C12 | 12 V | U5 → FJ 8 A | always on | Jetson + cameras (centre bay) |
| COF24 | 24 V | U7 → K4 → FCF | PNOZ standard output (functional) | 24 V capsule machine |

## 3. Power budget and protection (details in `CHECKS_AMR.md`)

- **Pack current, OA**: 1 763 W max sustained = 44 A at 40 V (limit 116 A). All peaks at once: 2 944 W = 74 A (limit
  180 A for 3 s, and below the 116 A continuous rating, so the 5 s DC-DC peaks are covered). One pack alone carries it
  (58 A / 90 A). C48: 32 A / 50 A. Rev A was 48 A / 89 A; the ACTILINK is gone.
- **F0 100 A gG** (NH00, DC rating 250 V / ≥ 25 kA **ASSUMED**: confirm on the Siemens DC table). 25 mm² H07Z-K.
- **Branch fuses**: 10×38 gPV 1000 V DC. F1 6 A (S24) and F2 16 A (AUX48) sit on B48_RAW; F3/F4 20 A (U1/U2) and F5L/F5R
  16 A (arms) sit on B48_SW. F5L/F5R could now be 20 A (no twisterband derating), but 16 A is kept: it already holds the
  19.6 A / 5 s DC-DC peak.
- **New in rev B**: W28 carries 12 V from U5 (right bay) to the Jetson (centre bay) through FJ 8 A gG. The carrier power
  connector is ASSUMED to be 8 A.
- **Ampacity basis**: IEC 60204-1 Table 6 / IEC 60364-5-52 values (recalled, ASSUMED), 45 °C bay air, grouping 0.8. There is
  no torsion section any more.
- **DC-DC margins**: T24 18 A / 36 A shared (30 A peak / 54 A), N+1. S24 3.5 A / 10 A. OpenArm buses are exactly at the
  limit (15 A / 20 A continuous, **30 A / 30 A peak**): the Damiao current limits **must** cap each arm at 720 W.
  C12 4.8 A / 10 A; COF24 12.8 A / 20 A.

## 4. Traction T24 and regen (unchanged from rev A)

- ez-Wheel SWD supply (SOURCED, manual v2.0.2): M12-L, OV alert 32 V / error 34 V → STO, OC alert 25 A / error 30 A.
  Phoenix SAC-5P-M12MSL/1,5-280 FE SH; F8 20 A gG per wheel.
- The two DDR-480C-24 share current behind one DRDN40-24. Their remote ON now comes from the **K0 aux NO** contact, so the
  converters start only after precharge without a controller output.
- Regen: the DDR cannot sink current and its OVP latches. Two DSR 50/5 at 27 V clamp T24 (208 W peak, 83 J per stop,
  2.8 W average → PASS). **Do not trim the DDR output above 26 V.**

## 5. Battery, BMS, main switching

- Discover DLP-GC2-48V (SOURCED): 58 A / 90 A 3 s, 29 A charge, bulk 55.2–56.8 V, internal fuse, LYNK J1939. Parallel
  count and lying mount are not specified (§14).
- BMS data path: LYNK (W20) → LYNK II gateway G01 → CAN-E → PCAN-Ethernet → Jetson.
- **K0 sequence, hard-wired (new):** key ON → S24 up → G01 alarm relay NC (closed = OK) energises K0P and K0T → after 0.6 s
  K0T energises K0 → K0 aux NO → U1/U2 remote ON. K0P stays closed in parallel (bypassed). A BMS alarm opens K0P and K0
  together.
- K0 is a functional contactor, not a safety contactor. Q0 **must be the ED250B (blowouts)**.
- Precharge 47 Ω × 2 000 µF (ASSUMED, measure): 5τ = 0.47 s < 0.6 s, 3.4 J.

## 6. Safety controller: re-optimisation and choice

**I/O after reduction (OA, non-spare):** 24 inputs (20 safety-relevant + 4 functional), **8 safe outputs**, 2 standard
outputs, 2 test pulse lines. Rev A needed 37 inputs / 20 outputs.

| Reduction | Saves | Basis |
|---|---|---|
| SDI pair → **permanent SLSa** in each SWD (reverse ≤ 0.3 m/s, forward ≤ 1.1 m/s) | 2 safe outputs | SWD manual: SLSa[1..8] commands + "permanent activation" (2624h) SOURCED; asymmetric per-drive mapping ASK ez-Wheel |
| 4 field sets / 2 complementary pairs → **3 field sets, 1-of-3**; ARM-WORK merged into SLOW with the arm field on OSSD2 | 1 safe output (costs 4 inputs) | nanoScan3: 2 OSSD pairs, ≤ 8 simultaneous fields (SOURCED); 1-of-n evaluation ASK SICK |
| K1 + K2 on one SC output + feedback loop | 1 safe output | Pilz: PL e with one SC output + 2 contactors + EDM [ASSUMED] |
| K0 permit + precharge → hard-wired G01 / K0T chain | 2 outputs, 1 input | K0 is functional |
| Dock signature (RLY3) and coffee K4 → PNOZ **standard** outputs | 2 safe outputs + €167 | SF10 is carried by the station chain; SF15 PLr b (Cat B) |
| ES1+ES2 in series; PSEN cs3.1 ×2 in series | 4 inputs | ISO/TR 24119; Pilz PSEN cs series connection [ASSUMED] |
| DC-OK, signal tower, arm DC-DC remote → Jetson / nothing | 2 inputs, 2 outputs | non-safety signals |
| Waist: MOC1 + encoder + SL1/SL2 + ACTILINK STO | 1 module, 6 inputs, 2 outputs | no waist |

Owner's suggestion, to let the SWD safe-limit logic drive the field-set switching: the field-select outputs are kept
**separate** from the SLS outputs. Wiring the scanner inputs to the SLS outputs would shrink the field at the instant the
limit is requested, up to 0.8 s before the drive has slowed down, which would be a hole in SF3. They are driven by the same
PNOZ function block, so the sequence comes from the SWD limit logic. The SWD has no safe outputs (manual: status only via
CANopen), so the drive cannot drive the scanner directly.

**Options for this I/O** (net prices, eibabo.de 2026-10-05, SECONDARY; checked in `CHECKS_AMR.md → Safety ctrl options`):

| Option | Modules | in / safe out / std out | Price € | Fits |
|---|---|---|---|---|
| **P1 Pilz PNOZmulti 2** | **PNOZ m B0 784.12 + EF 8DI4DO 321.86 + ES ETH 268.89** | 28 / 8 / 2 | **1,374.87** (+ terminals ~90 ASSUMED) | **yes — chosen** |
| P2 Pilz PNOZmulti 2 | PNOZ m B1 (2 × Ethernet, no local I/O) 601.35 + 3 × EF 8DI4DO | 24 / 12 / 0 | 1,566.93 | yes |
| F1 SICK Flexi Soft, fewest modules | FX3-CPU0 293.93 + MPL 62.22 + 3 × XTIO 453.39 + FX0-GENT 617.71 | 24 / 12 / 0 | 2,334.03 | yes |
| F2 SICK Flexi Compact | FLX3-CPUC200 1,149.76 (Modbus TCP built in, 8 test outputs usable as non-safe, SOURCED) + XTDI100 344.89 + XTDO100 529.46 | 28 / 12* / 6 | 2,024.11 | yes (*XTDI/XTDO counts ASSUMED) |
| F3 SICK Flexi Compact, minimum | FLX3-CPUC200 + 1 × FLX3-XTDS100 (mixed I/O; price not listed, ASSUMED = XTDO100) | 28* / 8* / 6 | ~1,679 (ASSUMED) | probably (*ASK SICK) |
| rev A Flexi Soft (reference) | CPU1 + MPL + GENT + 5 XTIO + MOC1 (MOC1 ASSUMED 750) | 40 / 20 / 0 | 4,114.57 | – |

Why Pilz B0 wins: it is the only option with 20 inputs **and** 4 safe outputs **and** 4 configurable outputs (2 test
pulses + 2 standard) in a single 45 mm base unit, so one expansion covers the rest. The Flexi Soft CPU has no I/O at all.
The Flexi Compact CPUC200 is the strongest SICK option: it has Modbus TCP built in (no gateway), free software and its
terminals are supplied. But it costs €1,150 on its own, so even its best case (F3, ~€1,679 ASSUMED) is about €215 per
robot above P1 + terminals (€1,465).

Extra one-off costs and points to check:
- the **PNOZmulti Configurator licence** (one-off, not per robot; price ASK Pilz). The SICK Safety Designer is free. Above
  a few robots, P1 stays cheaper even with a licence of several hundred euro.
- PFHd values for B0/EF (ASSUMED 2.0e-9 / 1.5e-9 here).
- the "one output, two contactors" PL e statement.

If any of these fail, the fallback is **P1 + 1 EF 8DI4DO (+€322)**, which still costs €1,697, below every SICK option.
With the C48 variant the second EF is fitted anyway (arm safety I/O).

## 7. Scanners

2 × SICK **NANS3-CAAZ30AN1** nanoScan3 Pro I/O are kept (owner).

| Source | Price € (net) | Tag | Note |
|---|---|---|---|
| vb-steuerungstechnik.de (A10197) | **2,394.95** | SECONDARY | "NEU in Originalverpackung", 3 in stock, 1 working day; surplus dealer → dealer warranty, check date code + firmware |
| eibabo.de (SICK list-based) | 3,719.21 | SECONDARY | – |
| rev A estimate | 2,420 | ASSUMED | incl. plug |
| System plug NANSX-AAACZZZZ1 (eibabo) | 265.73 each | SECONDARY | Pro I/O plug assignment ASSUMED: confirm the part number with SICK |

The package uses the vb price. For series production, ask SICK direct for an OEM price. At list price the package is
+€2.6k (OA €22.4k).

## 8. Arms

**OA:** K1/K2 (Siemens 3RT2026, mirror contacts, 2 poles in series per arm) switch the 48 V feeds into the centre bay:
UAL/UAR DDR-480C-24 (E50, lying on P10: **ask Mean Well about derating for horizontal mounting**) → DRDN40-24 → DSR 50/5 →
FAL/FAR 25 A → 6 mm² through E53 to the arm column (XT60).
- Normal stop: the Jetson disables the Damiao drives, then K1/K2 open at 0.5 s with < 1 A to break.
- Worst-case break (Jetson failed): 19.6 A per arm, against an ASSUMED DC-1 rating of 20 A with 2 poles in series at
  60 V. **Thin, verify** (fallback: Schaltbau C195-class DC contactor).
- The arm DC-DC remote OFF of rev A is dropped (it needed a controller output).

**C48:** remove UAL/UAR, ORing and DSR. A48L/R go through E53 to the arm DC boxes. Add K3 precharge (centre bay left inner
rail, in the FAL/FAR slot) and SX2 (second EF 8DI4DO) for the arm safety I/O. Kassow Edge needs a 44 V low-voltage
cut-off.

## 9. Centre bay and deck interface

- The Jetson (E51) gets 12 V from U5 + FJ (right bay, W28) and Ethernet from NET1 (H10b). The CAN buses stay on the PCAN
  gateway (CAN1); with the Jetson now in the base, a native/USB CAN interface could replace it (cost-down, §12).
- Two new DIN rails on the spine inner faces (z 276, x −76…+53): U7, K4, FCF on the right; FAL/FAR, U6, JR1, XC on the
  left (din_layout §5).
- **E53 deck grommet** carries about 10 cables: arm 24 V × 2 (XT60 pre-terminated), coffee 24 V, ES3, PSEN × 2 (M12), HL1,
  head 5 V, plus the Jetson USB/camera cables (superstructure scope). Use a split frame (icotek KEL-DPZ class) so that
  pre-terminated cables pass through.
- Air: the new front intake fan + the existing rear exhaust fans sweep the corridor above the batteries through the centre
  bay (52 W → 45 °C with fans, 94 °C passive).

## 10. Dock and charging (unchanged except the signature relay)

RoboPad **RPCOL90C-100** → H06a 10 mm² → DRDN40-48 → F7 32 A → H06b → B48_RAW. The station is an NPB-1700-48 (25 A CC,
IEC 60335-2-29), **reprogrammed to 56.8 V bulk / 53.6 V float** (ACTION), with a DC contactor with blowouts. The signature
resistor is now switched by the **KS interface relay on a PNOZ standard output**. The PNOZ energises it only when the Hall
sensor says docked, traction is in STO, and the Jetson requests charging. SF10 is carried by the station chain (Hall +
signature + CAN handshake + current monitor).

## 11. Grounding, EMC (unchanged)

- 0 V is bonded to the chassis at **E19 only**. The T24 0 V is bonded functionally, and S24 0 V reaches E19 via X0R/W13.
- DDR-480C conducted EMI is class A: twisted pairs, shield clamps at bay entries, a DC input filter budget for
  EN 61000-6-3. RED + EN 18031 apply for Wi-Fi (Jetson) and the RoboPad-C wireless CAN.
- Rev B removes the long torsion bundle (antenna risk) and moves the Jetson next to the DC-DCs: route its Ethernet/USB away
  from E50.

## 12. Cost: rev A vs rev B (package only, excl. arms, Jetson, head; € excl. VAT)

| Group | rev A1 OA | rev B1 OA | Δ | Note |
|---|---|---|---|---|
| Drives 2 × SWD 125 | 4,666 | 4,666 | 0 | SECONDARY |
| Scanners 2 × nanoScan3 Pro I/O (+ plugs) | 4,840 | 5,321 | +481 | rev A ASSUMED; rev B SECONDARY (vb + eibabo plug) |
| Safety controller (+ dock enable relay) | 4,240 | 1,480 | **−2,760** | Flexi Soft CPU1+GENT+5 XTIO+MOC1+RLY3 → PNOZ m B0+EF+ES ETH+terminals+KS |
| Waist chain (ACTILINK, safety encoder, limit switches) | 2,408 | 0 | **−2,408** | mechanics (RU124, twisterband) are outside this package |
| Battery 2 × DLP-GC2-48V + LYNK gateway | 2,210 | 2,210 | 0 | |
| Power, arm power, field devices, dock, cables | 6,189 | 6,073 | −116 | no CFROBOT, + K0T, WF/FJ, centre-bay fuses, fan |
| **Total OA** | **24,553** | **19,751** | **−4,802 (−19.6 %)** | |
| **Total C48** | **23,957** | **19,168** | **−4,789** | C48 adds SX2 + K3, drops arm DC-DCs |

Price quality, rev B OA: SECONDARY €13.8k, SOURCED €0.6k, ASSUMED €5.8k. Sensitivity: scanners at SICK list price
→ OA €22.4k.

Further cost-down candidates, not applied:
- drop CAN1 (€520) and use the Jetson's CAN controller + 2 transceivers (~€40, ASSUMED: check the CAN count on the Orin NX
  carrier);
- an unmanaged 5-port DIN switch instead of the FL SWITCH 1008N (~−€100);
- an SW80 economiser coil (−9 W heat);
- one DDR-480C-24 for traction (−€140, loses N+1).

## 13. CAD changes requested (the CAD stream owns amr_cad.py / amr_params.py)

> Rev B2: the current CAD request list is `din_layout.md` §0 (relay modules, E2F to the left rail, KI4, K0V, Mean Well
> clearances, G01 120 × 135 × 44, U6 52.5 mm). The rev B1 list below is kept for traceability; item 8 (lying E50) is void.

Module tuples as in `din_bays()`: (name, width, height, depth, x_start); rails as in the current CAD.

1. **Right upper rail (z 248)**
   - rename E20 → `E20_SC1_PNOZ_m_ES_ETH` (22.5 × 101.4 × 120, x −257);
   - **delete E24**; E21 → `E21_SC0_PNOZ_m_B0` **width 45** (45 × 101.4 × 120, x −234.5);
   - E22 → `E22_SX1_PNOZ_m_EF_8DI4DO` (22.5 × 101.4 × 120, x −189.5);
   - E28 → `E28_SX2_PNOZ_m_EF_8DI4DO_C48` (x −167, C48 only);
   - **delete E29, E2A, E23 (MOC1), E26 (RLY3)**;
   - **new** `E2F_WF1-3_AUX48_fuses` (52.5 × 82 × 70, x −142);
   - **new** `E2G_U5_DDR120C12_FJ` (51.5 × 125.2 × 102, x 195);
   - E25, E15, E27, E2C, E2D unchanged.
2. **Left upper rail:** E18 width **127.5 → 110** (x −83.5…26.5, 6 holders); **new** `E17_K0T_timer_Finder80` (17.5 × 90 × 70, x −238).
3. **Right lower rails:**
   - **new** `E37_KS_signature_relay` (6.2 × 90 × 70, x −114, rear segment);
   - **new** `E38_G01_LYNK_II_gateway` on the spine face of the front segment (~65 × 70 × 30, x 150…215, size ASSUMED).
4. **Centre bay:**
   - two new TS35 rails `E0C_R` / `E0C_L` on the spine **inner** faces (|y| 131 → 123.5), x −76…+53, **z 276**, plus tapped
     M5 rows in A03 for them;
   - right rail modules: `E54_U7_DDR480C24_coffee` (85.5 × 125.2 × 129.2, x −76), `E55_K4_Finder22` (17.5 × 90 × 70,
     x 11.5), `E56_FCF_fuse` (17.5 × 82 × 70, x 31);
   - left rail modules: `E57_FAL_FAR_fuses` (35 × 82 × 70, x −76), `E58_U6_DDR60L5` (40 × 125.2 × 100, x −39, width ASSUMED),
     `E59_JR1_relays` (12.4 × 90 × 80, x 3), `E5A_XC_deck_terminals` (30 × 60 × 50, x 17.4);
   - check: modules z 213.4…338.6 against E52 (x 55…77, z ≤ 230.5) and the H03/H10 harness envelopes.
5. **Fan:** new `E40_fan_Cin` 60 × 60 × 25 in the front cover on the centre line (x 363…388, y −30…30, z 255…315), with a
   cut-out + filter grille in K01.
6. **Harness routing:**
   - H03 = AUX48 left → right bay (under the deck, across the centre corridor) + right bay → centre bay (arm 48 V,
     coffee 48 V, head 48 V);
   - H10 = right bay → centre bay (control 18G0.5, Ethernet) → E53;
   - H06 dock harness → **right** bay lower rear (still open from rev A);
   - spine cut-outs with grommets between each side bay and the centre bay at z ~250.
7. **E53 grommet:** split cable-entry frame with ≥ 10 entries (2 × XT60 6 mm², M12 × 3, 4 × multi-core Ø 6–10 mm, USB).
8. **E50 note:** the DDR-480C-24 lie flat on P10; keep ≥ 15 mm above them for convection (shelf P11 at z 137.5 vs top
   125.5 → 12 mm: **raise P11 by ≥ 3 mm** or ask Mean Well).
9. Carried over from rev A, if not done yet: X05 dock controller = DC contactor with blowouts (not a Finder 62.32);
   rear panel SB1/SK1/SE1 (present as E41); torso ES3, HL1 and PSEN cs3.1 ×2 on the arm rests in the superstructure CAD.

## 14. Open questions for suppliers (rev B1) - CLOSED in rev B2

Every question below was answered from published documents in `../VERIFICATION.md` (or replaced by a documented part, §B2).
Kept for traceability only.

**Pilz (PNOZmulti 2)**
1. PFHd / PL for PNOZ m B0, EF 8DI4DO, ES ETH. Confirm **PL e with one SC output driving two contactors + feedback loop**,
   and the SC output current (2 × 3RT2026 coils, 0.5 A).
2. Can the B0 configurable outputs be split into 2 test pulses + 2 standard outputs, and can the base test pulses feed
   EF inputs?
3. Order of modules (ES left of B0) and the maximum number of EF modules on B0. Are the plug-in terminal sets included?
4. PNOZmulti Configurator licence price (one-off). Modbus TCP mapping on ES ETH for Jetson requests/status.
5. PSEN cs3.1: series connection of 2 units, PL e, cable lengths.

**SICK (nanoScan3 Pro I/O)**
1. **1-of-n static input evaluation** with 3 inputs (CI1–CI3) for 3 field sets; switching time. Do the **PNOZ SC output
   test pulses** need to be filtered on the control inputs?
2. Field set FS2 with 2 simultaneous fields (OSSD1 0.45 m ring + OSSD2 arm envelope); rotation-in-place coverage with 2
   diagonal scanners.
3. Correct system plug for NANS3-CAAZ30AN1 (NANSX-AAACZZZZ1?). OEM price for 2/robot in series.
4. Dock contour cut-out instead of muting: acceptable under IEC 61496-3 / ISO 3691-4?
5. Flexi Compact FLX3-XTDS100 / XTDI100 / XTDO100 channel counts and prices (benchmark against Pilz P1).

**vb-steuerungstechnik.de** (scanner offer A10197): warranty terms (dealer vs SICK), date code / firmware version,
availability of ≥ 2 units, CE documentation supplied.

**ez-Wheel (SWD 125)**
1. **SLSa as a permanent function** (forward 1.2 / reverse 0.3 m/s) with mirrored mounting. SBU mapped to INSafe_3/4 for
   SERVICE pushing.
2. STO / INSafe tolerance to PNOZ SC output test pulses (pulse width, period).
3. Regulated DC-DC supply without a battery on T24; regen energy and internal chopper; compatibility of a 27 V clamp.
4. PFHd / MTTFd / DC per safety function, and the SISTEMA library.

**Discover (DLP-GC2-48V)**
1. Lying mount, vibration rating; parallel operation of 2 packs.
2. Internal fuse rating, prospective short-circuit current.
3. **LYNK II alarm relay: contact type and rating** (it now switches the K0/K0P coil chain directly: ≥ 1.5 A at 24 V DC
   inductive, or add an interposing relay).
4. Functional-safety evidence of the BMS for SF12.

**Mean Well:** DDR-480C-24 derating when lying flat (E50); DDR remote ON/OFF wiring with a dry contact (K0 aux).
**Siemens:** 3RT2026 DC-1 rating with 2 poles in series at 60 V. **Synapticon / THK / igus:** no longer needed.
