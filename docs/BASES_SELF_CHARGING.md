# Giorgio: mobile bases with manufacturer-confirmed self-charging, and the on-board power-station question

Research date: 2026-10-03. Web search was not available. Every value below was read from an official manufacturer page, manual or datasheet, or from a distributor page, using direct fetches. Each value carries one of these labels:

- **V**: verified from the cited URL (page text, PDF text, or a dimension printed on an official drawing).
- **D**: verified, but from a distributor page (Generation Robots), not from the manufacturer.
- **UNVERIFIED**: not found, could not be fetched, or inferred. Inferences are marked "(inference)".

## Owner's requirement

1. **Hard requirement**: the robot docks and charges itself on a dock that the base manufacturer sells and documents.
2. **Preferred**: an open platform (ROS 2, documented API, no mandatory subscription).
3. **Payload margin** over a superstructure of about 70 kg (the target is 64 to 68 kg). The superstructure is tall: a column with two OpenArm 2.0 arms at 24 V.
4. Reference loads from `docs/alimentazione_e_certificazione.md`:
   - typical superstructure draw is about 250 W without coffee;
   - the arms run on a 24 V bus;
   - a 230 V inverter on board lengthens certification.

---

## 1. Summary table

**Margin** is rated payload minus 70 kg. **Energy** is nominal pack voltage times Ah.

