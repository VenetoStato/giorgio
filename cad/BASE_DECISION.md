# Giorgio — mobile base decision

Date 2026-10-03. Question from the owner: "if we say we can do something, we must be sure". Two requirements from the
AgileX Tracer 2.0 manual (V1.0.0, 2025-03) checked by the lead: **payload ≤ 100 kg (p.3, binding)** and **extension centroid at
the centre of rotation (p.3)**. Also from the manual: the accessory power is ≤ 5 A / 120 W (p.5). The rear 4-pin connector
carries VCC/GND/CAN only, so there is **no external E-stop or safety input** (p.11). Charging is a 2-pin plug with a 10 A charger (p.15).
The AgileX web page states 80 kg payload; the datasheet states 150 kg.

## 1. Can Giorgio stay on the Tracer 2.0? Mass and CoG: yes, with margin

After the mass reduction (see VALIDATION.md, "Mass budget"), the superstructure is **80.7 kg**. With the product payload
(2 × 3 kg objects in the hands + 2.1 kg in the chest tray) it is **88.8 kg ≤ 90 kg target**, which is 11.2 kg under the
100 kg manual limit. The extension CoG at nominal (arms home, tray loaded) is **(+4.5, +1.2) mm from the plan centre** (limit
±20 mm). With 2 × 3 kg held 300 mm in front it moves to +24.4 mm. That is transient while handling, so it is reported as WARN.
The plan centre is ASSUMED to be the centre of rotation (drive axle at mid-length, as in the sim). The manual drawing does not
show the axle, so **measure it on the delivered unit**.

It is still above the 80 kg on the AgileX web page. Ask AgileX for a written payload value with our CoG height (≈ 0.6 m above the deck).

## 2. What the Tracer cannot give: a safety-rated stop of the drive

The Tracer has no external E-stop, protective-stop or STO input. Our safety chain (2 × nanoScan3 → Pilz PNOZ, PL d/e) can
cut the arm bus, but it can stop the base only by a CAN command (not safety-rated) or by cutting power to a commercial machine
through an undocumented path. The machine manufacturer then owns that modification. For an EN ISO 3691-4 / EN ISO 13849-1
compliant product this is a **certification blocker**, independent of mass. It is acceptable for the R&D prototype and demos,
with the risk assessment noting it.

## 3. Candidates (data fetched this session from official pages; "UNVERIFIED" = not found)

| | Tracer 2.0 (now) | MiR250 | Robotnik RB-THERON(+) | Robotnik RB-KAIROS+ | AgileX Ranger Mini 3.0 | Clearpath Ridgeback | Custom chassis |
|---|---|---|---|---|---|---|---|
| L×W×H mm | 702×610×169 | 800×580×300 | 717×550×320 | 760×633 body (978×776 over scanners) ×690 | 720×500×345 | 960×793×311 | free |
| own mass | 54–56 kg | 94 kg | UNVERIFIED | UNVERIFIED | 75 kg | 135 kg | ~50–70 kg (estimate) |
| payload | **100 kg manual** / 80 kg web / 150 kg datasheet | **250 kg** | UNVERIFIED (must confirm) | 100 kg (250 kg strong wheels) | 120 kg | 100 kg | 4 × ZLTECH ZLLG65ASM500: 200 kg per pair |
| speed | 2.0 m/s | 2.0 m/s | 1.25 m/s | 1.5 m/s | 2.0 m/s | 1.1 m/s | design |
| battery | 24 V 30 Ah | Li-ion (V UNVERIFIED), 35 A charge, 13 h at max payload | 48 V 15 Ah, 8 h | 48 V 58 Ah, 12 h | 48 V 24 Ah | 24 V 100 Ah AGM | 48 V (ours) |
| external safety stop | **none** | **1 auxiliary E-stop input** + 4 DI/4 DO | safety PLC (external E-stop wiring to confirm) | safety PLC | none (CAN only) | 3.3 V motion-stop header, "backup", not safety-rated | Synapticon SOMANET Integro: STO + SBC SIL3/PLe (for flange motors, not hub motors) |
| safety scanners / cert | none | **2 × SICK nanoScan3**, 12 safety functions ISO 13849-1, designed to ISO 3691-4 (with listed exceptions) | safety LiDARs + PLC, page says ISO 3691-4 and ISO 13482 | safety LiDARs + PLC, cert not stated | none | laser, not safety-rated | ours (full certification on us) |
| docking / charging | "automatic recharging" (web, no detail) | VL-marker docking ±3 mm | charging station included | charging station included | not documented | none found | ours |
| ROS 2 | tracer_ros2 | no official driver (REST API), UNVERIFIED | yes | yes | ranger_ros2 (humble/jazzy) | yes (Jazzy) | ours |
| price | ~7.5 k€ (project README) | not public | not public | not public | not public | not public | parts + certification effort |

