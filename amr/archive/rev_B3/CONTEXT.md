# Giorgio own AMR: shared context for all work streams (rev B, 2026-10-05)

**Rev B (owner decision): NO waist yaw joint. Scanners kept. Everything certifiable, minimum cost, all docs in English.**
The top deck (10 mm 6082, z 343..353) is the fixed superstructure flange; Jetson + arm DC-DCs sit in the base centre bay.
The waist bullet below is HISTORY (rev A) and no longer applies.

Owner goals: build our OWN AMR base for Giorgio, quickly CE-certifiable, industrialisable at low cost in Italy, using
certified off-the-shelf DIN modules (no custom PCB). Rotate in place, plus a waist (torso yaw) joint. Ready for pre-production.
Owner language: Italian. Code/docs in the repo: English (match existing docs). Never present an estimate as a fact:
tag values SOURCED (manufacturer URL) / SECONDARY (distributor) / ESTIMATE / ASSUMED.

## Decided architecture
- Kinematics: differential drive, 2 rigid drive wheels at x=0, y=±232 (track 464), rotation centre = base centre;
  4 sprung swivel castors Blickle L-ALST 80K (D80) at (±275, ±180) on MGN15 guides (rev B3, CASTOR_SUSPENSION.md). Body 780 x 560 mm (corners chamfered 95 mm), ground clearance 32 mm.
- Drives: 2x ez-Wheel SWD 125 EW2A-125HN04B (4:1, brake): 24 V DC, 7.9 Nm nominal / 13 Nm peak, 380 rpm (~2.5 m/s),
  250 kg static per wheel, 200 W S1. Integrated certified safety: STO SIL3/PLe Cat 4; SBC, SLS, SDI, SMS, safe encoder
  SIL2/PLd (INERIS DoC). CANopen Safety + safe I/O. EUR 2,333 each (Generation Robots). Datasheet:
  https://www.ez-wheel.com/en/safety-wheel-drive-swd-125 ; manual https://www.ez-wheel.com/storage/upload/pdf/swd-products-v20x-03112023-user-manual-en-0-0.pdf
- Traction bus T24 (24 V) from the 48 V bus: 2x Mean Well DDR-480C-24 (33.6–67.2 V in, 20 A, 30 A 5 s) + ORing +
  27.5 V shunt regulator (regen). OPEN: confirm with ez-Wheel that a DC-DC supply (not a battery) is acceptable and regen energy.
- Battery: 2x Discover AES PRO DLP-GC2-48V in parallel (LFP 51.2 V 30 Ah 1.54 kWh each = 3.07 kWh; 58 A cont / 90 A 3 s each;
  14 kg each; 260x180x254 mm; IP67; IEC 62619, UL 2271, CE, UN 38.3; LYNK/J1939; ~USD 1,009 each). Each pack < 2 kWh ->
  EU 2023/1542 Art 7/8/10/77 (passport etc.) not triggered. Lying mounting + paralleling: to confirm with Discover.
- Bus B48: 40–58.4 V. Main fuse ~150 A 80 V class, Albright SW80 (blowout) main contactor, precharge relay+resistor,
  Albright ED250 key service disconnect.
- (rev A only, REMOVED in rev B) Waist yaw: Synapticon ACTILINK-JP25 Safe Motion (64/194 Nm, 38 rpm, 3.87 kg, STO/SBC/Safe Motion SIL3 PLe via FSoE, EtherCAT,
  24–48 V, EUR 1,618) hanging under the deck; THK RU124 crossed-roller ring (80/165/22, C0 50.9 kN) carries the tilting moment;
  igus twisterband (±180°) for cables; hard stops + safe limited position. Only 48 V (arms bus + aux), Ethernet/EtherCAT and the
  safety loop cross the joint; compute (Jetson Orin NX), arm DC-DCs sit on the rotating waist plate.
- Waist flange top at z=353 mm = old adapter plate height -> the whole superstructure (OpenArm torso/arms, head, coffee module,
  tray) is unchanged. Rotating mass 54.5 kg, CoG (-41, 2, 804) mm (yaw 0). Fixed base 98.6 kg, CoG (-5, 7, 152).
  Payload: 2 x 3 kg in the hands + 2.1 kg tray. Rotating swept radius 440 mm.
- Safety: 2x SICK nanoScan3 Pro I/O (PL d, Type 3, encoder inputs, 128 field sets) on the front-right and rear-left castor
  towers, scan plane 184.5 mm; SICK Flexi Soft FX3-CPU1 + 2x FX3-XTIO + FX3-MOC1 + gateway; 2 E-stops (Eaton M22, 2NC) on the
  sides + one on the torso; key service disconnect.
- Dock: Roboteq RoboPad (75 A, ±5 mm, Hall docked sensor) collector at the rear centre (z 120); dock with Mean Well NPB-1700-48
  (25 A CC, CANbus, IEC 60335-2-29) and a controller+relay that keeps the pads dead until Hall + CAN handshake; AprilTag +
  retro-reflective profile; Nav2 Docking Server (Apache-2.0).
- Arms: R&D variant = Enactic OpenArm 2.0 (Damiao motors, no STO, no brakes) on 2x regulated 24 V buses (DDR-480C-24 each, on
  the waist plate), power cut by safety contactors (stop cat 0/1), arms move only with the protective field clear (SSM by
  scanners), parked on mechanical rests, hand-over via tray only, objects carried in the tray while driving.
  CE-fast variant = certified DC cobot arms (Kassow Edge 42–58 V DC or UR e-Series + DC OEM box) on the 48 V bus.
- CE route: Machinery Regulation (EU) 2023/1230 applies from 20 Jan 2027 (Directive 2006/42/EC before); Giorgio not in Annex I
  as long as no ML ensures a safety function -> module A (self-assessment). Standards: EN ISO 12100, EN ISO 3691-4:2023 (base),
  EN ISO 10218-1/-2:2025 (arms/application), EN ISO 13849-1:2023, EN 60204-1, EN IEC 61800-5-2; barista in public: EN ISO 13482.
  RED (Wi-Fi) incl. EN 18031-1; EMC; Battery Reg.

## Files
- amr/amr_params.py (all dimensions), amr/amr_cad.py (CadQuery; run: cd ~/giorgio_sim/amr && ../cad/.env/bin/python amr_cad.py),
  amr/integrate.py, amr/out/parts.json (every part: mass, CoG, bbox, material, process), amr/out/integration.json,
  amr/out/{step,stl,dxf,exploded}/.
- Existing (reference, do not break): cad/ (superstructure CAD, validated), electrical/ (old power design: ARCHITECTURE.md,
  netlist*.yaml, calc.py), docs/bom.csv, docs/BASE_DECISION_2026-10-05.md.
- Loads (electrical/ARCHITECTURE.md §3): each OpenArm 70 W typ / 360 W cont / 720 W 5 s; Jetson Orin NX 10–40 W; coffee 300 W
  (barista); scanners ~ 2x 6 W; superstructure sustained ~1.24 kW, peak ~2.1 kW 5 s.
- Disk: / has only ~4 GB free. Do not write large files.