| Base | Rated payload / margin | Own mass | Footprint L x W x H (deck) | Battery / energy | Accessory power out | Manufacturer dock | Openness | Safety | Price (excl. VAT) |
|---|---|---|---|---|---|---|---|---|---|
| **Robotnik RB-THERON** | **200 kg (D) / +130 kg** | 70 kg (D) | 717 x 550 x 320 mm (V, drawing) | 48 V 15 Ah = 0.72 kWh (V) | 12 V / 24 V / VBATT (D); current not published | **"Charging station" included** (V) | ROS 2 native. Docking orchestrator `robotnik_charge` is public (BSD-3) | 2 safety LiDARs + safety PLC (V); ISO 3691-4 / ISO 13482 stated for RB-THERON+ (V) | **EUR 25,950** (D) |
| **Slamtec Poseidon** | **150 kg rated, 200 kg max (V) / +80 kg** | 80 kg std, 95 kg hot-swap (V) | 570 x 520 x 320 mm, deck 236 mm (std) or 65 mm (low-CoG) (V) | 48 V 30 Ah = 1.44 kWh (V) | **48 V 30 A** (hot-swap version: max 110 A) (V) | Charging method "Automatic / Manual" (V); dock product sheet not found | "Native ROS/ROS2 support and a mature SDK" (V). Navigation is the proprietary SLAMWARE stack | Dual E-stops, dual brakes, front + rear LiDAR (V); no safety-rated scanner or PL stated | not published |
| **Neobotix MPO-500 (high-payload option)** | 80 kg std, **250 kg option (V)** / +10 or +180 kg | 105 kg (datasheet, Nov 2025) or 80 kg (manual) (V, conflicting) | 988 x 662 mm, mounting plane 386 mm (V, manual) | **24 V** 50 Ah = 1.2 kWh, AGM or LiFePO4 (V) | 24 V terminals on RelayBoard (5 A fuse) (V); larger feed UNVERIFIED | **Automatic charging station** (optional, documented in manual) (V) | ROS 2 (repos `neo_mpo_500-2`, `neo_docking2` public; licence not declared) (V) | SICK nanoScan3, "PL d and SIL2" scanners, safety relays, fail-safe brakes (V) | not published |
| Robotnik RB-KAIROS (+) | 100 kg std wheels / 250 kg "strong" wheels (V, D) | 115 kg (D) | 978 x 776 x 690 mm (D) | 48 V 58 Ah = 2.78 kWh (D) | 12 V / 24 V / VBATT (D) | Charging station included (D) | ROS 2 | Safety Pack: 2 safety scanners + safety PLC (D) | EUR 34,950 base; EUR 35,950 for the + version (D) |
| AgileX Ranger Air | **80 kg (V) / +10 kg (+12 to +16 kg at 64 to 68 kg)** | 50-55 kg (V) | 552 x 500 x 250 mm (V) | **24 V 30 Ah = 0.72 kWh (V)** | 24-29.6 V, max 25 A, max 600 W total (V) | Product page: "Features automatic recharging" (V). **No dock datasheet; manual is silent** | CAN protocol documented; ROS 2 driver `ranger_ros2` (BSD-3). Auto-charge needs the AgileX NAVIS stack + AgileX kit | On-board E-stop only. No external safety input. Manual: "does not have complete safety functions" (V) | not published |
| Neobotix MP-500 | 80 kg (V) / +10 kg | 70 kg (V) | 814 x 592 x 361 mm (V) | 24 V 50 Ah lead (V) | as MPO-500 (UNVERIFIED) | Automatic charging station (optional) (V) | ROS 2 | SICK S300 Expert (V) | not published |
| Neobotix MPO-700 | 400 kg (V) / +330 kg | 142 kg (V) | dimensions in manual (not extracted) | uptime about 5 h (V) | UNVERIFIED | Automatic charging station (V, manual table) | ROS 2 (`neo_mpo_700-2`) | S300 Expert (V) | not published |
| Robotnik RB-VOGUI | 150 kg (V) / +80 kg | 165 kg (D) | 1044 x 776 x 742 mm (D) | 48 V 45 Ah (V) or 29 Ah (D) | DC out (D) | Charging station (V) | ROS 2 | safety LiDARs + PLC | EUR 53,950 (D). Built for outdoor; too large |
| Slamtec 48V Hermes | 50 kg rated / 80 kg max (V); **fails** | 60 kg (V) | 465 x 545 x 357 mm (V) | 44.8 V 29.4 Ah (V) | 48 V 30 A (V) | Recharging, "precision docking camera ±1.5 cm, ±1°" (V) | SLAMWARE HTTP SDK | bumper, depth cameras | not published. Spec also limits whole-machine CoG to 18 cm |
| Slamtec Apollo 2.0 | 80 kg rated / 100 kg max (V); marginal | 40 kg (V) | 520 x 520 x 270 mm (V) | 24 V LFP (V) | 24 V 10 A (20 A+ custom) (V) | Autonomous charging (V) | SLAMWARE HTTP SDK | E-stop button (V) | not published |
| Reeman Big Dog | 100 kg (V) / +30 kg | 50 kg (V) | 704 x 470 x 397 mm (V) | 25 Ah, 960 Wh (V) | not stated | "automatic charging" (V), no dock details | "Open SDK", API (V). ROS not stated | not stated | not published |
| PAL TIAGo Base | 70 kg (V); **fails** | 47 kg (V) | diameter 540 mm (V) | autonomy 10 h (V) | not extracted | Dock Station (V) | ROS | CE-marked industrial version available (V) | not published |
| Clearpath Ridgeback | 100 kg / +30 kg | 135 kg | 960 x 793 x 311 mm | 24 V 100 Ah AGM | 5 V 5 A, 12 V 7 A, 25.6 V 16 A | **No autodock found**; fails the hard requirement | ROS 2 Jazzy | E-stop header is not safety-rated | contact sales |
| Clearpath Dingo | 20 kg; **fails** | 13 kg | n/a | n/a | n/a | Wibotic wireless charging kit, 150 W (V) | ROS 2 Jazzy | n/a | n/a |
| Segway Nova Carter | about 50 kg (V*); **fails** | 51.2 kg (V*) | 722 x 500 x 556 mm (V) | 1033 Wh (V*) | n/a | Nova Carter Charging Dock: spring posts, live only on contact, open-source docking modules (V) | ROS / Isaac | n/a | n/a |
| Youibot, OTTO | page content is client-rendered; no specs extracted | | | | | | | | UNVERIFIED |

\* On the Nova Carter page the spec labels and values are interleaved. I read them as "value then label" (51.2 = net weight, 50 = max load, 1033 = Wh), which gives consistent numbers, but the reading is my interpretation.

**Bases that meet all three filters (manufacturer dock + ROS 2 + payload ≥ 100 kg):**

- RB-THERON
- Poseidon
- MPO-500 with the 250 kg option
- RB-KAIROS
- MPO-700
- RB-VOGUI (too big)

Ranger Air meets the dock requirement only at the level of a sentence on its product page, and its margin is thin.

---

## 2. Details per base

### 2.1 Robotnik RB-THERON / RB-THERON+