Rough tipping with the Giorgio superstructure (inference, not sourced). On MiR250, the deck is 131 mm higher than the Tracer's, so the extension CoG z is ≈ 0.72 m.
The combined CoG is ≈ 0.42 m with a 94 kg base at z ≈ 0.15 m (ESTIMATE). Lateral support ≈ ±0.25 m (ESTIMATE) gives a_tip ≈ 5.9 m/s² (vs 6.7 m/s² on
the Tracer). That is acceptable, but it needs the MiR top-module CoG limits from the MiR user guide (not fetched, UNVERIFIED).

## 4. Verdict

1. **Prototype / demos: keep the Tracer 2.0.** The mass budget is met (88.8 kg ≤ 90 kg with the product payload) and the CoG is centred.
   The whole CAD is validated on it (VALIDATION.md, 0 FAIL). Conditions:
   - a written payload confirmation from AgileX;
   - the axle position measured on the unit;
   - a documented operating limit of 2 × 3 kg objects per arm (software-enforced);
   - the safety-stop gap recorded in the risk assessment (base stopped by CAN + PNOZ-switched power to the arms only).
2. **Sellable product: move to the MiR250.** It is the only candidate with verified, published payload margin (250 kg), the same
   nanoScan3 scanners already integrated, an auxiliary E-stop input for our PNOZ, an ISO 3691-4/13849-1 safety design and
   automatic docking. This removes the scanner corner pods, our own safety-scanner integration and the custom docking contacts,
   and with them most of the certification risk. Costs:
   - closed software (REST API, ROS 2 bridge to be written);
   - higher price (ask for a quote);
   - deck 131 mm higher (re-run the arm reach in the sim, or shorten the column).

   **Second choice: Robotnik RB-THERON+** (ROS 2 native, ISO 3691-4/13482 claimed, charging station, 717×550×320), *only if* Robotnik
   confirms a payload ≥ 100 kg with our CoG. RB-KAIROS+ is too tall (690 mm) for this torso height. Ranger Mini 3.0 and Ridgeback
   have no safety-rated stop input. The Ridgeback is also at its 100 kg limit.
   A custom chassis with STO drives is feasible, but it puts the whole drive-safety certification on us. That is not the shortest path.
3. Actions:
   - ask MiR for the top-module CoG/mass limits and a quote;
   - ask Robotnik for the RB-THERON+ payload;
   - ask AgileX for the payload at 0.6 m CoG and whether a safety input/STO option exists.

## Sources (fetched 2026-10-03 unless noted)

