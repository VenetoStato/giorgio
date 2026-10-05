# Giorgio: mobile base decision (2026-10-05)

**Decision: Slamtec Poseidon, Standard Edition** (not the Hot-Swap Edition, which has no automatic charging).
This choice is **conditional** on Slamtec's written answers (`cad/SLAMTEC_REQUEST.md`): the dock, the price, and the
output while docked are not published anywhere.

Official sources saved in `docs/fonti/`:
- `Slamtec_Poseidon_Standard_datasheet_v1.2.1-260904.pdf` (sha256 81aae2ca…aa01), from
  https://bucket-download.slamtec.com/e493fe88f66be4afe2f4ad652f7e2b7a4766ce7f/EN%20SLAMTEC%20Poseidon%20Standard%20Edition_datasheet_v1.2.1-260904.pdf
- `Slamtec_Poseidon_HotSwap_datasheet_v1.2.1-260904.pdf` (sha256 9d5c642a…5f17), from
  https://bucket-download.slamtec.com/ff55bac6074f0648771f5043c5597dd5bf566db0/EN%20SLAMTEC%20Poseidon%20Hot-Swap%20Edition_datasheet_v1.2.1-260904.pdf
- Web pages: https://www.slamtec.com/en/poseidon/spec and https://www.slamtec.com/en/poseidon

## 1. The three requirements against Poseidon Standard

