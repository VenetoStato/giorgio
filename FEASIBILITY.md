# Giorgio: feasibility and software-access review

**Date checked:** 2026-10-03. Repo activity and releases come from the GitHub API on that date. Prices are EUR excl. VAT. A price marked "est." is an estimate, not a quote.
**Scope:** for every part of the v7 BOM (`README.md`, total ~€28,080), can we get SDKs, drivers, source code and licences? If not, what fully accessible part replaces it, and how does the price change?
**Convention:** "unverified" means I could not confirm the point from a primary source during this review.

---

## 1. Overall feasibility verdict

**Feasible. No part blocks the software stack.** Every core part (base, arms, scanners, depth camera, compute) has an open-source driver (Apache-2.0 or MIT), and every repository was active within the last ~2 months. Three areas need action before purchase:

1. **Arm safety architecture (main project risk).** The problem is safety, not software access. Damiao motors have closed firmware, no STO and no brakes. A safe stop therefore means a CAN-commanded controlled stop followed by a hardware power cut, and the arms fall when power is cut. This works for a prototype but is the hardest point for CE.
2. **The Insta360 X4 is the only part with gated, closed software.** The Desktop Camera SDK needs an application to Insta360 and is binary-only. It *does* support Linux aarch64 and a live 1920x960 preview on the X4. The robot does not need it: 2x nanoScan3 already give 360° planar coverage and the Gemini 336L covers the front. **Recommendation:** replace it with 2 plain UVC fisheye cameras. Keep the X4 only if Insta360 grants SDK access.
3. **Missing BOM items.** The 48 V LFP pack with CAN BMS, the CAN-FD adapters, the Pilz comms module and an Ethernet switch are not priced (or are under-priced inside "Cablaggi e alimentazione €600"). **Realistic cost is ~€30,300, not €28,080** (see §5).

**Correction to the brief:** the **nanoScan3 Core I/O DOES output measurement data over Ethernet (UDP/TCP CoLa2)**. The datasheet for NANS3-AAAZ30AN1 lists "Measured data output: Via Ethernet". It works with `sick_safetyscanners2`. Core and Pro I/O differ in I/O count and monitoring cases, not in data output (§3.4).

---

## 2. Component summary table