## 1. AgileX Ranger Mini 3.0

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions L x W x H | 720 x 500 x 345 mm | https://cdn.shopify.com/s/files/1/0551/0630/6141/files/RANGER_MINI_3.0_User_Manual.pdf?v=1773112703 | VERIFIED-FETCHED |
| Axle track / front-rear track | 494 mm / 364 mm | same PDF | VERIFIED-FETCHED |
| Own mass | 75 kg | same PDF | VERIFIED-FETCHED |
| Rated payload | 120 kg ("maximum load ... 120 KG") | same PDF; also https://global.agilex.ai/products/ranger-mini | VERIFIED-FETCHED |
| Max speed | 7.2 km/h (2.0 m/s per web page) | PDF + https://global.agilex.ai/products/ranger-mini | VERIFIED-FETCHED |
| Climbing | 15 deg (with 25 kg) | PDF | VERIFIED-FETCHED |
| Ground clearance | 105 mm | PDF | VERIFIED-FETCHED |
| Battery | LiFePO4, 48 V 24 Ah, charge 1.5 h; web page says 6 h runtime and hot-swap | PDF + web page | VERIFIED-FETCHED |
| Steering | 4WD/4WS, spin mode, Ackermann, oblique (crab) | PDF | VERIFIED-FETCHED |
| User power / IO | Rear 4-pin aviation connector: 46-50 V, max 15 A, CAN_H/CAN_L. No E-stop pins | PDF (Fig. 2.3) | VERIFIED-FETCHED |
| Safety I/O | Onboard e-stop switch (Q2) on the rear panel. After it is released, the error must be cleared by key or CAN command. No external E-stop/STO input is documented | PDF | VERIFIED-FETCHED |
| Safety scanners / certification | None. The manual says the integrator must do the risk assessment and add safety functions | PDF | VERIFIED-FETCHED |
| **Payload CoG requirement** | "When installing external equipment ... ensure their centroid location is at the RANGER MINI 3.0's center of rotation." No height limit is stated | PDF | VERIFIED-FETCHED |
| Docking / auto-charging | Not mentioned in the manual (only a charger is in the box) | PDF | UNVERIFIED |
| ROS / ROS 2 | Manual covers ROS Melodic. GitHub agilexrobotics/ranger_ros2 lists "Ranger Mini V2.0 and V3.0" and has humble and jazzy branches | https://github.com/agilexrobotics/ranger_ros2 | VERIFIED-FETCHED |
| Price | Not public: the Shopify JSON price is 0.00 ("contact sales") | https://global.agilex.ai/products/ranger-mini-3.json | UNVERIFIED |
| Related: AgileX UMR | 830x540x410, 90 kg, **70 kg load**, 48V 24Ah, 5.4 km/h, built-in lidar/NAVIS. Payload too low | https://cdn.shopify.com/s/files/1/0551/0630/6141/files/UMR_USER_MANUAL_-_AgileX_Robotics_Universal_Mobile_Robot.pdf?v=1788332754 | VERIFIED-FETCHED |

## 2. MiR250 (Mobile Industrial Robots / Teradyne)

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions L x W x H | 800 x 580 x 300 mm | https://mobile-industrial-robots.com/products/robots/mir250/specifications | VERIFIED-FETCHED |
| Own mass | 94 kg | same | VERIFIED-FETCHED |
| Rated payload | 250 kg | same | VERIFIED-FETCHED |
| Max speed | 2.0 m/s | same | VERIFIED-FETCHED |
| Ground clearance | 25-28 mm; max incline +/-5% at 0.5 m/s; gap tolerance 20 mm | same | VERIFIED-FETCHED |
| Battery | Li-ion. Voltage and capacity are not on the page. Charging current up to 35 A, ratio 1:16, at least 3000 cycles. Up to 13 h with max payload, 17.5 h without payload | same | VERIFIED-FETCHED (voltage UNVERIFIED; 48 V = UNVERIFIED (memory)) |
| Safety I/O | 4 DI, 4 DO (GPIO), 1 Ethernet, **1 auxiliary emergency stop** | same | VERIFIED-FETCHED |
| Safety functions | "12 safety functions according to ISO 13849-1" | same | VERIFIED-FETCHED |
| Scanners | 2x SICK nanoScan3 (front and rear, 360 deg), 2x 3D cameras, 8 proximity sensors | same | VERIFIED-FETCHED |
| Certification | Designed to meet ISO 3691-4 (except clauses 4.4, 4.9.4, 5.1, 6 and Annex A), ISO 13849-1, ISO 13850, ISO 12100, ANSI B56.5, RIA R15.08-1; EMC EN 61000-6-2/-4, EN 12895; IP21 | same | VERIFIED-FETCHED |
| Docking / charging | Docking to VL-marker +/-3 mm; charging specs on the page; charger product page not found | same | VERIFIED-FETCHED (charger: "MiR Charge 48V" = UNVERIFIED (memory)) |
| Corridor / doorway | Default setup needs 1450 mm corridor and 1500 mm doorway. Minimized footprint with protective fields muted: 850 / 800 mm | same | VERIFIED-FETCHED |
| ROS / ROS 2 | Not stated. MiR exposes a REST API; there is no official ROS 2 driver | - | UNVERIFIED (memory) |
| Payload CoG requirement | Not on the spec page. The MiR user guide has top-module CoG limits | - | UNVERIFIED |
| Price | Not public | - | UNVERIFIED (memory: roughly EUR 35-50k, low confidence) |
| MiR100 | No longer listed on the robots page (it lists only MiR250, MiR600, MiR1200 pallet jack, MiR1350). The MiR100 specifications URL returns 404 | https://mobile-industrial-robots.com/products/robots | VERIFIED-FETCHED (discontinued/unlisted) |
| Related: Enabled Robotics MC250 | Mobile cobot on a MiR250 with an "integrated safety/E-stop system for complete robot" (MiR Go partner) | https://mobile-industrial-robots.com/products/mir-go/enabled-robotics-MC250 | VERIFIED-FETCHED |