| Item | Value | Status / source |
|---|---|---|
| Battery | "UN38.3 - 48VDC@15Ah", autonomy up to 8 h; RB-THERON+ up to 6 h | V, [R1] |
| Speed, environment | up to 1.25 m/s, indoor, IP30 | V, [R1] |
| Included | CPU i7, IMU, RGBD camera, 5G router, "Safety Pack 360º: 2D Safety LiDARs + Safety PLC", **Charging station** | V, [R1] |
| Dimensions | 717 (660 body) x 550 x 320 mm; 418 mm with the lifting unit; 16 mm ground clearance | V, datasheet drawing [R2] |
| Mass / payload | 70 kg / "up to 200 kg" | D, [G1] |
| Drive | 2 x 250 W with brake, differential; max slope 6 % | D, [G1] |
| Power outputs | "12V / 24V / VBATT", currents not published | D, [G1] |
| RB-THERON+ (with cabinet + UR arm) | 1076 x 552 x 655 mm; platform 160 kg; platform payload 100 kg; ISO 3691-4 and ISO 13482 stated | D [G2]; V for the ISO claim [R1] |
| Docking software | `RobotnikAutomation/robotnik_charge` (BSD-3, ROS 2 Jazzy). Sequence: dock to the station marker frame, move onto contacts, **activate relay**, wait for "charge detected", retry or back off. Safety-laser field switching for docking is marked "still pending to be implemented". So it is a contact dock, and the base stays powered while docked (inference) | V, [R3] |
| External E-stop / safety I/O for the superstructure | Safety PLC present. Input count and type not published | UNVERIFIED: ask Robotnik |
| Price | EUR 25,950 excl. VAT (31,140 incl.) | D, [G1] |

Assessment:

- **Strengths**: the most complete match to the requirement. The dock ships in the box, the docking stack is open source, the safety PLC and safety scanners are integrated, an ISO 3691-4 claim exists (for the + version), and the price is published. The 200 kg payload leaves a large margin. The footprint (717 x 550) is close to the target.
- **Weakness**: energy. 0.72 kWh is the same as the Ranger Air. At about 250 W superstructure plus traction, expect roughly 2 to 2.5 h between charges (inference). Opportunity charging between tasks makes that workable.
- **Integration**: the pack is 48 V, so Giorgio needs a 48→24 V DC-DC for the arms. That fits the 48 V architecture in `alimentazione_e_certificazione.md`.

### 2.2 Slamtec Poseidon (embodied-intelligence platform)

| Item | Value | Status / source |
|---|---|---|
| Standard version | 570 x 520 x 320 mm; 80 kg; mounting-deck height 236 mm; turning diameter 720 mm | V, [S1] |
| Hot-swap version | 690 x 600 x 316 mm; 95 kg; deck 65 mm; 2 x 15 Ah | V, [S1] |
| Payload | rated 150 kg (max 200 kg) | V, [S1][S2] |
| Power supply capability | 48 V 30 A (hot-swap version: 48 V 30 A, max 110 A) | V, [S1] |
| Battery | LFP 48 V 30 Ah, 8 h, 3 h charge; **"Charging Method: Automatic / Manual"**; battery swap via charging cabinet | V, [S1] |
| Kinematics | 4-wheel independent steering (lateral, diagonal, spin, parking), 1.5 m/s, 10° slope, 40 mm gap, stop accuracy ±20 mm / ±1° | V, [S2] |
| High-CoG design | "maintains stable motion performance even at a total robot height of 1.8 m, with a static anti-tip coefficient of up to 1.65" | V, [S2] |
| Software | "native ROS/ROS2 support and a mature SDK" (C++, Python, ROS). Navigation is Slamtec's proprietary SLAMWARE stack. `slamtec/slamware_ros_bridge` is BSD-2 | V, [S2][S5] |
| Safety | front and rear LiDAR, vision, 8 ultrasonics, "dual braking systems and dual emergency stops, with core components certified to international standards" | V, [S2]. Safety-rated scanner, PL and external safety input: UNVERIFIED |
| Dock product (contacts, dimensions, price) | not published. The sister 48V Hermes lists a "precision docking camera" with ±1.5 cm / ±1.0° docking accuracy | UNVERIFIED for Poseidon; V for Hermes [S3] |
| Price / lead time | not published (Alibaba store and sales@slamtec.com) | UNVERIFIED |

Assessment:

- **Strengths**: the best mechanical fit. It is built for exactly this kind of tall embodied-AI superstructure. It has twice the energy of the Ranger Air or THERON, and its 48 V 30 A output can feed a 48→24 V arm bus directly.
- **Weaknesses**:
  - Openness is weaker than Robotnik or Neobotix: you drive it through SLAMWARE, with a ROS bridge on top.
  - There is no published safety rating.
  - The dock has to be confirmed in writing as a product, with a datasheet.

