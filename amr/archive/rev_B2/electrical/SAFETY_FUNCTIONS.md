# Safety functions: Giorgio own AMR (rev B2, 2026-10-05)

Rev B: **no waist yaw joint** (owner decision 2026-10-05). All waist functions of rev A (waist SLS, waist SLP, overtravel
switches, waist STO/SBC) are gone, and the list below is renumbered SF1–SF16. Safety controller rev B2: **Pilz PNOZmulti 2: PNOZ m B0 + 2 × PNOZ m EF 4DI4DOR
(positive-guided relay outputs) + PNOZ m ES ETH**; the C48 variant adds one EF 8DI4DO (SX2). Rev B2 applies the design
changes of `../VERIFICATION.md` (official documents in `../../docs/fonti/`); row IDs are quoted as [V:xx].

Scope: base (EN ISO 3691-4:2023), arms application (EN ISO 10218-2:2025), control system per EN ISO 13849-1:2023,
stop categories per EN 60204-1 §9.2.2, drives per EN IEC 61800-5-2. Variants: **OA** = OpenArm 2.0 R&D arms (no STO, no
brakes); **C48** = certified 48 V DC cobot arms. I/O channels are in `netlist_amr.yaml → safety_io`, the drawing is
`safety_diagram.png`, and the numbers are in `CHECKS_AMR.md → PL`.

**This is a pre-assessment, not the risk assessment.** The PLr values come from the ISO 13849-1 Annex A risk graph, with
the reasoning written next to each one. They must be confirmed in the EN ISO 12100 risk assessment. The achieved PL is an
estimate: PFHd summed per subsystem. SOURCED in rev B2: nanoScan3 8.0E-8, PNOZ m B0 (CPU 4.74E-10, inputs 7.95E-11, SC output
1.66E-11), EF 4DI4DOR (CPU 2.84E-10, relay outputs 2-channel 7.52E-12, 1-channel 3.75E-8), SWD STO 1.42E-9 and SLS/SLSa/SBC3
2.29E-7 (MTTFd 14 y). E-stop, contactor, key, enabling and PSEN values are still **ASSUMED** (from the manufacturer SISTEMA
libraries at release).
Method for release: SISTEMA with the Pilz, SICK, Siemens libraries and the published ez-Wheel PFHd (no ez-Wheel library needed, V:E5). Duty profile: E-stop 220/y,
K1/K2 6 600/y. DC is 99 % where PNOZ test pulses and EDM apply, and 60–90 % otherwise (E-stops in series). CCF score ≥ 65.

Risk graph (Annex A): S1 slight/reversible, S2 serious/irreversible; F1 seldom/short, F2 frequent/long; P1 possible, P2
scarcely possible. PL: S1F1P1 a, S1F1P2 b, S1F2P1 b, S1F2P2 c, S2F1P1 c, S2F1P2 d, S2F2P1 d, S2F2P2 e.

Common basis for S/F/P: the robot weighs ~165 kg with payload (conservative; rev B is lighter) and drives at up to 1.2 m/s
(SMS). It works in a public/service environment with people present the whole shift, so anything that happens during
normal operation is F2. Hot liquids travel in the tray. OpenArm payload is 3 kg per hand, with an arm envelope of ~0.9 m.

## What changed in rev B2 (from `../VERIFICATION.md`)