## 3a. Robotnik RB-KAIROS / RB-KAIROS+

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions | Body 760 x 633 mm. Overall 978 x 776 mm including the corner scanner housings. Height 690 mm. Mecanum wheel diameter 254 mm, ground clearance 66 mm | https://robotnik.eu/wp-content/uploads/2024/07/RB-Kairos-Datasheets-01-1.webp (drawing linked from https://robotnik.eu/rb-kairos-2-2/) | VERIFIED-FETCHED (read from drawing) |
| Own mass | Not on page | - | UNVERIFIED |
| Rated payload | 100 kg with standard mecanum wheels; 250 kg with optional "strong" mecanum wheels | https://robotnik.eu/rb-kairos-2-2/ | VERIFIED-FETCHED |
| Max speed | Up to 1.5 m/s | same | VERIFIED-FETCHED |
| Battery | 48 V @ 58 Ah (UN38.3); autonomy up to 12 h | same | VERIFIED-FETCHED |
| Safety | "Safety Pack 360: 2D safety LiDARs + safety PLC" included | same | VERIFIED-FETCHED |
| Certification | ISO 3691-4 not stated on the KAIROS page | same | UNVERIFIED |
| Docking / charging | Charging station included | same | VERIFIED-FETCHED |
| ROS 2 | "ROS 2-based architecture"; GitHub sim. Driver repo RobotnikAutomation/robotnik_base_hw is active | same + https://github.com/RobotnikAutomation/robotnik_base_hw | VERIFIED-FETCHED |
| Arm integration | RB-KAIROS+ is UR+ approved, plug-and-play for UR7e/UR12e/UR16e (OEM DC e-Series) | same | VERIFIED-FETCHED |
| Environment | Indoor, IP42 | same | VERIFIED-FETCHED |
| Price | Not public | - | UNVERIFIED |
| Note | The URL https://robotnik.eu/products/mobile-robots/rb-kairos/ returns 404, and so do .../rb-kairos-2/ and /products/mobile-manipulators/rb-kairos/. The working page is https://robotnik.eu/rb-kairos-2-2/ | | |