### 2.3 Neobotix MPO-500 (also MP-500 and MPO-700)

| Item | Value | Status / source |
|---|---|---|
| Payload | 80 kg, "Option: high payload of 250 kg" | V, datasheet 28 Nov 2025 [N1] |
| Mass | 105 kg (datasheet) vs 80 kg ("Weight 80 kg", manual) | V, conflicting [N1][N2] |
| Dimensions | overall length 988 mm, max width 662 mm, mounting plane 386 mm, scanner cover 409 mm, track 548 mm, wheel 254 mm | V, manual [N2] |
| Battery | 24 V, 50 Ah, AGM or LiFePO4. Battery quick change without tools | V [N1][N2] |
| Uptime / charge | about 5 h / 5 h; max 0.8 m/s | V [N1] |
| Automatic charging station | Wall-mounted. Bottom edge of the backplate on the floor; needs a free path at least 1.0 m wide. The charger sits inside the station. Contacts carry current only after the charger detects the correct batteries. On the robot, the charging contacts are isolated by a software-controlled relay on the RelayBoard. The station's dimension table covers MP-400, MP-500, MPO-500 and MPO-700 | V, manual §3.5.1 [N2] |
| Docking software | `neobotix/neo_docking2` (ROS 2, contour matching, safety-mode switching for approach and departure) | V [N4] |
| Safety | SICK nanoScan3 ("approved as safety device with Performance Level d and SIL2"); E-stop buttons cut drive power and engage fail-safe brakes; safety-relay diagnostics; wireless E-stop supported | V, manual [N2] |
| Power for payload | "24 V Terminals" on RelayBoard, 5 A fuse. A larger superstructure feed would need confirmation | V for the fuse [N2]; high-current tap UNVERIFIED |
| Software | ROS / ROS 2 / PlatformPilot. Web lists "ROS 2 Start" and "ROS 2 Advance" packages (whether these are paid licences: UNVERIFIED). GitHub repos `neo_mpo_500-2` and `neo_mpo_700-2` are public, but no licence is declared | V [N3][N4] |
| MP-500 | 80 kg payload, 70 kg, 814 x 592 x 361, 24 V 50 Ah lead, up to 10 h | V [N5] |
| MPO-700 | 400 kg payload, 142 kg, 0.9 m/s, about 5 h / 4 h, S300 Expert | V [N6] |

Assessment:

- **Strengths**: a mature research and industry vendor. The documented auto-charging station and the PL d / SIL2 scanners give the best documented safety story of the open vendors. The pack is **24 V native**, which matches OpenArm's 24 V bus.
- **Weaknesses**: heavy (105 kg) and long (988 mm). You must order the 250 kg option, because the standard 80 kg leaves no margin. Price and lead time come only on request.

### 2.4 AgileX Ranger Air (the current design choice)

| Item | Value | Status / source |
|---|---|---|
| Dimensions | 552 x 500 x 250 mm; wheelbase 388 mm; front/rear track 338 mm; ground clearance 39 mm | V, manual [A1] |
| Mass / payload | 50-55 kg; "The maximum payload of RANGER AIR is 80KG" | V [A1] |
| Battery | LiFePO4 24 V 30 Ah; normal voltage range 24-29.4 V; 3 h charge with the 10 A charger | V [A1] |
| **Endurance** | **6.5 h no load, 2.5 h full load**; range 45 km no load, 25 km full load | V [A1] |
| Accessory power | rear 4-pin aviation plug: VCC 24-29.6 V, load current max 25 A; "total power must not exceed 600w"; CAN_H/CAN_L. Expansion and drive power are cut below 10 % SOC | V [A1] |
| Speed / IP | 5.4 km/h; IP22 | V [A1] |
| Safety | rear E-stop switch (error cleared by key or CAN command). No external safety input. "This robot does not have complete safety functions of a fully autonomous mobile robot" | V [A1] |
| Payload CoG | centroid at the centre of rotation (Fig. 2.2); no height limit published | V [A1] |
| **Self-charging claim** | Product page: "Automatic Charging & Obstacle Avoidance – Features automatic recharging to complete prolonged unattended operations" | V [A2] |
| Dock in the manual | **Not mentioned.** Only the 10 A charger and the rear charging port | V (as absence) [A1] |
| Dock product, specs, price | No stand-alone dock in AgileX's global catalogue. The NAVIS API documents `/find_charger/*` services and refers to a "wireless charging pile", charged via "the autonomous charging kit produced by our company". Example telemetry is 54.9 V / 10.89 A, which matches a 48 V robot, not the 24 V Air | V [A3][A4] |
| "EUR 835, 24/48 V, 5-10 A" (quoted in `alimentazione_e_certificazione.md`) | not found in any official source | **UNVERIFIED**: remove or replace with a written quote |
| Payload powered while docked? | Not documented. The NAVIS state machine has a "charging" state (9), so the base computer is up while docked (inference). For UMR, the manual forbids manual charging while on the auto pile | UNVERIFIED for Ranger Air |