| # | Component | SDK / driver | Lang | License | ROS 2 | Jetson / ARM64 | Last activity (checked 2026-10-03) | Interface | Risk | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AgileX Tracer 2.0 | [ugv_sdk](https://github.com/agilexrobotics/ugv_sdk) + [tracer_ros2](https://github.com/agilexrobotics/tracer_ros2) | C++ | Apache-2.0 | branches `humble`, `jazzy`, `tracer2.0` | yes (ugv_sdk: x86_64/arm64) | ugv_sdk push 2026-08-11; tracer_ros2 push 2026-07-30; no tagged releases | CAN 2.0B **500 kbit/s**, protocol published in user manual | Low | **KEEP** |
| 2 | 2x Enactic OpenArm 2.0 (Damiao) | [openarm_can](https://github.com/enactic/openarm_can) v1.4.0, [openarm_ros2](https://github.com/enactic/openarm_ros2) 0.9.2, [openarm_description](https://github.com/enactic/openarm_description) 1.0.4, [openarm_mujoco](https://github.com/enactic/openarm_mujoco) 2.3.0 | C++ (Python bindings "unstable/temporary") | Apache-2.0 (hardware CERN-OHL-S-2.0) | Humble recommended; Jazzy "work in progress, may be unstable" | SocketCAN, any Linux; apt packages for Ubuntu 22.04/24.04/26.04 (Jetson not explicitly listed, but nothing x86-specific) | openarm_can 1.4.0 on 2026-09-16; ros2/description/mujoco pushes 2026-10-02 | **CAN-FD** 1 M nominal / 5 M data, 1 kHz | **Med-High** (safety, not access) | **KEEP WITH CAVEAT** |
| 2a | Damiao motor firmware | Damiao Debugging Tool (Windows only), UART 921600 for flashing | binary | closed (proprietary `.bin`) | n/a | n/a | n/a | UART (flash), CAN (run) | Med | caveat: closed |
| 3 | OpenArm parallel gripper | in openarm_can / openarm_ros2 (8th Damiao DM-J4310) | C++ | Apache-2.0 | as above | as above | as above | CAN-FD | Low | **KEEP** (default EE) |
| 4 | ORCA Hand v2 (optional) | [orca_core](https://github.com/orcahand/orca_core) v0.5.2 | Python | MIT; hardware [CC BY 4.0](https://github.com/orcahand/orcahand_hardware) | none official (FastAPI server; ROS 2 wrapper needed) | pure Python + dynamixel-sdk → OK | push 2026-10-01, ~10 contributors | USB-serial (Dynamixel or Feetech, 17 motors) | Med | **OPTIONAL, not in BOM** (assembled $3,500–4,500 per hand) |
| 5 | Pollen AmazingHand (optional) | [AmazingHand](https://github.com/pollen-robotics/AmazingHand) v1.0 | Python / Arduino | Apache-2.0 code, CC BY 4.0 CAD | none official | pure Python → OK | release 2026-04-01, push 2026-04-23 | USB-serial bus to Feetech SCS0009 (8/hand) | Low-Med (low force) | **OPTIONAL** (<€200/hand + driver) |
| 6 | 2x SICK nanoScan3 | [sick_safetyscanners2](https://github.com/SICKAG/sick_safetyscanners2) 1.0.5 + [sick_safetyscanners_base](https://github.com/SICKAG/sick_safetyscanners_base) | C++ | Apache-2.0 | ROS index: Humble, Jazzy, Kilted, Rolling | yes (plain C++/Boost) | push 2026-08-25 | Ethernet UDP + TCP CoLa2; safety: OSSD wired | Low | **KEEP** (prefer Pro I/O, §3.4) |
| 6a | SICK Safety Designer | Windows config tool | — | proprietary (free download: unverified) | — | — | — | Ethernet / USB | Low | needed once per config |
| 7 | Pilz PNOZmulti 2 | **no SDK**. PNOZmulti Configurator (Windows, licensed; licence tiers/price unverified). Status read via Modbus TCP (PNOZ m ES ETH or PNOZ m B1 built-in Ethernet) and/or semiconductor outputs | — | proprietary | none (use generic Modbus TCP, e.g. `pymodbus`) | yes, via Modbus TCP | — | Ethernet Modbus TCP port 502 / 24 V IO | Low-Med | **KEEP WITH CAVEAT** (add comms module) |
| 8 | Orbbec Gemini 336L | [OrbbecSDK_v2](https://github.com/orbbec/OrbbecSDK_v2) v2.10.6, [OrbbecSDK_ROS2](https://github.com/orbbec/OrbbecSDK_ROS2) v2.10.6, [pyorbbecsdk](https://github.com/orbbec/pyorbbecsdk) | C/C++/Python | SDK core MIT + **proprietary "Extension Library" under EULA**; ROS2 wrapper Apache-2.0 | Foxy/Humble/Jazzy (+Lyrical/Rolling per README) | **tested on AGX Orin**, arm64 .deb | both released 2026-09-30 | USB 3 | Low | **KEEP** |
| 9 | Insta360 X4 | Insta360 **Desktop CameraSDK** (by application: insta360.com/sdk/apply). Camera-V2.1.8 released 2026-08-28 | C++ | **proprietary, binary, gated** | none | **Ubuntu 22.04 aarch64 supported** (official docs) | docs repo push 2026-09-08 | USB (libusb "Android mode") | **High** (access + ops) | **REPLACE** (or keep only if SDK granted) |
| 10 | Wrist cams (OpenArm built-in) | presumably UVC (model/resolution **unpublished**: unverified) | — | — | `usb_cam`/`v4l2_camera` if UVC | if UVC, yes | — | USB | Med (unknown part) | **KEEP WITH CAVEAT**; D405 as upgrade |
| 10a | Intel/RealSense D405 (option) | [librealsense](https://github.com/realsenseai/librealsense) v2.58.4, [realsense-ros](https://github.com/realsenseai/realsense-ros) v4.58.4 | C++ | Apache-2.0 | Humble/Jazzy/Kilted | yes (Jetson builds documented) | release 2026-08-30, push 2026-10-02; repo moved to `realsenseai` org after the spin-off | USB 3 | Low | optional upgrade |
| 11 | Jetson AGX Orin 64 GB | JetPack 6.2 (Ubuntu 22.04 → **Humble**) or JetPack 7.2 (Ubuntu 24.04 → Jazzy) | — | NVIDIA proprietary BSP + open userspace | Humble (JP6), Jazzy (JP7.2) | — | Isaac ROS 4.6.0 (2026-08-18) added Orin on JP 7.2; Isaac ROS 5.0.0 (2026-09-21) moves to ROS 2 Lyrical | 2x MTTCAN (CAN-FD capable), GbE/10GbE, USB, 40-pin GPIO | Low-Med | **KEEP** |
| 12 | LED face 32x16 HUB75 P4 | ESP32-S3 + [ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrfaptastic/ESP32-HUB75-MatrixPanel-DMA) (MIT, push 2026-08-16) | C++ (Arduino/IDF) | MIT | via micro-ROS or plain serial | Jetson talks USB-CDC serial | active | USB serial | Low | **KEEP** (use this path) |
| 13 | Coffee machine + shuttle | RP2040/ESP32 + [micro-ROS](https://github.com/micro-ROS/micro_ros_espidf_component) (Apache-2.0) or plain serial protocol | C/C++ | Apache-2.0 | Humble/Jazzy (micro-ROS agent) | yes | micro_ros_espidf push 2026-10-02 | USB serial | Low | **KEEP** (add MCU) |
| 14 | 48 V LFP + CAN BMS | REC Q/ABMS (Victron-compatible CAN, published manual) or Orion BMS 2/Jr 2 (programmable CAN messages) or a CE pack with Pylontech/Victron CAN protocol | — | documented protocol (no code needed: SocketCAN + DBC) | write ~200-line node | yes (SocketCAN) | — | CAN 250/500 kbit/s | Med (not in BOM) | **ADD** |
| 15 | Docking station | Nav2 docking server ([opennav_docking](https://github.com/open-navigation/opennav_docking) `humble` branch; merged into [navigation2](https://github.com/ros-navigation/navigation2) for Jazzy+, Nav2 1.5.2 on 2026-09-16) | C++ | Apache-2.0 | Humble (opennav_docking), Jazzy+ (nav2_docking) | yes | active | contacts + detection (laser ICP/AprilTag) | Med (custom HW) | **KEEP** (custom dock) |

---

## 3. Component notes

### 3.1 AgileX Tracer 2.0: KEEP (Low)
- The user manual says the Tracer 2.0 uses **CAN 2.0B, 500 kbit/s, Motorola byte order**, with the message protocol fully documented. A USB-to-CAN module (gs_usb) ships in the box. Battery: **24 V 30 Ah LFP**, and battery state is readable over CAN. Source: [Tracer 2.0 user manual](https://static.generation-robots.com/media/user-manual-tracer-2-0-agilex-robotics.pdf).
- ugv_sdk lists Tracer as Protocol V2 / CAN / "Active". The ugv_sdk README still lists only "Melodic/Noetic/Foxy/Humble", but tracer_ros2 has a `jazzy` branch.
- **No official Tracer charging dock was found.** `docs/alimentazione_e_certificazione.md` already notes that AgileX docks exist only for Ranger Mini 3.0 / Ranger Air. The product page advertises "automatic recharging", so ask AgileX for the part number and price (unverified).
- Risk: the manual states it has **no obstacle-avoidance sensor** and that safety is the integrator's job. This is expected; our scanners and PNOZ cover it.

### 3.2 OpenArm 2.0 + Damiao: KEEP WITH CAVEAT (Med-High)
- **Software access is good.** The whole stack is Apache-2.0: CAN library, ros2_control hardware interface, bimanual MoveIt config, URDF/MJCF, Isaac Lab, teleop and LeRobot/Dora integration. Releases are recent (openarm_can 1.4.0 on 2026-09-16) and the repos are very active.
- **CAN-FD:** default 1 Mbit/s nominal, 5 Mbit/s data, 1 kHz; classic CAN 2.0 fallback (`--no-fd`). The docs warn that more than 1 kHz with 8 motors makes the bus unstable, so **use one bus per arm** (7 joints + gripper = 8 motors).
- **Adapter:** WowRobo's bimanual kit ships **1x "USB-to-CANFD converter"** (model unverified; for Linux it must be SocketCAN-compatible, e.g. gs_usb/candleLight-FD class). Initial motor-ID setup uses the Damiao USB-CAN debugger on Windows. Recommendation: **2x PEAK PCAN-USB FD** (€278–298 each, mainline `peak_usb` driver), one per arm. Fallback: the Orin's built-in MTTCAN with a CAN-FD transceiver (§6).
- **Jetson:** not explicitly listed (unverified), but openarm_can is plain SocketCAN C++ and builds on any Linux with apt packages for Ubuntu 22.04/24.04. Expect no problems on arm64; build from source if no arm64 .deb exists.
- **ROS 2:** Humble is recommended; Jazzy is "being worked on, may be unstable" ([docs](https://docs.openarm.dev/api-reference/ros2/install)). Humble EOL is May 2027, so plan the Jazzy migration together with JetPack 7.2.
- **Risks:**
  - Damiao firmware is **closed** and is flashed only with the Windows "Damiao Debugging Tool" over UART ([docs](https://docs.openarm.dev/setup/openarm-setup/motor-firmware-update/)).
  - There is **no STO and no brakes** ([CNX spec summary](https://www.cnx-software.com/2026/09/30/openarm-2-0-an-open-source-7-dof-robot-arm-with-qdd-joints-bilateral-force-feedback-in-hand-camera/)). Protections are driver-level only (temperature, voltage, current) plus backdrivability.
  - Stop sequence: a Cat-1 stop sent over CAN (not safety-rated), then the PNOZ opens the DC contactors on the 24 V arm bus, and the arms drop. Mitigations: carry pose during navigation, mechanical rests/hooks, low joint torque limits in firmware config, and a speed/separation monitoring argument.
  - Motors are 24 V. Only the J8009P accepts 24–48 V. Peak draw ~480 W per the vendor.
- In-hand camera: RGB only, **model and resolution unpublished**.

### 3.3 End effectors
- **OpenArm parallel gripper (default):** same CAN stack, no extra software. KEEP.
- **ORCA Hand v2:** orca_core (MIT, v0.5.2, very active, has tests in CI). It supports Dynamixel *and* Feetech, and calibration/tensioning scripts exist. There is no ROS 2 package (it exposes a FastAPI server), and Python on USB serial runs 17 motors per hand. Assembled price is **$3,500 (Feetech) / $4,500 (Dynamixel)** per hand ([ROBOTIS/robozaps listings](https://www.robotis.us/orca-hand)). Each hand adds ~2 kg (est.) to a 4.1 kg-nominal arm. Software maturity is research-grade (0.x). **Not recommended for v1.**
- **AmazingHand:** Apache-2.0, Python and Arduino examples, <€200 BOM per hand, 8x Feetech SCS0009 on a serial bus. Simple and fully open, but low grip force. Good as an expressive or demo option.

### 3.4 SICK nanoScan3: KEEP (Low). Core vs Pro I/O
- `sick_safetyscanners2` supports "all microScan3, nanoScan3 and outdoorScan3 variants with Ethernet connection". It publishes LaserScan, extended scan, field/intrusion data, output paths and diagnostics. It is on the ROS index for Humble/Jazzy/Kilted/Rolling.
- **Core I/O (NANS3-AAAZ30AN1):** the datasheet lists "Measured data output: Via Ethernet", 3 universal I/O and 1 OSSD pair. The SICK technical information "Data output via UDP and TCP/IP" covers nanoScan3 Core I/O and Pro I/O; only the number of data-output channels and I/O bits differ. **So the Core works with ROS.**
- **Pro I/O (NANS3-CAAZ30AN1):** 4 universal I/O plus 2 universal inputs, and more monitoring cases. **Recommendation: Pro I/O** for an AMR, because speed-dependent field switching (driving vs. standing vs. docking vs. "arms working") needs more monitoring cases and inputs. Price is about the same (~€2,340–2,395 at distributors such as [vb-steuerungstechnik](https://vb-steuerungstechnik.de/Sick-NANS3-CAAZ30AN1-/-1100334-/-nanoScan3-Pro-/-Safety-Laser-Scanner_1); Core ~€2,350 converted from UK pricing). Delta ~€0; get a quote.
- Configuration uses SICK Safety Designer (Windows). Whether it is free is unverified.

### 3.5 Pilz PNOZmulti 2: KEEP WITH CAVEAT (Low-Med)
- No SDK, as expected for a safety controller. Logic is configured in **PNOZmulti Configurator (Windows, licensed; tiers and price unverified)**.
- **Integration:**
  1. **Safety path stays hardwired**: scanner OSSDs and the e-stop go to PNOZ inputs; PNOZ outputs drive the arm-bus contactors and the Tracer e-stop loop.
  2. **Diagnostics to the Jetson over Modbus TCP**: use **PNOZ m ES ETH** (Modbus/TCP server, port 502 fixed, up to 8 connections, virtual I/O set in the Configurator; [Pilz comms manual](https://pim.galco.com/Manufacturer/Pilz/TechDocument/Operation%20Manual/772135_opm.pdf)), or a **PNOZ m B1** base unit with built-in Ethernet/Modbus TCP ([pilz.com 772101](https://www.pilz.com/en-INT/eshop/product/772101)). Read it with `pymodbus` in a small ROS 2 node.
  3. **Redundant fast signal**: 1–2 PNOZ semiconductor outputs go through 24 V→3.3 V optocouplers into Jetson 40-pin GPIO, so the software sees "safe stop active" without the network.
- The Jetson must **never** be in the safety chain; it only reads status. This also keeps the AI/LLM out of safety functions, as the Machinery Regulation plan requires.
- Price for ES ETH / B1 Ethernet not verified (est. **€350–450**).

### 3.6 Orbbec Gemini 336L: KEEP (Low)
- SDK v2.10.6 and the ROS 2 wrapper v2.10.6 were both released 2026-09-30. Arm64 .deb packages are **tested on Jetson AGX Orin**. The ROS 2 wrapper covers Humble and Jazzy. Gemini 336L firmware is 1.8.10.
- **Licence caveat:** the SDK repo is MIT, but it ships a **proprietary "Extension Library" under an Orbbec EULA** (some advanced filters). The core depth/color streams are open. The licence is restricted to genuine Orbbec hardware. Acceptable.

### 3.7 Insta360 X4: REPLACE (High)
- **What works:** the official Desktop CameraSDK supports X4 on **Windows, Ubuntu 22.04 x86-64 and aarch64** (Jetson toolchains named). `StartLiveStreaming` gives a **1920x960 p30 preview** as H.264/H.265 **unstitched dual fisheye** through a `StreamDelegate` callback. Camera-V2.1.8 was released 2026-08-28. Sources: [Desktop-CameraSDK-Cpp README](https://github.com/Insta360Develop/Desktop-CameraSDK-Cpp), [developer docs](https://github.com/Insta360Develop/Insta360-Developer_Docs).
- **Why it is still High risk:**
  - The SDK is **gated** ([apply](https://www.insta360.com/sdk/apply)), binary-only, with licence terms not public (unverified).
  - The X4 must be put in **"Android" USB mode by choosing it on a pop-up on the camera at each connection**. This is a problem for a headless robot after reboots or USB resets; whether the choice can be persisted is unverified.
  - The docs say Linux needs `sudo` (fixable with udev rules).
  - You must do your own decode and stitching.
  - Continuous streaming on an action camera: thermal behaviour and battery-vs-USB-power are unverified.
  - **X4 "webcam mode" (UVC)** is officially documented only for OBS on desktop OSes. **UVC on Linux/Jetson is unverified.**
- **Do we need 360° at all?** For safety and navigation, **no**: 2x nanoScan3 at 275° each, mounted on diagonal corners, cover 360° in the plane, and the Gemini 336L covers manipulation. 360° vision is only for HRI (finding and facing people) and remote telepresence.
- **Replacements:**

| Option | Software | Linux/Jetson | Price | Delta vs X4 €500 |
|---|---|---|---|---|
| **A (recommended): 2x USB UVC fisheye (~180°, 1080p, e.g. Arducam/e-con class), front + back** | standard V4L2, `usb_cam`/`v4l2_camera`, GStreamer; no SDK | native | ~€50 each (est.) | **−€400** |
| B: RICOH THETA X | UVC 4K H.264 equirectangular live stream; [gstthetauvc](https://github.com/nickel110/gstthetauvc) (LGPL-2.1, last push 2023); `ricohapi/libuvc-theta` is **archived** (2020) | community-confirmed on Jetson ([theta360.guide thread](https://community.theta360.guide/t/live-streaming-over-usb-on-ubuntu-and-linux-nvidia-jetson/4359)); Z1 thermal shutdowns reported in long streams | $599.95 (~€550) | +€50 |
| C: 3–4x GMSL fisheye (Leopard/e-con) | Jetson drivers from vendor (some closed) | needs GMSL carrier | €800–1,500 (est.) | +€300–1,000 |
| D: keep X4 | gated SDK | aarch64 OK | €500 | 0, if SDK approved |

### 3.8 Wrist cameras: KEEP WITH CAVEAT (Med)
- The OpenArm 2.0 in-hand camera is RGB, with **model, resolution and interface unpublished**. Ask the vendor for the USB VID/PID and confirm it is UVC. If it is UVC, it is fully accessible.
- **Upgrade option: RealSense D405** (Apache-2.0 librealsense v2.58.4, 2026-08-30; Jetson supported). RealSense spun out of Intel on 2025-07-11 as RealSense Inc. with a $50 M Series A and an NVIDIA collaboration. The GitHub org is now `realsenseai` and is active, so there is no orphaning risk today. Adds depth at 7–50 cm. Price ~€250–300 each (est., unverified). Not included in the new total.

### 3.9 Jetson AGX Orin 64 GB: KEEP (Low-Med)
- **JetPack 6.2** (Ubuntu 22.04) → ROS 2 **Humble**, matching openarm_ros2's recommendation. **JetPack 7.2** brings Orin to Ubuntu 24.04 / Jazzy; Isaac ROS 4.6.0 added Orin on JP 7.2 ([Isaac ROS release notes](https://nvidia-isaac-ros.github.io/releases/index.html)). Isaac ROS 5.0.0 (2026-09-21) targets ROS 2 Lyrical. Exact distro mapping per Isaac ROS 4.x release: double-check before migrating.
- **CAN:** **2 MTTCAN controllers**, both on the 40-pin header J30 (CAN0 DIN pin 29 / DOUT pin 31; CAN1 DIN pin 37 / DOUT pin 33). **No on-board transceiver.** Pinmux must be enabled. **CAN FD is supported, up to 15 Mbit/s data** ([NVIDIA Jetson Linux r36.4 CAN guide](https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/HR/ControllerAreaNetworkCan.html)). NVIDIA's suggested Waveshare SN65HVD230 board is only good to ~1 Mbit/s, so **for 5 Mbit/s CAN-FD use a CAN-FD-rated 3.3 V transceiver** (e.g. TCAN1042V / MCP2562FD class).

### 3.10 LED matrix face: KEEP (Low)
- `hzeller/rpi-rgb-led-matrix` (GPL-2.0) drives HUB75 from **Raspberry Pi** GPIO timing and is not a Jetson path.
- **Recommended:** ESP32-S3 HUB75 board (e.g. Adafruit Matrix Portal S3 class, ~€20–25) + `ESP32-HUB75-MatrixPanel-DMA` (MIT, active) or Adafruit Protomatter. The Jetson sends frames or expression IDs over USB-CDC serial (32x16x3 bytes = 1.5 KB per frame, trivially fast), optionally through micro-ROS. A 32x16 P4 panel costs ~€10–15 and needs a 5 V 2–4 A supply.

### 3.11 Coffee machine + shuttle: KEEP (Low)
- RP2040 (Pico) or ESP32 running micro-ROS (Apache-2.0; ESP-IDF component pushed 2026-10-02; Pico SDK port 6.0.0), or a plain line protocol over USB serial.
- I/O: one opto-isolated relay or MOSFET in parallel with the machine's brew button (or a small solenoid "finger" if we must not open the machine), a linear actuator through an H-bridge (e.g. DRV8871) with end-stops, and a cup-present sensor.
- The coffee machine's 230 V side stays outside the MCU. Interlocks belong in the PNOZ, or at least in software with a hardware timeout.

### 3.12 48 V LFP battery + CAN BMS: ADD (Med, not in BOM)
- Prefer a **documented, published protocol**:
  - **REC Q BMS / REC ABMS:** Victron-GX-compatible CAN (11-bit IDs 0x351/0x355/0x356/0x35A/0x35B/0x35E/0x370, every 170 ms), manual is public ([REC Victron manual](https://www.rec-bms.com/datasheet/UserManual_REC_Victron_BMS.pdf)).
  - **Orion BMS 2 / Orion Jr 2 w/CAN:** up to 15 freely programmable CAN messages, public manual ([operation manual](https://www.orionbms.com/manuals/pdf/orionbms2_operational_manual.pdf)). Orion 2 ~$1,060; Jr 2 covers 1–16 S (48 V LFP = 16 S).
  - Simplest for certification: buy a **complete CE pack (IEC 62619, UN 38.3) whose BMS speaks the Pylontech/Victron "CAN-BMS" protocol** and decode it with a DBC + `cantools` on SocketCAN.
- Avoid BMSs with undocumented UART/BLE only (many Daly/JBD units). JK BMS has good community support ([esphome-jk-bms](https://github.com/syssi/esphome-jk-bms), UART/BLE), but the protocol is reverse-engineered.
- Estimate: 48 V 40 Ah CE pack with CAN BMS + DC-DCs (48→24 V 20 A x2, 48→5 V) + charger ≈ **€1,500** (est.).

### 3.13 Docking station: KEEP (Med)
- Software: Nav2 docking server (Apache-2.0). Use `opennav_docking` (`humble` branch) on Humble; it lives in navigation2 (`nav2_docking`) from Jazzy on. You write a ChargingDock plugin (detection by laser ICP or AprilTag, charging-state check from the BMS CAN current).
- Hardware is custom (spring contacts, contacts energised only when the robot is detected). The €900 budget is plausible but not verified against parts.

---

## 4. Top risks (ranked)

1. **Arm functional safety / CE:** Damiao has no STO, no brakes and closed firmware. A safe stop means a non-safety CAN stop followed by a contactor cut, so the arms drop. Certification effort and cost are the biggest unknowns (doc estimate 12–18 months with OpenArm). *Mitigation:* stowed pose while driving, mechanical rests, torque limits, PNOZ-timed Cat-1 stop, early talk with a notified consultant. Medium term, evaluate arms with brakes/STO.
2. **BOM under-costing:** battery/BMS, CAN-FD adapters, Pilz comms, switch and MCUs add ~€2,200–2,600. Fixed in §5.
3. **ROS 2 distro lock-in:** openarm_ros2 is stable on Humble only (Humble EOL May 2027), while Isaac ROS and JetPack 7.2 are moving to Jazzy/Lyrical. Plan one migration to JetPack 7.2 + Jazzy in 2027.
4. **Insta360 X4 access/ops:** gated SDK and an on-camera USB-mode pop-up. Avoid it with option A.
5. **CAN-FD timing on USB adapters:** 2 arms x 8 motors at 1 kHz plus USB latency jitter on Jetson. *Mitigation:* one bus per arm, PREEMPT_RT kernel optional, or native MTTCAN with CAN-FD transceivers.
6. **Unknown wrist-camera part:** confirm it is UVC before ordering.
7. **No vendor dock for Tracer, and Tracer battery 24 V vs. pack 48 V:** custom charging design (48→24 V LFP charger on board) needs validation.
8. **Hand options:** ORCA is research-grade (v0.x), adds weight and ~€3–4 k per hand. AmazingHand is weak. Keep the parallel gripper for v1.

---

## 5. Recommended part swaps / additions

| Change | Reason | Delta (EUR) |
|---|---|---|
| Insta360 X4 → 2x USB UVC fisheye cameras (front/back) | X4 SDK gated + closed; UVC is open and native on Jetson; 360° safety already covered by scanners | **−400** |
| + 2x PEAK PCAN-USB FD (one bus per arm) + 2x 3.3 V CAN transceiver modules for Orin MTTCAN (BMS, spare) | kit includes only 1 USB-CANFD converter (model unverified); Orin needs external transceivers | **+600** |
| nanoScan3 Core I/O → Pro I/O (x2) | more monitoring cases/inputs for speed-dependent fields; same data output | **~0** (get a quote) |
| + Pilz PNOZ m ES ETH (or PNOZ m B1 base unit) | Modbus TCP status to Jetson; Pilz has no SDK | **+400** (est.) |
| + 48 V 40 Ah LFP pack with CAN BMS (REC/Orion/Pylontech-protocol, CE + IEC 62619 + UN 38.3) + DC-DCs + charger | missing from BOM; required by the power architecture doc | **+1,500** (est.) |
| + Industrial 5–8-port Ethernet switch (24 V DIN) | scanners + PNOZ + Jetson | **+80** |
| Face: GC9A01 eyes → 32x16 P4 HUB75 panel + ESP32-S3 driver | brief spec; open MIT driver path | **+30** |
| + RP2040/ESP32 + relay + H-bridge + sensors for coffee shuttle | MCU not budgeted | **+30** |
| **Total delta** | | **+2,240** |
| **New BOM total** | vs current ~€28,080 | **≈ €30,320** |

Optional, not included: 2x RealSense D405 (+~€540, est.), 2x ORCA Hand v2 (+~€6,500–8,300), 2x AmazingHand (+~€400–500), Ricoh THETA X instead of option A (+€450 vs option A).

At the README's 30% margin, €30,320 / 0.70 ≈ **€43,300** customer price. Above the current €39,900 early-bird list price, which needs revisiting.

---

## 6. Interfaces summary

**CAN buses (4 recommended):**

| Bus | Devices | Type / bitrate | Host port |
|---|---|---|---|
| CAN-A | Tracer 2.0 base | classic CAN 2.0B, 500 kbit/s | Tracer's bundled USB-CAN (gs_usb) **or** Orin MTTCAN0 + 3.3 V transceiver |
| CAN-B | Left OpenArm (7 joints + gripper) | CAN-FD 1 M / 5 M, 1 kHz | PCAN-USB FD #1 (or kit converter) |
| CAN-C | Right OpenArm (7 joints + gripper) | CAN-FD 1 M / 5 M, 1 kHz | PCAN-USB FD #2 |
| CAN-D | 48 V BMS | classic CAN, 250 or 500 kbit/s (BMS-specific) | Orin MTTCAN1 + 3.3 V transceiver |

Do not share the base and BMS on one bus unless bitrate and ID ranges are confirmed compatible. Keep the arms on separate buses. Jetson MTTCAN can do CAN-FD up to 15 Mbit/s with a proper FD transceiver, so the arms could also run on native MTTCAN if USB jitter is a problem (then the base and BMS move to USB adapters).

**Ethernet (switch, 24 V DIN, ~5–8 ports):** 2x nanoScan3 (UDP data + Safety Designer), PNOZ m ES ETH / B1 (Modbus TCP), Jetson (devkit RJ45, 10GbE), plus a maintenance port. Use static IPs on a separate subnet.

**USB (use a powered USB 3 hub; ~9–11 devices):** Gemini 336L (USB 3, direct port), 2x wrist cams, 2x fisheye cams (or X4), 2x PCAN-USB FD, Tracer USB-CAN (if used), ESP32-S3 face (CDC), RP2040 coffee MCU (CDC), and optionally hand servo adapters (U2D2/Feetech). Exact devkit port count: check against the Orin devkit spec (unverified here).

**GPIO / hardwired:** PNOZ semiconductor outputs → optocouplers → Jetson 40-pin GPIO ("safe-stop active", "e-stop pressed"). Scanner OSSDs, e-stop and contactors stay hardwired to the PNOZ only.

---

## 7. Unverified items (to confirm with vendors)

- Model of the OpenArm USB-to-CANFD converter and whether it is SocketCAN (gs_usb/candleLight-FD) compatible.
- Model, resolution and UVC compliance of the OpenArm 2.0 in-hand camera.
- An official arm64/Jetson build of openarm_can/openarm_ros2 (expected to work; not documented).
- Insta360 SDK licence terms, approval time, whether X4 "Android" USB mode persists without the on-camera pop-up, X4 UVC webcam mode on Linux, and thermal behaviour in continuous streaming.
- PNOZmulti Configurator licence tiers and price; PNOZ m ES ETH / B1 prices.
- Whether SICK Safety Designer is free; exact Core vs Pro monitoring-case counts and the current quote.
- AgileX dock/charging pile for Tracer 2.0 (advertised "automatic recharging"; no part found).
- 48 V pack, D405, fisheye camera and LED panel prices (estimates).
- Jetson AGX Orin devkit USB port count; Isaac ROS 4.x distro per release.

## 8. Sources (checked 2026-10-03)
- GitHub API metadata/releases for all repos linked above (enactic/*, agilexrobotics/*, SICKAG/*, orbbec/*, orcahand/*, pollen-robotics/AmazingHand, realsenseai/*, Insta360Develop/*, ros-navigation/navigation2, open-navigation/opennav_docking, micro-ROS/*, mrfaptastic/ESP32-HUB75-MatrixPanel-DMA, hzeller/rpi-rgb-led-matrix, nickel110/gstthetauvc, ricohapi/libuvc-theta)
- OpenArm docs: https://docs.openarm.dev/ , /purchase/ , /setup/openarm-setup/ , /api-reference/can/ ; WowRobo kit contents: https://shop.wowrobo.com/products/openarm-2
- SICK nanoScan3 Core I/O datasheet NANS3-AAAZ30AN1; SICK TI "Data output via UDP and TCP/IP": https://www.sick.com/media/docs/1/01/701/technical_information_microscan3_outdoorscan3_nanoscan3_data_output_via_udp_and_tcp_ip_en_im0083701.pdf
- Pilz PNOZmulti 2 communication interfaces manual; PNOZ m B1 (772101)
- NVIDIA Jetson Linux r36.4 CAN guide; Isaac ROS release notes
- RealSense spin-off: https://www.therobotreport.com/intel-spins-out-realsense-as-standalone-company/
- RICOH THETA X price: https://us.ricoh-imaging.com/product/theta-x/
- PCAN-USB FD prices: https://www.esacademystore.eu/en/PCAN-USB-FD , https://twincomm.nl/en/product/pcan-usb-fd/
- Orion BMS: https://amprevolt.com/products/orion-bms

---

## 9. How this maps to the code (`giorgio_os/`)

Each component above has one driver class in `giorgio_os/giorgio_os/hal/real/drivers.py`. Each class names the SDK/topics listed here: `TracerBase`, `OpenArm`, `OpenArmGripper` / `OrcaHand` / `AmazingHand`, `NanoScan3`, `PnozRelay`, `OrbbecCamera`, `UvcCamera` (wrist cams and the recommended fisheye replacement for the X4), `CanBms`, `NavDock`, `Hub75Face` and `CoffeeMcu`. They are stubs today; the bring-up order is in `giorgio_os/README.md`. The real-robot wiring for each configuration (CAN interfaces, IPs, topics, serial ports) is in `giorgio_os/giorgio_os/configs/*.yaml`. The swaps recommended in §5 need no change above the HAL: the 360° camera becomes a `UvcCamera`, and the Pilz comms module is read by `PnozRelay` over Modbus TCP.