| rev B1 | rev B2 | Why [source] |
|---|---|---|
| SWD STO_1/2 and INSafe_1/2 on B0 safe semiconductor outputs (test pulses) | **SR1 EF 4DI4DOR positive-guided relay contacts**, 2.2 kΩ bleed each | the SWD input tolerance to test pulses is not published [V:E6]; relay DC1 min 10 mA [V:P14] |
| scanner CI1–CI3 on EF 8DI4DO SC outputs | **SR2 EF 4DI4DOR relay contacts**, bleed resistors; scanner input delay class "relays" | nanoScan3 pulse rejection not published [V:S4] |
| EF 8DI4DO (SX1) | **removed**: K1/K2 → SC0 O0; inputs → SR1/SR2 | I/O fits B0 + 2 relay modules (26/28 inputs) |
| STO at 0.5 s after the stop request | **SS1-t: SLS[1] requested at t = 0, STO at 1.2 s** (ramp always complete) | SWD has no safety-rated SS1, default SBC = phase short [V:E3/E4] |
| t_logic 10 ms ASSUMED | **54 ms SOURCED** (relay path), t_drive 20 → 40 ms (to measure) | [V:P8, V:E9] |
| PSEN cs3.1 × 2 in series | **separate input pairs** (SC0 I18/I19, SR1 I0/I1) | series connection undocumented [V:P16] |
| Eaton M22 E-stops | **Siemens 3SU1 with 3SU1400-1AA10-1CA0** (positive opening documented) | Eaton datasheet not retrievable [V:EA1] |
| K4 coil on a PNOZ standard output | **KI4 interposing relay** on the auxiliary output | 92 mA coil > 75 mA output [V:FI1, V:P7] |
| K0 chain: LYNK alarm **NC** = OK | **LYNK R1 NO "energised = OK" + K0V 48 V low-voltage cut-off + D0 diode** | NC is closed when de-energised: not fail-safe [V:D4]; LVD recommended 48 V [V:D10] |
| dock: NPB-1700 reprogrammed, wireless CAN | **NPB-750-48 (Class B) DIP "flooded", 59 V OV relay, handshake over Wi-Fi/Ethernet** | [V:M11–M13, V:R1, V:R5] |
| BMS "FETs" | BMS main **relay** | [V:D13] |

## What changed from rev A

| rev A | rev B | Why |
|---|---|---|
| SF9 waist SLS, SF10 waist SLP + SL1/SL2, waist STO/SBC in SF1/SF2 | removed | no waist joint |
| SF5 SDI "no reverse in FAST" (2 controller outputs → INSafe_3/4) | **SF5 reverse speed ≤ 0.3 m/s, permanent SLSa in each SWD** (no controller channel) | saves 2 safe outputs. Reversing is rare (differential drive turns on the spot; docking creeps at 0.1 m/s) |
| 4 field sets on 2 complementary pairs (4 outputs) | **3 field sets, 1-of-3 (3 outputs)**. ARM-WORK is merged into SLOW: OSSD2 carries the arm field | saves 1 output; costs 4 inputs, which are plentiful |
| K1, K2 on two outputs | K1 + K2 on **one** PNOZ safe semiconductor output with a feedback loop | Pilz: one SC output + 2 contactors + EDM = PL e [ASSUMED, verify in the B0 manual] |
| K0 permit + precharge on Flexi outputs | hard-wired: S24 → G01 BMS alarm NC → K0P + K0T on-delay → K0 | K0 is a functional contactor and does not need a safety controller channel |
| SR1 RLY3-OSSD100 for the dock signature | KS interface relay on a PNOZ **standard** output | SF10 is carried by the station chain; the robot-side relay is a functional measure |
| SF17 coffee stop PLr c on a safe output | **SF15 PLr b, K4 on a standard output (Cat B)** | see SF15. Fallback if the risk assessment keeps PLr c: add 1 EF 8DI4DO |
| 3 E-stops, 6 inputs | ES1+ES2 in series (2 inputs) + ES3 (2 inputs) | ISO/TR 24119: 2 rarely-operated devices in series → DC low, still Cat 3 / PL d |
| TR4 Direct ×2, 4 inputs | Pilz PSEN cs3.1 ×2 in series, 2 inputs | cheaper; series connection [ASSUMED, confirm with Pilz] |

Safe I/O: rev A (OA) used 37 inputs / 20 outputs on CPU1 + 5 XTIO + MOC1. Rev B1 used 24 inputs, 8 safe outputs and
2 standard outputs on B0 + 1 EF. Rev B2 uses 26 inputs, 1 safe SC output + 7 safe relay outputs and 2 auxiliary outputs on
B0 + 2 EF 4DI4DOR (spare: 2 inputs, 3 SC outputs, 1 relay output).

## Stop categories

| Initiator | Traction (SWD) | Arms OA | Arms C48 | Coffee |
|---|---|---|---|---|
| E-stop (SF1) | SS1-t: t = 0 SLS[1] request (SR1 O2/O3) + SWD quick-stop ramp 1.5 m/s² (non-safe); STO + SBC at t = 1.2 s (PNOZ timer, SR1 O0/O1) | Jetson disables the Damiao drives, then K1/K2 open at 0.5 s (**cat 1 in timing, but the arm drops onto its rests: no brakes**) | arm E-stop input → the arm's own cat 1 with brakes; K1/K2 open at 1.0 s | KI4 → K4 off (auxiliary output) |
| Protective stop, OSSD1 (SF2) | as for E-stop; automatic restart in AUTO once the field is clear (reset only after an E-stop) | as for E-stop | arm safeguard-stop input (SS2, power kept) | not affected |
| Arm field, OSSD2 (SF7) | already in STO (arms work only at standstill) | K1/K2 SS1-t | arm protective stop / reduced mode | not affected |