Assessment:

- **Margin**: only 10 kg at 70 kg, or 12 to 16 kg after the weight cut.
- **Stability**: the CoG must sit over the centre of rotation, on a 338 to 388 mm wheel base under a tall bimanual column.
- **Energy**: the manual states 2.5 h at full load, and that is before the superstructure draws its 250 W from the same 0.72 kWh (inference: about 1.5 to 2 h real).
- **Dock**: the self-charging claim is one sentence on a product page, with no dock datasheet, and its software path goes through NAVIS.
- **Verdict**: acceptable as a low-cost prototype base only if AgileX confirms in writing:
  1. the dock part number and price for the 24 V Air;
  2. contact or wireless, and the charge current;
  3. that the payload port stays live while docked;
  4. that docking can be triggered without NAVIS, or that NAVIS has no subscription.

  The written list of questions already exists in `AGILEX_REQUEST.md`.

### 2.5 Others checked

- **Robotnik RB-KAIROS(+)**:
  - 250 kg with the strong-wheel option; 48 V 58 Ah (2.8 kWh, the best energy here); charging station included; safety PLC; EUR 34,950 (D).
  - At 978 x 776 x 690 mm with mecanum wheels it is big and tall for a café or office robot. The 690 mm deck raises the overall CoG.
  - Pick it over THERON only if runtime matters more than size.
- **Slamtec Phoebus** (300 kg, automatic recharge, 780 x 506 x 270, 90-105 kg): an industrial lifter, and overkill. **Apollo 2.0** (80 kg rated / 100 kg max, 24 V 10 A out, autonomous charging) has too little margin. **Hermes / 48V Hermes** (50 kg rated, whole-machine CoG limited to 18 cm) does not fit. [S3][S4]
- **Reeman Big Dog**: 100 kg, 50 kg own mass, 960 Wh, "automatic charging", "Open SDK". No ROS, safety or dock details are published. Second-tier. [E1]
- **PAL TIAGo Base**: 70 kg payload (zero margin), with a dock station and a CE-marked industrial version. Fails on payload. **TIAGo Pro** is a complete robot (36 V, 12 V 8 A user power, dock station), not a base for a third-party superstructure. [P1][P2]
- **Clearpath**:
  - **Ridgeback** (100 kg, 135 kg own mass, AGM 24 V): no autodock product found, so it fails the hard requirement.
  - **Dingo** has a Wibotic 150 W wireless charging kit, but only 20 kg payload.
  - OTTO (now Rockwell) pages are client-rendered and I could not extract specs. It is a closed industrial stack in any case. [C1][C2]
- **Segway**: Nova Carter (about 50 kg load) has a well-specified dock (spring-loaded posts, power only on contact, open-source docking modules), but its payload is too low. The RMP page has no extractable specs. [SG1]
- **Youibot**: product pages are client-rendered; nothing could be extracted (UNVERIFIED).

---

## 3. Ranking for the owner's requirement

The criteria, in priority order:

1. a self-charging dock confirmed and documented by the manufacturer;
2. openness;
3. payload margin with about 70 kg, tall;
4. energy and safety.