## 3b. Robotnik RB-THERON / RB-THERON+

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions | 717 x 550 x 320 mm (660 mm body length; 418 mm with lifting unit; 16 mm clearance) | https://robotnik.eu/wp-content/uploads/2024/07/Theron-v4.0-dibujo-para-datasheet-EN-01-1536x1086.webp (from https://robotnik.eu/products/mobile-robots/rb-theron/) | VERIFIED-FETCHED (drawing) |
| Own mass / base payload | Not in the fetched page text | - | UNVERIFIED (memory: around 100 kg payload, low confidence; must confirm) |
| Max speed | Up to 1.25 m/s | https://robotnik.eu/products/mobile-robots/rb-theron/ | VERIFIED-FETCHED |
| Battery | 48 VDC @ 15 Ah; autonomy up to 8 h | same | VERIFIED-FETCHED |
| Safety | Safety Pack 360 (2D safety LiDARs + safety PLC) included; E-stop button | same | VERIFIED-FETCHED |
| Certification | "complies with ISO 3691-4 and ISO 13482" (stated for RB-THERON+) | same | VERIFIED-FETCHED |
| Docking / charging | Charging station included | same | VERIFIED-FETCHED |
| ROS 2 | Yes | same | VERIFIED-FETCHED |
| Environment | Indoor, IP30 | same | VERIFIED-FETCHED |
| Price | Not public | - | UNVERIFIED |

## 3c. Robotnik RB-VOGUI / RB-VOGUI+

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions | 1044 x 650 mm body (776 mm over handles/antennas); base top 559 mm; 235 mm wheels; 191 mm clearance | https://robotnik.eu/wp-content/uploads/2026/02/RB-VOGUI-7e-Datasheet-01.jpg | VERIFIED-FETCHED (drawing) |
| Payload | 150 kg (base); RB-VOGUI+ "up to 125 kg on the platform" plus 12.5 kg on the arm | https://robotnik.eu/products/mobile-robots/rb-vogui/ | VERIFIED-FETCHED |
| Speed | Up to 2.5 m/s | same | VERIFIED-FETCHED |
| Battery | 48 VDC @ 45 Ah; up to 6 h | same | VERIFIED-FETCHED |
| Safety | Safety Pack 360 (safety LiDARs + safety PLC) | same | VERIFIED-FETCHED |
| Docking | Charging station included | same | VERIFIED-FETCHED |
| ROS 2 | Yes | same | VERIFIED-FETCHED |
| Environment | Indoor/outdoor, IP53 | same | VERIFIED-FETCHED |
| Mass / price / cert | not found | - | UNVERIFIED |

## 4. Clearpath Ridgeback

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions | 960 x 793 x 311 mm | https://storage.pardot.com/92812/1748526548LF9RMqfY/RIDGEBACK_DATA_SHEET_May2025.pdf (linked from https://clearpathrobotics.com/ridgeback-indoor-robot-platform/) | VERIFIED-FETCHED |
| Own mass | 135 kg | same | VERIFIED-FETCHED |
| Rated payload | 100 kg | same | VERIFIED-FETCHED |
| Max speed | 1.1 m/s | same | VERIFIED-FETCHED |
| Drive | 4 independently driven omni (mecanum) wheels; obstacle clearance 18 mm; indoor | same | VERIFIED-FETCHED |
| Battery | AGM sealed lead-acid 24 V 100 Ah; 15 h with max payload; 8 h charge | same | VERIFIED-FETCHED |
| User power | 5 V @ 5 A, 12 V @ 7 A, 25.6 V @ 16 A | same | VERIFIED-FETCHED |
| Safety I/O | 4 latching mushroom Stop buttons put the motor drivers into an "electrical reset condition". There is an **external motion-stop breakout header** (4-pin "E-STOP BREAKOUT": pins 1-2 latching switch at 3.3 V, pins 3-4 shorted to indicate presence). Clearpath describes it as "a backup option" and the safety chain is not safety-rated | https://docs.clearpathrobotics.com/docs_robots/indoor_robots/ridgeback/user_manual_ridgeback ; https://docs.clearpathrobotics.com/docs_robots/indoor_robots/ridgeback/integration_ridgeback | VERIFIED-FETCHED |
| Scanners | Front laser (optional rear) included; not described as safety-rated | datasheet + brochure https://storage.pardot.com/92812/1748526421haFyNhiQ/Ridgeback_Brochure_2025.pdf | VERIFIED-FETCHED |
| Certification | None stated | - | UNVERIFIED |
| Docking / charging | Only manual charger and shore power are mentioned; no autodock found | user manual | UNVERIFIED (not found) |
| ROS 2 | ROS 2 Jazzy; clearpath_robot repo active | datasheet + https://github.com/clearpathrobotics/clearpath_robot | VERIFIED-FETCHED |
| Payload CoG | Manual only says to avoid payloads overhanging the front/rear (they would block the Stop buttons) | user manual | VERIFIED-FETCHED |
| Price | "Contact us for pricing" | datasheet | VERIFIED-FETCHED (not public) |