### SS1-t timing (rev B2 decision)

Two options were open [V:E4]: (A) STO delay ≥ 1.1 s so the ramp always ends before STO, or (B) keep 0.5 s and size the
fields for STO arriving mid-ramp. **Chosen: A, with t_STO = 1.2 s.**

| Item | Value | Source |
|---|---|---|
| ramp (SWD quick-stop 604Ah, non-safe) | 1.5 m/s² | design; SWD has no safety-rated SS1 |
| latency to ramp start | t_logic 54 ms + t_drive 40 ms = 94 ms | Pilz catalogue p.26–28; t_drive ASSUMED (measure TP-01) |
| ramp end from 1.5 m/s (design envelope) / 1.2 m/s (SMS) | 1.094 s / 0.894 s | CALC §7 |
| SLS[1] 0.3 m/s requested at t = 0, t_SLS (6691h) | 1.0 s, violation → STO by the SWD (PL d) | SWD manual p.109–110 |
| PNOZ STO_1/STO_2 off | **t = 1.2 s** (PL e) | design |

Why A: with B the tail of every stop above 0.75 m/s is a cat-0 phase-short stop whose decel is not published, so the field
could not be computed without a test, and the cat-0 tip margin is lower (CALC §2b, SF 1.23). With A the field is sized on
the ramp (CALC §7: 251 / 535 / 894 / 1240 mm at 0.3 / 0.8 / 1.2 / 1.5 m/s) and STO always arrives at standstill. Cost of A:
if the non-safe ramp fails, the robot is stopped by the SWD SLS monitoring at 1.0 s (or the PNOZ STO at 1.2 s) and then
brakes in cat 0; this single fault of a non-safety part is not covered by the field (SS1-t per IEC 61800-5-2 does not
monitor the ramp). It is listed as a residual risk (H03 in `../ce/risk_assessment.csv`) and measured in TP-01b (ramp disabled).
The arm contactors K1/K2 keep their own 0.5 s timer. Cat-0 stopping distance and 6 % slope holding are type tests (TP-03a/b).

## Safety functions

### SF1 Emergency stop (ES1+ES2 base in series, ES3 torso)
- **PLr d**. S2 (165 kg robot, arm strike); F1 (complementary measure, used seldom); P2 (a person reaching for the E-stop
  is already in the hazard) → d. ISO 13850 requires ≥ PL c; ISO 3691-4 expects PL d for the E-stop of the base [recalled].
- Architecture: Cat 3 inputs (2 NC, test pulses T0/T1). ES1 and ES2 are in series (ISO/TR 24119: fault masking → DC low).
  ES3 sits on its own pair at the deck interface XC. E-stops: Siemens 3SU1 with 2 × 3SU1400-1AA10-1CA0 NC (positive
  opening "Yes", SOURCED). → PNOZ m B0 (PL e) → SR1 relay contacts (2-channel PL e) → SWD STO_1/STO_2 (PL e, Cat 4) via
  SS1-t, K1+K2 on SC0 O0 with mirror-contact EDM (Cat 3; coil wires in separate multicore cables, Pilz B0 manual p.29), and
  KI4/K4 (functional).
- Devices: ES1/ES2/ES3, SC0 I0–I3, SR1 O0–O3, SC0 O0, M1L/M1R, K1, K2.
- Estimate: 2.7–6.0e-8 /h → **PL d (PL e numerically)**. A manual reset with SB1 is required (SF13).
- OA: the arms **fall** when power goes. The residual risk is handled by parking on the rests first when there is time,
  and by gravity-spring compensation [design needed].

### SF2 Protective stop on person detection (2 × nanoScan3 Pro I/O, OSSD1)
- **PLr d**. S2, F2 (people walk near the robot all shift), P1 (warning field + signal tower, speed limited per field set)
  → d. Matches ISO 3691-4 personnel detection [recalled].