| Requirement | Official text (Standard datasheet v1.2.1, 2026-09-04) | Status |
|---|---|---|
| (1) Payload ≥ 85 kg | "Rated Payload 150kg (Max. payload 200kg)" | **CONFIRMED** (+65 kg margin on the rated value) |
| (2) Automatic charging | "Charging Method: Automatic / Manual" | **CONFIRMED** as a charging method. The dock product (part number, datasheet, price, contacts, power) is **NOT PUBLISHED** |
| (3) Power for Giorgio | "Power Output Interface: 48V 30A (rated)"; battery "Rated 30A; continuous max. 50A; instantaneous peak 110A" | **CONFIRMED** at 1.44 kW rated output (covers 1.24 kW sustained, or the ~370 W needed to charge Giorgio's pack). **2.1 kW for 5 s at the connector: NOT CONFIRMED** (that needs 44 A, above the 30 A rated output) |

Hot-Swap Edition: "Charging Method: Hot-swappable (battery swap), Manual charger". **No automatic charging.** Do not order it.

The other datasheet values were also read directly: 570 × 520 × 320 mm, 80 kg, LFP 48 V 30 Ah, more than 8 h at full payload, less than 3 h charge (0–80 %), stop accuracy ±20 mm / ±1°, RJ45 + Wi-Fi, and RS485/CAN (reserved). The web page claims "native ROS/ROS2 support and a mature SDK", 4-wheel independent steering, and an anti-tip coefficient of 1.65 at 1.8 m total height. Launch and pre-orders opened in June 2026 (press, Chinese).

### What is NOT confirmed (questions in `cad/SLAMTEC_REQUEST.md`)
1. The charging dock: product, price, method, power, contact position on the robot.
2. Whether the 48 V output stays live **while docked and charging**.
3. Peak current allowed at the output connector.
4. External safety input / STO, and certifications.
5. Allowable CoG height with 85 kg.
6. Price and lead time.

## 2. Commercial alternatives checked (official sources)

| Base | (1) Payload | (2) Auto-charge, maker-confirmed | (3) Power out | Price | Verdict |
|---|---|---|---|---|---|
| **Slamtec Poseidon Standard** | ✔ 150 kg | ✔ datasheet (dock not documented) | ✔ 48 V 30 A rated | not published | **chosen** |
| Slamtec Poseidon Hot-Swap | ✔ 150 kg | ✖ swap + manual charger only | ✔ 48 V 30 A (max 110 A) | not published | ✖ |
| Robotnik RB-THERON | ✔ 200 kg (Robotnik datasheet via distributor) | ✔ "Charging station: Included" (robotnik.eu) | ? "12V / 24V / VBATT", currents not published | €25,950 (distributor) | 2nd choice, ask currents |
| MiR250 | ✔ 250 kg | ✔ MiR Charge 48V (up to 1.9 kW) | ✖ 48 V 10 A (≈480 W) top-module power (spec v2.81); removed from spec v2.99 | not published | ✖ power, 800 mm long |
| OMRON LD-250 | ✔ 250 kg | ✔ docking station in the manual | ✖ 24 V; ≈460 W while driving | not published | ✖ 24 V, 963 mm, end of production announced (unverified) |
| Neobotix MPO-500 (250 kg option) | ✔ | ✔ automatic charging station in the manual | ✖ 24 V terminals, 5 A fuse | not published | ✖ power |
| AgileX Ranger Mini 3.0 (previous) | 120 kg (old project data) | ✖ not on the product page (hot-swap only); "automatic charging" appears only for the Modular ALOHA system | 48 V ≤ 15 A / 720 W | €12,480 (distributor) | ✖ requirement 2 |
| AgileX Ranger Air | ✖ 80 kg | sentence on the product page only; the dock appears only at a distributor (24/48 V, 5–10 A) | 24 V 600 W | not published | ✖ |
| Slamtec 48V Hermes | ✖ 50 kg rated | not on the spec page | 48 V 30 A | — | ✖ |

## 3. Open projects
No open project satisfies all three requirements as a finished product. The full table is in §5.

## 4. Estimated total BOM (barista configuration, EUR excl. VAT, parts only)

| Section | EUR | Note |
|---|---|---|
| A. Mobile base: Poseidon Standard | **12,000–20,000 (est.)** | price not published; estimate placed between the Ranger Mini (€12,480) and the RB-THERON (€25,950) |
| J. Charging dock | **1,500–3,000 (est.)** | not published; references: Stretch dock $1,495; contact dock + 48 V charger DIY ≈ €1,000 |
| B. Arms (OpenArm 2.0 bimanual) | 5,950 | |
| C. Compute, perception, comms | 1,535 | |
| D. Face and UI | 72 | |
| E. Coffee backpack | 290 | |
| F. Power (48 V 1.44 kWh pack, DC-DC, Orion-Tr 48/48 charger fed from the base output) | 2,602 | |
| G. Safety (2× nanoScan3 Pro, PNOZ) | 5,745 | |
| H. Wiring | 187 | |
| I. Shells PA12 | 971 | |
| K. Structure | 1,930 | the base adapter plate (P01) must be redrawn for the Poseidon deck |
| L. Fasteners | 107 | |
| **Total** | **≈ €32,900 – €42,400** | **central estimate ≈ €36,400** (base €15k + dock €2k) |
| Assembly + test labour (35 h) | +1,750 | optional |

Previous total with the Ranger Mini: €31,869 (without a dock, which was not available). Everything except the base and
the dock is unchanged from `docs/bom.csv`.

## 5. Open-source options
Labels: ✔ satisfied, ✖ not satisfied, ? not documented.

| Project | Open (licence) | (1) Payload | (2) Auto-charge on real hardware | (3) Power out | Cost | Verdict |
|---|---|---|---|---|---|---|
| **Husarion Panther** | software Apache-2.0, CAD MIT; electronics not open | ✔ "max carrying capacity: 120 kg" | ✔ WiBotic wireless + AprilTag + Nav2 docking, but the charger is only **200 W** (42 V 5 A) | ✖ "User Power Ports … up to 780 W" at 32–42 V (36 V Li-ion, 720 Wh) | €17,900 + wireless kit (quote) | closest open-software option; fails (3) and recharges too slowly for Giorgio |
| **OpenAMRobot / OpenAMR** | hardware CERN-OHL-P-2.0, software MIT | "up to 150 kg" (README, not tested) | ✖ docking "tuned in simulation", real robot "in progress"; no dock design | ✖ 24 V, no payload port | BOM not published | the only truly open hardware; not ready |
| Ubiquity Magni Silver | ROS 2 software open; hardware not open | ✔ 100 kg | ✔ WiBotic 300 W (partner) | ✖ 5 V / 12 V only | $4,995 | ✖ |
| ROMR (hoverboard) | GPL-3.0 | 90 kg max | ✖ | ✖ | < $1,500 | ✖ |
| Mobile ALOHA (AgileX Tracer) | open software; base closed | ✔ | ✖ | separate 1.26 kWh battery | ~$32k complete | ✖ |
| TidyBot++ | open BOM/CAD | ✖ 60 kg | ✖ | 768 Wh power station | $5–6k | ✖ |
| AhaRobot, XLeRobot, Bracket Bot, Nori | open | ✖ light | ✖ | ✖ | $0.5–1.8k | ✖ |
| Wheeltec EC130, Leo Rover, Stretch docks | open docks (various licences) | n/a | ✔ but 3 A at 12–25 V | n/a | €380–500 | small-dock references only |

Open software that can be used on any base: Nav2 Docking Server (Apache-2.0, SimpleChargingDock, charge detected
from `BatteryState`), neo_docking2 (Neobotix).

**Open DIY base (estimate, not validated):** 2× ZLTECH 48 V 800 W hub motors (~$430), ZLAC8030L driver (~$150),
51.2 V 50 Ah LFP 2.56 kWh (~$500), 58.4 V 30 A charger in the dock (~$210), 100 A AGV brush contacts (~$148), Victron
Orion-Tr 48/48-8 (~$203), lidar (~$65). Total ≈ **$1.7k** for the priced parts, **≈ $2.1–2.6k** with frame, safety and
wiring. Meets all three requirements on paper, but nobody "confirms" anything: no maker, no CE, and we would design the
dock and the safety ourselves.

Sources for §5: https://husarion.com/manuals/panther/overview/ (fetched 2026-10-05), https://store.husarion.com/products/panther,
https://husarion.com/tutorials/ros-equipment/wch01-02/, https://github.com/openAMRobot/openamr-platform-hw,
https://github.com/chrswp/open_amr, https://www.ubiquityrobotics.com/product/magni-silver/,
https://github.com/LinusNEP/ROS-Mobile-Robot, https://tidybot2.github.io/, https://arxiv.org/abs/2401.02117,
https://docs.nav2.org/configuration/packages/configuring-docking-server.html.

## 6. Lessons from similar robots (wheeled torso + arms)
- Integrated products run everything from one pack: KUKA KMR iiwa ("Li-Ion battery pack for the whole system"), Franka
  Mobile FR3 Duo, Rainbow RB-Y1, Galaxea R1. Robots bolted onto a third-party base hit the base's port limit: MiR250
  480 W, OMRON LD 40 A at 24 V. This is why Giorgio keeps its own pack.
- Charging power: MiR Charge 48V up to 1.9 kW; KUKA/Wiferion 3 kW inductive. Giorgio at 1.24 kW sustained needs a fast
  dock plus opportunity charging between tasks.
- Docking tolerance: ±5 mm (KUKA) to ±20 mm (Poseidon). Use floating or sprung contacts, and re-localise the arms with
  vision after every stop (OMRON "Landmark").
- Safety interlock (Neobotix MM): the arm is enabled only while the base is stationary, and the base drives only with
  the arm in its home pose.
- The pack goes as low as possible, as ballast (Mobile ALOHA).