## 5. AgileX Tracer 2.0 (reference)

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| Dimensions | 702 x 610 x 169 mm | https://cdn.shopify.com/s/files/1/0551/0630/6141/files/TRACER_2.0_User_Manual.pdf?v=1773112702 | VERIFIED-FETCHED |
| Own mass | 54-56 kg | same | VERIFIED-FETCHED |
| Payload | 100 kg in the manual, **80 kg** on the product web page (conflict) | manual + https://global.agilex.ai/products/tracer-2-0 | VERIFIED-FETCHED |
| Speed | 2.0 m/s in the manual (1.5 m/s low mode); the web page says 1.5 m/s | both | VERIFIED-FETCHED |
| Battery | 24 V 30 Ah (optional 60 Ah); runtime 6.5 h (web) | both | VERIFIED-FETCHED |
| Safety | Onboard e-stop only | manual | VERIFIED-FETCHED |
| Auto-charging | The web page mentions "automatic recharging" capability | web page | VERIFIED-FETCHED (no details) |
| ROS 2 | agilexrobotics/tracer_ros2 exists | https://github.com/agilexrobotics/tracer_ros2 | VERIFIED-FETCHED |

## 6. Custom chassis components

| Quantity | Value | Source URL | Status |
|---|---|---|---|
| **Synapticon SOMANET Integro** (servo drive integrated on the motor) | STO + SBC standard, **SIL3 / PLe Cat.3**. Optional Safe Motion: SS1, SS2, SOS, 4x SLS, safe speed/position/torque, safe fieldbus | https://www.synapticon.com/en/products/somanet-integro | VERIFIED-FETCHED |
| Integro electrical | 24-60 VDC (48 V nominal); 60/120 A RMS peak, 20 A RMS / 40 A continuous; up to 4.5 kW; EtherCAT/EtherNet-IP/PROFINET/CAN; 60/80 mm flange; IP67 | same | VERIFIED-FETCHED |
| Integro caveat | It is a motor-mounted drive for 50-100 mm flange servo motors, not for hub motors. A hub-motor chassis would need a separate STO drive or a geared wheel module | same | (inference) |
| **ZLTECH ZLLG65ASM500 V2.09** hub servo motor (6.5 in) | 48 VDC; **max load 200 kg per 2 sets**; rated torque 10 N.m / peak 30 N.m; rated current 7 A / peak 21 A; 260 rpm rated / 360 rpm max; wheel diameter 165.3 mm; 4096-line encoder; 15 pole pairs; 4.85 kg; IP65 | https://www.zlingkj.com/Data/zlingkj/upload/file/20250212/ZLLG65ASM500%20V2.09.pdf (from https://www.zlingkj.com/robot-hub-servo-motor-series/539592) | VERIFIED-FETCHED |
| ZLTECH ZLLG80ASM250-4096 V2.18 (8 in) | 24 V; 6 N.m rated / 18 N.m peak; 160 rpm rated / 205 rpm peak; 6 A / 18 A; dia 200 mm; IP65. No load rating on the drawing | https://www.zlingkj.com/Data/zlingkj/upload/file/20250212/ZLLG80ASM250-4096%20V2.18-20240808.pdf | VERIFIED-FETCHED |
| ZLTECH ZLAC8030L driver | 24-48 VDC, CANopen (CiA301/402)/RS485, 4 programmable isolated inputs (enable/start-stop/**e-stop**/limit), brake output. **No STO or SIL/PL rating mentioned** (only a programmable e-stop input) | https://www.zlingkj.com/robot-hub-servo-motor-series/933617 | VERIFIED-FETCHED |
| Roboteq STO controllers | Could not fetch www.roboteq.com (timeout / no connection) | - | UNVERIFIED |
| Sizing sanity (inference) | Robot of about 90 kg superstructure + about 50-70 kg chassis + battery is roughly 150-170 kg. With 4x ZLLG65ASM500 (2x 200 kg per pair) the motors are rated for about 400 kg, a margin of about 2.4x. The safety concept would be: PNOZ → STO-capable drive, or PNOZ cuts the motor bus through safety contactors plus a brake | - | inference |