- Architecture: Type 3 scanner (PL d, Cat 3) → PNOZ → SR1 relays → SWD SLS + STO/SBC (SS1-t, 1.2 s), arm stop.
- Field lengths: CALC §7 (rev B2, t_logic 54 ms, t_drive 40 ms). Reflector supplement ZR = 350 mm applies if a
  retroreflector is within 6 m of the scan plane (SICK OI p.27): keep the dock reflector at z 380–500.
- Estimate: 8.2e-8 → **PL d**. The scanner caps the chain at PL d. If the risk assessment ends at P2 → PLr e → not
  achievable with any Type 3 scanner.

### SF3 Speed-dependent protective field switching
- **PLr d**. Failure means a small field at high speed: S2 F2 P1.
- Concept: no safe speed signal reaches the safety controller. The SWD has no encoder or safe outputs (status only over
  CANopen), and the nanoScan3 Pro I/O has no encoder inputs. So the field size is bound to a **commanded, drive-monitored
  speed limit**: FS1 FAST only with SLS released (SMS 1.2 m/s cap); FS2 SLOW and FS3 DOCK only with SLS[1] = 0.3 m/s active.
- Switching rule: towards a smaller field, the PNOZ first drops INSafe_1/2 (SLS request), waits t = 1.1 s (SWD t_SLS
  6691h = 1.0 s, SOURCED p.109), then changes the field code. Towards a larger field, the field changes first, then SLS is
  released. If the robot is still faster than SLS after the delay, the SWD triggers STO itself.
- Why not let the SLS outputs select the field directly (cheaper): the field would shrink at the same instant the
  limit is requested, before the drive has slowed down. The field-select outputs and the SLS outputs are therefore
  separate. They come from **one** function block in the PNOZ, so field switching is still driven by the SWD safe-limit
  logic.
- Devices: SR1 O2/O3 → SWD INSafe_1/2 (both drives); SR2 O0–O2 (relay contacts, 2.2 kΩ bleed) → static control inputs
  CI1–CI3 of both scanners, 1-of-3 evaluation (SOURCED, SICK OI p.44), input delay class "relays".
- Single-channel relay contacts (PL c Cat 1 each, PFH 3.75E-8): a welded contact gives two inputs high, an open contact
  gives none; both are invalid codes → OSSDs off. A wrong **valid** code needs two independent faults → Cat 3 argument;
  confirm in SISTEMA.
- Estimate: 3.5e-7 → **PL d**.

### SF4 Safe limited speed per mode
- **PLr d** (S2 F2 P1). AUTO-FAST: SMS 1.2 m/s, permanently configured in each SWD. AUTO-SLOW, DOCK, MANUAL and arms not
  parked: SLS 0.3 m/s. SERVICE: STO.
- Devices: SWD SMS/SLS (PL d, Cat 3, PFHd 2.29E-7 SOURCED), SR1 O2/O3. Estimate 2.3e-7 → **PL d**.
- SLS acts per wheel. In-place rotation at 0.3 m/s wheel speed gives a 1.29 rad/s body rate and a 0.62 m/s corner speed,
  so rotation is allowed only in FS2.

### SF5 Safe limited reverse speed (replaces the rev A SDI)
- **PLr d** (S2 F2 P1). In FS1 the rear protective field is short (0.35 m), so fast reversing must be impossible.
- Means: **SLSa permanently active in each SWD** (manual: SLSa[1..8] commands and "permanent activation", object 2624h):
  forward ≤ 1.2 m/s, reverse ≤ 0.3 m/s, with the sign mirrored on the left and right drives. The 0.35 m rear field
  covers the 0.3 m/s stopping distance (232 mm field at 0.3 m/s, CALC). No controller channel is needed, and INSafe_3/4
  become spare (candidate: SBU for pushing in SERVICE).
- Estimate 2.3e-7 → **PL d**. Closed from the manual [V:E7]: any safety function can be made permanent (2624h/2625h);
  SLSa has separate positive/negative limits (3052h/3055h); polarity 607Eh does not change the safety sign, so each wheel
  gets its own parameter set (left: forward = negative), documented with its signature 3058h. SLSa is guaranteed from
  100 rpm motor (0.3 m/s ≈ 167 rpm).