| Rank | Base | Why | What to get in writing first |
|---|---|---|---|
| **1** | **Robotnik RB-THERON** | Dock included as standard. ROS 2 docking stack public (BSD-3). Safety PLC + safety LiDARs. ISO 3691-4 claim. 200 kg payload (+130 kg margin). Published price EUR 25,950. Compact (717 x 550). | Current rating of the 24 V and VBATT outputs. Can the superstructure stay powered while docked? External E-stop / safety-PLC inputs for the PNOZ chain. Payload CoG-height limit. Declaration of incorporation. Larger battery option (0.72 kWh is short). |
| **2** | **Slamtec Poseidon** | 150 kg rated (+80 kg margin). Explicitly designed for 1.8 m tall superstructures. 48 V 30 A payload power. 1.44 kWh. Automatic charging listed as a charging method. ROS/ROS 2 + SDK. | Dock datasheet (contacts, power, price). Whether ROS 2 control bypasses SLAMWARE or needs it. Any licence or cloud fees. Safety rating of scanners and E-stop chain, external safety input. Price and lead time to the EU. |
| **3** | **Neobotix MPO-500 with 250 kg option** (or MPO-700) | Automatic charging station documented in the manual. nanoScan3 PL d / SIL2. 24 V native pack (no DC-DC needed for the arms). ROS 2 repos public. | Price and lead time. Mass (105 vs 80 kg). Whether "ROS 2 Start/Advance" is a paid licence. High-current 24 V tap for about 600 W of arms. Whether a free-standing station exists (the standard one is wall-mounted). |
| 4 | Robotnik RB-KAIROS(+) | Same openness and safety as THERON, 2.8 kWh, 250 kg option, EUR 34,950. | Too big and tall for a service robot (978 x 776 x 690). |
| 5 | AgileX Ranger Air | Cheapest and lightest. 24 V matches the arms. The product page claims auto-recharge. | Fails "documented dock" until AgileX supplies a datasheet. Thin margin (10 to 16 kg). 2.5 h full-load endurance before the superstructure load. No safety I/O. |

**Bottom line**:

- If the owner's "manufacturer-confirmed, documented dock" rule is applied strictly, the Ranger Air does not pass today. RB-THERON passes on public evidence alone, and it is the recommended base.
- Poseidon is the best mechanical fit but needs written confirmations.
- Neobotix is the best documented safety and charging option, at the cost of mass and size.
- With THERON (or Poseidon) the 64 to 68 kg weight-cut effort is no longer critical. The mechanical lead can spend that effort on CoG height instead.

---

## 4. Portable power station (BLUETTI / EcoFlow) as an on-board energy router or buffer

### 4.1 What the products actually offer

| Model | Capacity / chemistry / cycles | Mass | DC outputs | 24 V output? | DC input (could take base or dock power) | AC input | Pass-through / UPS | Control | Source |
|---|---|---|---|---|---|---|---|---|---|
| BLUETTI AC70 | 768 Wh / 24 Ah, LiFePO4; "3,000+ cycles" | 10.2 kg | cigarette lighter 12 V 10 A; USB-A 5 V 2.4 A x2; USB-C up to 20 V 5 A x2 | **No** | XT60, **12-58 V, 10 A, 500 W max** | 850 W max | "UPS switching time ≤20 ms" | Bluetooth 5.0/5.1 app | V [B1][B2] |
| BLUETTI AC180 | 1152 Wh, LiFePO4 | 16.4 kg | cigarette lighter 12 V 10 A; USB; 15 W wireless pad | **No** | DC7909, **12-60 V, 500 W / 10 A max** | 1440 W max | UPS ≤20 ms ("test the function before use") | Bluetooth app | V [B3] |
| BLUETTI AC200L, EB3A | specs not extractable (client-rendered pages; no manual URL found) | | | | | | | | UNVERIFIED |
| EcoFlow RIVER 2 Pro | 768 Wh, LFP; 80 %+ after 3000 cycles | about 8.3 kg (18.2 lb) | "DC Output 12.6V, 10A/3A/3A, 126W Max"; DC5521 12.6 V 3 A | **No** | solar 11-50 V 13 A, **220 W max**; car input 12/24 V 8 A, 100 W | 940 W (US) | "<30ms EPS auto-switch" | Wi-Fi + Bluetooth app | V [F1] |
| EcoFlow DELTA 2 | 1024 Wh, LFP; 3000 cycles to 80 %+ | 12 kg | car output 12.6 V 10 A 126 W; DC5521 12.6 V 3 A x2 | **No** | solar 11-60 V 15 A, **500 W max**; car 12/24 V 8 A | 1200 W | EPS (switch time not stated on the EU page) | Wi-Fi + Bluetooth | V [F2]. The US DELTA 2 URL now redirects to DELTA 3 |

Certifications:

- RIVER 2 Pro: the page claims "TÜV Rheinland safety certification", with no standard numbers given.
- BLUETTI manuals: these carry FCC statements. I found no UN 38.3 / IEC 62619 / CE declaration in the fetched documents, so their status is **UNVERIFIED**. Products of this class normally hold UN 38.3 to ship, but I did not see a document.

### 4.2 Manufacturer restrictions that matter on a robot (verbatim)

- BLUETTI AC70 manual: "DO NOT move the product while operating as vibrations and sudden impacts may lead to poor connections to the hardware inside." [B2]
- BLUETTI AC180 manual: "This product is not suitable for providing electrical service for equipment and machines that are highly dependent on the reliability of electrical power supply and that involve personal safety…" [B3]
- BLUETTI AC70 manual excludes liability for "devices that require a high-performance Uninterruptible Power Supply (UPS)". [B2]

### 4.3 Verdict: do not put a consumer power station on Giorgio

1. **No regulated 24 V output.** Every model checked offers only 12 V at 10 A (about 126 W) on DC, plus USB-C up to 100 W. Feeding the 24 V arm bus would mean DC → 230 V inverter → 24 V PSU:
   - double conversion losses;
   - idle inverter draw;
   - and **230 V AC on board**, which `alimentazione_e_certificazione.md` already identifies as lengthening certification (6-9 months becomes 12-18).
2. **Mass**: 8 to 16 kg for 0.77 to 1.15 kWh. On a Ranger Air this eats the whole 10 to 16 kg margin. On THERON or Poseidon the payload is there, but the energy is better bought as a bigger base pack, or as a pack you design yourself.
3. **Operating misuse**: BLUETTI explicitly forbids moving the unit while it operates, and excludes safety-relevant machinery. Using one on a mobile machine that you CE-mark yourself shifts all the battery-safety evidence onto you:
   - IEC 62619 / UN 38.3 documentation;
   - vibration;
   - and integration of its BMS faults into the safety concept,

   with no technical file from the vendor to lean on.
4. **No machine interface.** Control is a phone app over Bluetooth or Wi-Fi. There is no documented local CAN or serial API in the fetched material, so the robot cannot reliably read SOC, inhibit outputs, or log faults (UNVERIFIED that no API exists; none is documented on the pages fetched).
5. **Pass-through is "EPS/UPS" with ≤20-30 ms switchover**, not a true online UPS. That gap is long enough to drop a Jetson or brown out motor drivers if the input switches.
6. **What one could legitimately do with it**: the wide DC inputs (12-60 V, 500 W on AC180/AC70/DELTA 2) could take 48 V from a base or a dock. So a power station can serve as an off-robot coffee or 230 V utility at the docking station. It does not belong on the machine.

**Recommended instead** (only if the chosen base cannot supply peak arm power):

- **Pack**: a purpose-built 24 V (8s) LFP buffer with a CAN-reporting BMS that carries IEC 62619 + UN 38.3 documentation.
- **Charging**: charged from the base's VBATT/48 V through a CE DC-DC charger.
- **Connection**: an ideal-diode or ORing into the arm bus.
- **Size**: about 0.3 to 0.7 kWh, roughly 3 to 7 kg (estimate). The BOM already carries a ≤2 kg / EUR 250 option (8s1p 6 Ah + BMS + charger module + ideal diode) for exactly this case.

With the RB-THERON or Poseidon (48 V packs, 48 V 30 A out on Poseidon) a buffer is probably unnecessary: a 48→24 V DC-DC sized for arm peaks does the job.

---

## 5. Sources (fetched 2026-10-03)

**Robotnik**
- [R1] https://robotnik.eu/products/mobile-robots/rb-theron/
- [R2] https://robotnik.eu/wp-content/uploads/2024/07/Theron-v4.0-dibujo-para-datasheet-EN-01.webp (datasheet drawing)
- [R3] https://github.com/RobotnikAutomation/robotnik_charge (README; BSD-3)
- RB-VOGUI: https://robotnik.eu/products/mobile-robots/rb-vogui/
- RB-KAIROS: https://robotnik.eu/rb-kairos-2-2/

**Generation Robots (distributor)**
- [G1] https://www.generationrobots.com/en/404262-rb-theron-autonomous-mobile-robot-2068.html
- [G2] https://www.generationrobots.com/en/404394-rb-theron-mobile-manipulator-robot-2072.html
- RB-KAIROS: https://www.generationrobots.com/en/404396-rb-kairos-indoor-autonomous-mobile-robot-2074.html
- RB-VOGUI: https://www.generationrobots.com/en/404263-mobile-autonomous-robot-rb-vogui-1799.html

