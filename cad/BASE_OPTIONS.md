# Giorgio — base options (AgileX only), payload certainty, self-charging

> **DECISION (owner, 2026-10-03): AgileX RANGER AIR**, the base whose automatic recharging is confirmed on the manufacturer's page.
> The CAD has been rebuilt on it and fully re-validated: 55 PASS / 17 WARN / 0 FAIL, superstructure + product payload **59.3 kg = 74 % of 80 kg**.
> See section 0 below and README / VALIDATION.md. Sections 1–6 are the comparison that led there; their Giorgio numbers refer to the Tracer-era model (git 2660c92).

## 0. Ranger Air — chosen base (data: manual V1.0.0 2026-01-25, product page, ROS ranger_ros air_delta, Generation Robots)

| Item | Value | Status |
|---|---|---|
| L × W × H | 552 × 500 × 250 mm (deck = flat top plate at ≈ 250) | SOURCED / deck height EST |
| mass / payload | 50–55 kg / **80 kg**; payload CoG at the rotation centre | SOURCED |
| wheels | wheelbase 388 × track 338 mm (ROS 0.39 × 0.34), Ø ≈ 122 solid, 4WD/4WS: spin, crab, Ackermann | SOURCED / Ø EST |
| top interface | 8 tapped holes, grid 200 (y) × 80 (x) pitch; thread not given | SOURCED drawing / thread ASSUMED M6 |
| speed / slope / obstacle | 1.5 m/s / 8° / 10 mm; **braking/decel not published** | SOURCED |
| battery | LFP 24 V 30 Ah (0.72 kWh), 10 A charger, 3 h; runtime 6.5 h empty / 2.5 h full load | SOURCED |
| expansion power | rear 4-pin: 24–29.6 V, ≤ 25 A, ≤ 600 W total (the plug table says 23–26.5 V, 10 A: conflict); cut below 10 % SOC; no 12/5 V | SOURCED (conflicting) |
| safety | rear mushroom e-stop, CAN status bit; **no external stop input** | SOURCED |
| auto-charging | product page: "automatic recharging". Manual drawings: **contact "charging brush plate" at the rear face centre** (≈ 137 mm wide, z ≈ 115–180). Station photo: wall box at floor level with a marker. Alignment, NAVIS or navigation-version requirement, price: **UNVERIFIED** | SOURCED claim / geometry EST |
| price | €3,700 (standard) / €5,600 (navigation: 2 lidars + depth camera) excl. VAT, Generation Robots | SOURCED (distributor) |

**Giorgio on the Ranger Air (validated CAD)**
- Robot 104.2 kg; superstructure 54.2 kg; + product payload (2 × 1.5 + 2.1 kg) = **59.3 kg ≤ 64 kg target**.
- Extension CoG (−17.7, 0.2, 788) mm.
- Tipping (m/s², fwd/back/left/right): nominal 4.40/3.83/3.58/3.59, worst 3.43/4.34/3.38/3.39. These need software acceleration limits ≤ 1.5 m/s².

**Power architecture for the electrical lead.** Everything runs from the base battery at 24 V:
- OpenArm bus direct, through the PNOZ-switched contactors;
- 24→19 V for the Jetson module;
- 24→5 V for cameras and LEDs;
- a ≤ 2 kg 24 V LFP buffer behind an ideal diode for arm peaks above 600 W;
- an arm power cap in software.

The AgileX station then charges the single base battery: one dock charges everything.


Date 2026-10-03. Owner constraints:
- MiR is rejected (closed system, subscriptions).
- We must be **sure** about the payload.
- **Autonomous self-charging on the base manufacturer's own charging station** is mandatory. There is no custom dock of ours, so the RoboPad collector and the nose contacts come out of the design.

Hot-swap batteries are not a criterion. Sources: official AgileX manuals and pages fetched today. Labels used below:
- VERIFIED: read in a fetched document.
- (drawing): a dimension printed on an official drawing; how it was read is ours.
- UNVERIFIED: not found.

The URLs are at the end. Numbers for our robot come from `base_options.py`: the same static method as `validate.py`, applied to the validated Tracer design, with results in `out/base_options.json`.

## 1. Base data