### SF6 Safe standstill of the base while the arms work
- **PLr d** (unexpected base motion next to a person at the working arms: S2 F2 P1).
- The PNOZ closes K1/K2 only while the SWD STO contacts (SR1 O0/O1) are open (traction STO, PL e) and SBC holds (PL d).
  Note: the default SBC is the internal phase-short brake, held ~3 min after power loss [V:E3]; standstill on a slope
  relies on the parking brake of the EW2A-125HN04B, whose torque is a type test (TP-03b, 6 %: 0.76 Nm per motor needed).
  Arm work happens only in FS2.
- Estimate 2.3e-7 → **PL d**.

### SF7 Arms move only with the arm field clear (OA) / protective stop of certified arms (C48)
- **PLr d**: S2 (3 kg payload, hot cup, pinch), F2, P1 only if arm speed is low (≤ 250 mm/s Cartesian). **For OpenArm that
  limit is firmware only. If the assessment does not accept P1, PLr = e → impossible with Type 3 scanners → OpenArm cannot
  be certified near people.**
- OA chain: nanoScan3 OSSD2 (FS2 contains a second simultaneous field: arm envelope + S = K·T + C) → PNOZ (SC0 I13–I16,
  evaluated only while K1/K2 are closed) → SC0 O0 → K1/K2 SS1-t (Cat 3, mirror EDM). The Jetson re-enables the arms after the
  field has been clear for 2 s.
- C48 chain: OSSD2 → SX2 O2/O3 → arm safeguard-stop inputs. The arm's own PL d functions do the rest.
- Estimate 9.3e-8 → **PL d** (limited by the scanner).

### SF8 Carry mode (FAST travel only with the arms parked and de-energised)
- **PLr d** (unexpected arm motion while driving fast past people: S2 F2 P1).
- OA: FS1 is allowed only if both PSEN cs3.1 (each on its own input pair: SP1 SC0 I18/I19, SP2 SR1 I0/I1, PL e) report "arm on rest" **and** K1/K2 are open
  (EDM confirmed). Objects travel in the tray, never in the hands.
- C48: arms parked + arm safety output "robot stopped" (SX2 I0–I3). Arm power may stay on.
- Estimate 6.5e-8 → **PL d**.

### SF9 Docking field (reduced rear field, no muting)
- **PLr c**: S2 (pinch between robot and dock frame), F1, P1 (creep speed, visible) → c.
- FS3 uses a static rear cut-out shaped like the dock contour (120 mm deep). It is allowed only with SLS 0.3 m/s active
  (navigation creeps at 0.1 m/s), and the arms are off. Selecting FS3 is a non-safe request (Jetson via Modbus TCP +
  RoboPad Hall + AprilTag), and the request can only shrink the rear field where the dock stands. There is no muting.
- Estimate 1.3e-7 → **PL d** ≥ c.

### SF10 Charging contacts dead unless docked
- **PLr c**: the pads sit at 57.6 V DC (below the 60 V PELV dry limit, so no shock hazard), but a metal object across the
  25 A pads can cause a burn or fire: S2 F1 P1 → c.
- Robot side (inherent): the DRDN40-48 ideal diode means the pack never back-feeds the pads.
- Station side (carries the PL): the output contactor closes only with Hall docked AND the 10 kΩ signature seen AND the
  handshake over the robot ↔ dock **Wi-Fi/Ethernet** link (Jetson ↔ dock controller: docked, BMS charge enable). RoboPad
  has no wireless CAN (passive part, datasheet v1.3) [V:R5]. It opens within 100 ms on current collapse.
- **Rev B2: over-voltage relay XD3 at 59 V** in series with the dock contactor coil. RoboPad requires ≤ 60 V even under fault
  conditions, while the charger OVP trips only at 82–100 V [V:M12]. Charger NPB-750-48 with the DIP "flooded" preset
  56.8 / 53.6 V (no reprogramming) [V:M11/M13].
- Robot-side signature: KS relay on a PNOZ auxiliary output, energised only when docked + traction STO + Jetson request
  (functional, diverse to the station chain). H06a ≤ 2 m (RoboPad).
- Estimate 1.0e-6 → **PL c** (station chain, single channel + current monitor, ASSUMED). The station is part of the
  machine for CE.

### SF11 No traction while charging is permitted
- **PLr c** (the robot drives off with energised pads or drags the dock). While KS is energised, the PNOZ holds SWD STO
  (safe outputs). Undocking: the Jetson requests it, KS drops, and the station sees the signature disappear and opens.
- Estimate 1.2e-8 → **PL e** ≥ c.