**Slamtec**
- [S1] https://www.slamtec.com/en/poseidon/spec
- [S2] https://www.slamtec.com/en/poseidon
- [S3] https://www.slamtec.com/en/48v-hermes/spec, https://www.slamtec.com/en/hermes/spec
- [S4] https://www.slamtec.com/en/apollo2/spec, https://www.slamtec.com/en/phoebus/spec, https://www.slamtec.com/en/athena2/spec
- [S5] https://github.com/slamtec/slamware_ros_bridge

**Neobotix**
- [N1] https://www.neobotix-robots.com/fileadmin/images/downloads/Datenbl%C3%A4tter/Data-Sheet_MPO-500.pdf
- [N2] https://www.neobotix-robots.com/fileadmin/images/downloads/Bedienungsanleitung_2022/MPO-500_Englisch.pdf
- [N3] https://www.neobotix-robots.com/products/mobile-robots/mobile-robot-mpo-500
- [N4] https://github.com/neobotix/neo_docking2, https://github.com/neobotix/neo_mpo_500-2
- [N5] https://www.neobotix-robots.com/fileadmin/images/downloads/Datenbl%C3%A4tter/Data-Sheet_MP-500.pdf
- [N6] https://www.neobotix-robots.com/fileadmin/images/downloads/Datenbl%C3%A4tter/Data-Sheet_MPO-700.pdf

**AgileX**
- [A1] https://cdn.shopify.com/s/files/1/0551/0630/6141/files/RANGER_AIR_USER_MANUAL_AgileX_Robotics.pdf?v=1788332629
- [A2] https://global.agilex.ai/products/mobile-manipulator (Ranger Air product page)
- [A3] https://raw.githubusercontent.com/agilexrobotics/Navis/master/user_api.html
- [A4] https://global.agilex.ai/products.json?limit=250
- UMR manual: https://cdn.shopify.com/s/files/1/0551/0630/6141/files/UMR_USER_MANUAL_-_AgileX_Robotics_Universal_Mobile_Robot.pdf?v=1788332754

**Others**
- [E1] Reeman: https://www.reemanrobot.com/robot-chassis/big-dog-robot-chassis.html
- [P1] PAL TIAGo Base: https://pal-robotics.com/robot/tiago-base/
- [P2] PAL TIAGo Pro: https://pal-robotics.com/robot/tiago-pro/
- [C1] Clearpath Ridgeback: https://clearpathrobotics.com/ridgeback-indoor-robot-platform/
- [C2] Clearpath Dingo: https://clearpathrobotics.com/dingo-indoor-mobile-robot/
- [SG1] Segway Nova Carter: https://robotics.segway.com/nova-carter/

**Power stations**
- [B1] https://www.bluettipower.com/products/ac70
- [B2] https://cdn.shopify.com/s/files/1/0536/3390/8911/files/AC70_User_Manual_US_EN_V1.0.pdf
- [B3] https://cdn.shopify.com/s/files/1/0536/3390/8911/files/AC180_User_Manual_6812221c-ec19-42ce-8aba-ef1f72152d98.pdf
- [F1] https://us.ecoflow.com/products/river-2-pro-portable-power-station
- [F2] https://eu.ecoflow.com/products/delta-2-portable-power-station

**Failed or empty fetches**
- Robotnik: `robotnik.eu/products/mobile-robots/rb-kairos-en/` and `/rb-kairos-2/` returned 404.
- AgileX: `global.agilex.ai/products/ranger-air`, `/chassis/ranger-air` and `agilex.ai/chassis/*` returned 404.
- Neobotix: `neobotix-robots.com/products/accessories/automatic-charging-station` returned 404.
- PAL: `pal-robotics.com/robot/tiago-omnibase/` returned 404.
- BLUETTI EU: `bluettipower.eu/products/ac70|ac180|ac200l` returned 404, and `/eb3a` returned a 302 that did not resolve.
- BLUETTI US: the AC200L and EB3A pages are JS-rendered, and Shopify `.json` timed out.
- Client-rendered pages with no specs extracted: Youibot (`en.youibot.com`), OTTO (`ottomotors.com`), Segway RMP (`robotics.segway.com/rmp/`).