| | TRACER 2.0 | RANGER MINI 3.0 | RANGER (full) | RANGER AIR | UMR |
|---|---|---|---|---|---|
| L × W × H (mm) | 702 × 610 × 169 | 720 × 500 × 345 (top of rails) | 1228 × 876 × 475 (table); drawing: 1302 long, rails top ≈ 536 — **conflict** | UNVERIFIED | 830 × 540 × 410 |
| own mass | 54–56 kg | 75 kg | "100 kg curb" and "135 kg single battery" — **conflict** | UNVERIFIED | 90 kg |
| payload (manual) | **100 kg** (web 80 / datasheet 150) | **120 kg** | **150 kg** | 80 kg | 70 kg |
| payload CoG rule | at centre of rotation, no height limit | same | same | — | — |
| wheel contact polygon (x × y) | ≈ ±281 × ±255 (casters, ESTIMATE as in the sim) | **494 × 364 mm** (ROS params + drawing; AgileX's table labels swapped) | **890–900 × 560 mm** | UNVERIFIED | UNVERIFIED |
| base CoG height | ESTIMATE 80 mm | **213 mm** (manual Fig 2.2) | UNVERIFIED (250 assumed) | — | — |
| top rails | 2 rails 230 mm apart, ≈ 561 long | 2 T-slot rails 230 mm apart (drawing), 16 mm tall, ≈ 675 long (scaled) | 2 rails **380 mm** apart, 1200 long, 16 mm tall (drawing) | T-slot rails | — |
| speed | 2.0 m/s | 2.0 m/s (ROS driver caps 1.5) | 2.6 m/s | — | 1.5 m/s (5.4 km/h) |
| braking / max decel | 0.9 m from 2 m/s empty (≈ 2.2 m/s²) | **not stated** | **not stated** | — | — |
| slope / obstacle | 8° / 10 mm | 15° (at 25 kg) / 120 mm gap | 10° / 100 mm step | — | — |
| battery | LFP **24 V** 30 Ah | LFP **48 V 24 Ah** (1.15 kWh) | LFP **48 V 24 Ah per pack**, up to 4 | LFP **24 V** 30 Ah | LFP 48 V 24 Ah |
| accessory output | 24 V, **≤ 5 A / 120 W** | 46–50 V, **≤ 15 A / 720 W**, cut < 10 % SOC | 46–50 V, **≤ 15 A / 720 W** | 24–29.6 V, **≤ 25 A / 600 W** | ≤ 15 A / 720 W |
| peak accessory power | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| external safety-stop input | **none** (onboard e-stop only) | **none** (CAN status bit only) | **none** | UNVERIFIED (likely none) | UNVERIFIED |
| **OEM self-charging dock** | **no evidence.** The "automatic recharging" text on /products/tracer-2-0 is pasted Ranger Air copy; the real Tracer page and the manual have none | **indirect**: Modular ALOHA (built on Ranger Mini 3.0) is sold "with an auto-return charging pile"; the NAVIS page lists Ranger Mini 3.0 | **no evidence** (NAVIS page: "compatible with the full range of AgileX bases") | **yes** (product page: "automatic recharging"; the manual says nothing) | **yes** (manual mentions "the automatic charging pile") |
| dock details | — | AgileX "autonomous charging kit"; NAVIS API calls the dock a "wireless charging pile"; example 54.9 V / 10.9 A. Contact type and position, alignment tolerance, robot-side kit, price: **UNVERIFIED** | — | same kit (assumed) | same kit |
| docking software | — | **NAVIS** stack (`/find_charger/*` over rosbridge); no docking in the open ranger_ros2 | — | NAVIS | NAVIS built in |
| price (excl. VAT) | ≈ 7.5 k€ (project BOM) | **€12,480** (Generation Robots) | **€19,760** (Generation Robots) | UNVERIFIED | UNVERIFIED |

The "€835 AgileX charging station, 24/48 V, 5–10 A" in our earlier documents was **not found in any source** and is UNVERIFIED.

## 2. Giorgio on each base (static, same method as VALIDATION.md)

"Superstructure + payload" includes the 2.1 kg tray content and 2 × 3 kg handled objects. Tip accelerations are fwd / back / left / right in m/s².
The 0.5 g target is 4.9 m/s². The e-stop requirement is ≥ 2.2 m/s² (Tracer data; the Rangers publish no braking value).

| Configuration | Superstr. + payload (kg) | Limit / margin | Nominal | Work (2 × 4.1 kg) | Worst (arms fwd, 2 × 6 kg) |
|---|---|---|---|---|---|
| **Tracer 2.0**, both modules, own 48 V pack, column 150 mm stroke (validated design) | **88.8** | 100 / 11.2 (11 %) | 7.03 / 7.16 / 6.42 / 6.46 | 6.05 / 6.94 / 5.88 / 5.91 | 4.41 / 6.75 / 5.05 / 5.08 (lift 150) |
| Tracer 2.0, barista config (no chest tray) | 84.4 | 100 / 15.6 | 7.55 / 7.38 / 6.75 / 6.79 | | 4.67 / 6.94 / 5.25 / 5.28 |
| Tracer 2.0, logistics config (no coffee module) | 82.5 | 100 / 17.5 | 7.02 / 7.77 / 6.68 / 6.74 | | 4.24 / 7.15 / 5.14 / 5.18 — CoG +24 mm, rebalance |
| **Ranger Mini 3.0**, powered from the base battery (our pack, tray, charger and RoboPad removed), column shortened 176 mm (**fixed height**, shoulders kept at 1.278 m) | **70.7** | 120 / **49.3 (41 %)** | 5.53 / 4.93 / **3.86 / 3.86** | 4.84 / 4.97 / 3.61 / 3.61 | 3.80 / 5.39 / **3.39 / 3.39** |
| Ranger Mini 3.0, same, barista | 66.3 | 120 / 53.7 | 5.88 / 4.98 / 4.00 / 4.00 | | 4.00 / 5.47 / 3.49 / 3.49 |
| Ranger Mini 3.0, own pack kept, superstructure simply raised 176 mm | 88.4 | 120 / 31.6 | 4.77 / 4.82 / 3.52 / 3.54 | 4.19 / 4.78 / 3.29 / 3.32 | 3.19 / 4.85 / 2.95 / 2.97 |
| **Ranger**, base battery, no column (body_link0 on a 44 mm spacer, shoulders kept) | **68.0** | 150 / **82 (55 %)** | 9.63 / 9.16 / 5.85 / 5.85 | 8.81 / 8.96 / 5.53 / 5.53 | 7.69 / 9.11 / 5.23 / 5.23 |

Notes on the Ranger rows:
- The Ranger rows with the base battery leave the extension CoG at x ≈ −30 mm, because the battery that went away sat in front. The electronics or the coffee module must be moved forward to get back within ±20 mm. That is feasible: 10 kg moved 90 mm.
- Ranger Mini lateral stability (3.4–3.9 m/s², 0.35–0.39 g) comes from its **364 mm track**. It is above the e-stop value but **below 0.5 g**, so cornering limits are needed (lateral acceleration ≤ 0.2 g at full height).
- Ranger (full) uses 100 kg base mass at an assumed 250 mm CoG height (not published). With 135 kg the margins would be better.

## 3. Option A — stay on Tracer 2.0, superstructure + payload ≤ 80 kg

From 88.8 kg we need −8.8 kg.

| Measure | kg | Function impact | Certainty |
|---|---|---|---|
| One task module at a time: barista = no chest tray (tray + carrier + its payload) | −4.4 | No kitting while in barista mode. The tray is already quick-release (2 pins + plunger); the swap takes ~2 min | sure (CAD masses) |
| … or logistics = no coffee module | −6.3 | No coffee in logistics mode; swap takes ~15 min (7 bolts + cable). Re-centre the CoG (+24 mm) | sure |
| Battery 15s 30 Ah → 15s 20 Ah (0.96 kWh, ≈ 9 kg) | −4.0 | Runtime 5.2 → ≈ 3.5 h at 250 W | ESTIMATE pack mass. The electrical lead must check: cells ≥ 2C continuous (40 A) for the 1.0–1.4 kW peaks, BMS current limit, charge ≤ 1C (20 A) from the dock, cycle life with more opportunity charging |
| Jetson AGX Orin dev kit → module on a compact carrier | −1.0 | none if the carrier has the IO; thermal design to redo | UNVERIFIED masses |
| 48→24 V Tracer charger, smaller unit | −0.7 | none | UNVERIFIED |
| Shells 2.0 → 1.6 mm (skirt 2.5 → 2.0) | −1.0 | Stiffness: needs ribs; prototype test | computed from CAD volumes; stiffness not verified |
| Hollow foam bumper profile | −0.6 | none | ESTIMATE |
| Adapter plate further pocketing (6.0 → 4.5 kg) | −1.5 | none, after FEA | ESTIMATE, needs FEA |
| Wiring allowance 3.0 → 2.0 kg after harness design | −1.0 | none | UNVERIFIED until the harness exists |
| Fixed-height column (no sleeve, clamps or liners) | −1.6 | **Loses the manual height adjustment** | sure |

Is ≤ 80 kg reachable without losing a function?
- **Both modules at once: no.** The sure measures give 88.8 → 83.0 kg. Only the 20 Ah battery (runtime −33 %) brings it to ≈ 79 kg.
- **One module at a time: yes on paper.** Barista 84.4 − 5.8 = **78.6 kg**; logistics 82.5 − 5.8 = **76.7 kg**. But ~3.5 kg of the 5.8 kg are unverified estimates. It is **not "sure"** until parts are weighed.
- Under the owner's self-charging rule **Option A is moot anyway.** There is no documented OEM dock for the Tracer. Its 24 V / 120 W accessory output can neither power nor recharge our 48 V superstructure pack: 1.44 kWh at 120 W is about 12 h.

## 4. Self-charging and power architecture per base (owner: OEM dock only)

| | Tracer 2.0 | Ranger Mini 3.0 | Ranger | Ranger Air |
|---|---|---|---|---|
| OEM dock | none documented → **disqualified** | AgileX kit via NAVIS (system-level evidence) → **qualifies pending datasheet** | none documented → qualifies only if AgileX confirms the kit fits | documented on the product page → qualifies |
| Superstructure power | impossible from the base (120 W) | **from the base: 46–50 V, ≤ 15 A / 720 W continuous** | same 720 W | 24 V ≤ 25 A / 600 W |
| Our typical load (≈ 250 W: arms 100–150, Jetson 30–40, scanners 8, PNOZ 6, cameras/LEDs ≈ 10) | — | OK | OK | OK |
| Our peaks (arms ≈ 720 W, Jetson 60, coffee) | — | **exceed 720 W** → arm power limit or a small buffer (e.g. 48 V 5 Ah LFP or supercap, ≈ 2–3 kg) behind an ideal diode; no 230 V coffee machine possible | same | exceed 600 W; but the arms are 24 V, so no 48→24 V DC-DCs (−2.75 kg) |
| Runtime | — | 1.15 kWh shared with traction: ≈ 3–4 h (estimate) + opportunity charging on the dock | up to 4 packs (4.6 kWh) | 0.72 kWh: ≈ 2 h (estimate) |
| Payload margin with base power | — | 49 kg (41 %) | 82 kg | 80 kg limit → 70.7 kg = 9 kg (11 %): **not enough for "sure"** |

## 5. Mechanical changes when moving off the Tracer and dropping our dock

- **Removed:**
  - S03 RoboPad collector, P10 bracket, 2 × M6 + 4 × M4 bolts, the skirt nose window.
  - Base powered: battery pack E01, tray P03, pad P04, hold-downs P05, Tracer charger E09.
- **Added:** the OEM dock receiver from AgileX's kit. Position unknown (possibly a wireless coil at the bottom/rear). The skirt needs an opening or a non-metallic window there — **wait for the kit drawing**.
- **Adapter plate:** Ranger Mini rails are 230 mm apart like the Tracer's, so the P01 bolt pattern can be reused on a narrower outline. The Ranger needs a new P01 for its 380 mm rail spacing.
- **Column:**
  - Ranger Mini: the deck is 176 mm higher. Keeping the validated shoulder height (task reach, coffee poses) means a fixed column with no stroke, or raising the shoulders 176 mm and re-solving reach in the sim.
  - Ranger: the deck is at 536 mm. body_link0 sits almost directly on P01 (44 mm spacer), with no column.
- **Scanners:** the scan plane must stay at ≈ 180 mm (ISO 3691-4 lying test piece).
  - Ranger Mini: the body spans 105–329 mm with four steering wheels near the corners. The scanners must hang **outside the 720 × 500 body** at the corners or the front/rear, which grows the footprint (≈ 830 × 620, estimate).
  - Ranger: ground clearance 190, body up to 520. Same issue; the footprint is already 1228 × 876.
- **Skirt:** a new shell per base. The Ranger Mini needs wheel-steering clearance; the 4WS wheels swing ±90°.

## 6. Recommendation

**(i) Prototype**
- Keep developing on the **Tracer 2.0 already in the design** for lab work. Its mass and CoG are validated: 88.8 kg ≤ 90 kg, 11 % margin to the manual's 100 kg; ≥ 20 % margin in single-module configurations with the sure measures.
- Charge it manually. It **does not meet the self-charging requirement** and cannot get it from AgileX.
- In parallel, order a **Ranger Mini 3.0 + AgileX auto-charging kit (NAVIS)** as soon as AgileX confirms the kit datasheet and price for Ranger Mini 3.0 (AGILEX_REQUEST.md).

**(ii) Product: RANGER MINI 3.0, powered from its own 48 V battery**, conditional on AgileX's written answers. Why:
- 120 kg payload with a 41 % margin;
- an AgileX self-charging dock exists at system level;
- 48 V matches our DC-DC inputs (Mean Well DDR-480C: 33.6–67.2 V);
- €12.5k;
- footprint close to the current robot.

Conditions:
- cornering and braking limits for its 364 mm track;
- a peak-power buffer or arm power limit for the 720 W output;
- fixed-height column;
- scanner pods outside the body;
- confirm its braking deceleration loaded.

The **RANGER** is the fallback if AgileX confirms the charging kit for it. It has the best stability (≥ 5.2 m/s² in every case) and the largest margin (55 %), but it is a 1.23 × 0.88 m machine at €19.8k.
Ranger Air (80 kg) and UMR (70 kg) are excluded: no sure payload margin.

**Remaining uncertainties (all in AGILEX_REQUEST.md)**
- Dock / kit datasheet: contact or wireless, current, alignment, receiver position, price; whether the payload may stay powered while docked.
- Payload with our CoG height.
- Braking deceleration loaded.
- Peak accessory power.
- External safety-stop input: **none of the AgileX bases documents one.** The EN ISO 3691-4 stop of the drive therefore stays an open certification issue for every AgileX option.
- Ranger mass and height conflicts in the manual.
- Centre-of-rotation position on the Tracer.

## Sources (fetched 2026-10-03)

- TRACER 2.0 manual: https://cdn.shopify.com/s/files/1/0551/0630/6141/files/TRACER_2.0_User_Manual.pdf?v=1773112702 ; pages https://global.agilex.ai/products/tracer-2-0 (contains pasted Ranger Air text), https://global.agilex.ai/products/tracer-2-0-indoor-robot-smart-logistics
- RANGER MINI 3.0 manual: https://cdn.shopify.com/s/files/1/0551/0630/6141/files/RANGER_MINI_3.0_User_Manual.pdf?v=1773112703 ; ROS params https://raw.githubusercontent.com/agilexrobotics/ranger_ros2/humble/ranger_base/include/ranger_base/ranger_params.hpp ; price https://www.generationrobots.com/en/404051-ranger-mini-mobile-robot-ugv.html
- RANGER manual V2.0.2: https://cdn.shopify.com/s/files/1/0551/0630/6141/files/RANGER_User_Manual.pdf ; price https://www.generationrobots.com/en/404081-mobile-ranger-4ws-4wd-robot.html ; page https://global.agilex.ai/products/ranger
- RANGER AIR: page https://global.agilex.ai/products/mobile-manipulator ; manual https://cdn.shopify.com/s/files/1/0551/0630/6141/files/RANGER_AIR_USER_MANUAL_AgileX_Robotics.pdf?v=1788332629
- UMR manual: https://cdn.shopify.com/s/files/1/0551/0630/6141/files/UMR_USER_MANUAL_-_AgileX_Robotics_Universal_Mobile_Robot.pdf?v=1788332754
- Modular ALOHA (Ranger Mini 3.0 + auto-return pile): https://global.agilex.ai/products/modular-aloha , https://www.agilex.ai/product/69a91e590a52fd338d02b22b
- NAVIS (supported bases, automatic charging): https://www.agilex.ai/industry/69cceba6f70ae516ed948dff ; API https://raw.githubusercontent.com/agilexrobotics/Navis/master/user_api.html
- AgileX shop catalogue (no dock product): https://global.agilex.ai/products.json?limit=250
- Full research notes: SOURCES.md and BASE_DECISION.md (earlier MiR/Robotnik comparison, now superseded by the owner's decision).