### SF12 Battery protection
- **PLr d** (thermal runaway/fire: S2 F1 P2 → d).
- Means: the Discover BMS (IEC 62619 CB certificate, UL 2271, internal 60 A fuse, **main relay**; over-voltage > 58.24 V
  3.2 s, over-discharge > 58 A 10 s, under-voltage < 40 V 5.2 s, cell over-temperature 62 °C) is the primary protection.
  Independent layers, no PL credit taken [V:D13]: F0 3NA3830 100 A gG (25 kA DC); K0 opened by the LYNK II relay R1
  **NO programmed "energised = OK"** (fail-safe: alarm, gateway power loss and wire break all open K0) [V:D4]; **K0V 48 V
  application low-voltage cut-off** [V:D10]; charger CV by DIP preset 56.8 V; dock OV relay 59 V.
- No PL is computed (no published BMS PL/PFHd). Argued in the technical file as a product-standard function (IEC 62619)
  plus the layers above.

### SF13 Manual reset (no automatic restart after an E-stop)
- **PLr d**. SB1, a blue illuminated pushbutton on the rear panel with a view of the robot, edge-evaluated (0.1–5 s) in
  the PNOZ. Estimate 1.0e-7 → **PL d**.

### SF14 Mode selection and manual mode
- **PLr d**. Key SK1 with 2 contacts: AUTO = 10, MANUAL = 01, SERVICE = 00 (a wire break gives the safest mode), 11 = fault.
  MANUAL: SLS 0.3 m/s, scanners still active, motion only while the 3-position enabling switch SE1 is held (Cat 3,
  test-pulsed). SERVICE: traction STO + SBC, arms off, coffee off. Pushing the robot needs SBU: INSafe_3/4 are free and
  SBU on a safety input is documented [V:E8] (only in SWITCHED_ON_DISABLED / READY_TO_SWITCH_ON). Not wired in rev B2:
  a 2-channel SBU needs one more relay pair (third EF 4DI4DOR, +€380); until then the robot is moved in SERVICE with the
  drives powered and SBU commanded over CANopen Safety is not used.
- Estimate 2.8e-7 → **PL d**.

### SF15 Coffee module stop
- **PLr b, to be confirmed**. The capsule machine is an appliance (EN 60335-2-15). Its hot water stays enclosed, and the
  only motion is the shuttle (Actuonix, low force): S1, F2, P1 → b. Rev A had PLr c (S2 for scalding). In rev B, scalding
  is handled by the appliance standard and by the tray/cup handling rules.
- Means: KI4 interposing relay (Phoenix PLC-RSC) on the PNOZ auxiliary output S0 (the K4 coil, 92 mA, exceeds the 75 mA
  output [V:FI1/P7]) → K4, Cat B, with K4 aux read back (SR2 I0). Estimate 3.8e-6 → **PL b**.
- If the risk assessment keeps PLr c: drive KI4 from a free B0 safe SC output (O1, cost €0 in rev B2) and add the U7
  remote OFF as a diverse second channel (Cat 1).

### SF16 Hand-over in the hand / collaborative operation (C48 only)
- **PLr d** per ISO 10218-1/-2:2025. C48: arm-internal PL d Cat 3 functions + scanner SSM (SF7). **OA: impossible.**
  With OpenArm, hand-over happens only via the tray while the arms are parked (SF8).

## What OpenArm makes impossible (unchanged)

| Function | Why | Consequence |
|---|---|---|
| Safe stop with holding (SS2/SOS) | no brakes, no safe encoders | every stop drops the arm onto its rests; cat 0/1 only |
| Hand-over in the hand, PFL | no safety-rated force/speed monitoring | tray hand-over only |
| PL e for arm-related functions | scanner is Type 3 / PL d | if P2 is concluded → not certifiable |
| Arms powered while the base moves fast | no safe standstill monitoring | carry mode = arms parked AND unpowered |
| Safe reduced speed of the arm | Damiao limits are firmware | the P1 argument rests on non-safety measures |

Renumbering map rev A → rev B: SF1–SF8 keep their numbers (SF5 is now SLSa instead of SDI), rev A SF9/SF10 are deleted,
SF11→SF9, SF12→SF10, SF13→SF11, SF14→SF12, SF15→SF13, SF16→SF14, SF17→SF15, SF18→SF16. Documents in `../ce/` still use
the rev A numbers.