---

## Notes relevant to the 85-95 kg, high-CoG superstructure

- Only AgileX gives an explicit payload CoG rule: the centroid must be at the centre of rotation, with no height limit stated. The other vendors' fetched pages give no CoG height limit. MiR and Robotnik limits would have to come from their user guides (not fetched; UNVERIFIED).
- Tip-over check (inference, not sourced). On a 500 mm track Ranger Mini 3.0, take a 95 kg payload with CoG about 0.345 + 0.45 = about 0.8 m above the floor. Combined with the 75 kg base it gives a lateral static margin of half-track / h_cog, roughly 0.25 / 0.5 m, so tolerable deceleration is about 0.5 g before quasi-static tip. That is OK for normal driving but tight under E-stop braking with arms extended. A wider base (MiR250 580 mm, KAIROS 633 mm body, Ridgeback 793 mm) helps.
- **Safety-stop compatibility with SICK nanoScan3 + Pilz PNOZ:**
  - MiR250: already has 2x nanoScan3 and a safety PLC, plus 1 auxiliary E-stop input to connect a PNOZ output or E-stop.
  - Robotnik: safety LiDARs + safety PLC included; external E-stop wiring needs to be confirmed with Robotnik.
  - Ridgeback: only a 3.3 V latching motion-stop header (not safety-rated).
  - AgileX Ranger Mini/Tracer: nothing external. You would interrupt motor power yourself, which is not a documented interface.
- **Auto-docking:** MiR (VL-marker docking) and Robotnik (charging station included) are verified. Not found for Ranger Mini 3.0 or Ridgeback.

## URLs that failed

| URL | Result |
|---|---|
| https://global.agilex.ai/products/ranger-mini-3-0 | 404 (working: https://global.agilex.ai/products/ranger-mini-3 and /products/ranger-mini) |
| https://docs.agilex.ai | no connection |
| https://www.agilex.ai/chassis/11 | 404 |
| https://www.generationrobots.com/en/404092-ranger-mini-30-agilex.html | 410 Gone |
| https://mobile-industrial-robots.com/mir250 | 404 (working: /products/robots/mir250 and /products/robots/mir250/specifications) |
| https://mobile-industrial-robots.com/products/robots/mir100/specifications | 404 (MiR100 not listed) |
| https://mobile-industrial-robots.com/products/accessories/mir-charge-48v, .../mir-charge-24v, .../mir250/accessories, .../mir250/top-modules | 404 |
| https://robotnik.eu/products/mobile-robots/rb-kairos/ , .../rb-kairos-2/ , /products/mobile-manipulators/rb-kairos/ | 404 (working: https://robotnik.eu/rb-kairos-2-2/) |
| https://robotnik.eu/products/mobile-robots/rb-vogui-en/ | not tried separately; .../rb-vogui/ works |
| https://robotnik.eu/products/mobile-robots/rb-1-base/ | returned RB-THERON content (redirect/merge) |
| https://clearpathrobotics.com/ridgeback/ | not needed; the indoor-platform page worked |
| https://go.pardot.com/.../RIDGEBACK_Data_Sheet_2020.pdf | HTML wrapper; real PDF at storage.pardot.com (worked) |
| https://docs.clearpathrobotics.com/docs/robots/indoor_robots/ridgeback/... | 404 (working path: /docs_robots/indoor_robots/ridgeback/...) |
| https://www.roboteq.com (and /products, /all-products) | timeout / no connection |
| https://www.zlrobotmotor.com (http and https) | **domain now redirects to an unrelated game-download site (gpangplay.com); do not use**. Official ZLTECH site is https://www.zlingkj.com |
