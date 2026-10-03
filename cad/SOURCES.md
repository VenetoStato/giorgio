# Giorgio CAD — sources of purchased-part data

Confidence labels: **SOURCED** = read from an official datasheet, manual, drawing or official CAD/URDF;
**SECONDARY** = reseller / forum / third-party copy; **NOT FOUND / ESTIMATE / ASSUMED** = no public number, best guess,
must be confirmed before ordering. Research done 2026-10-03 (web) plus our own measurements of the official files below.

## Own measurements on official files (in this repository)

| Item | Value | How | Confidence |
|---|---|---|---|
| OpenArm 2.0 body_link0 base plate | 250 x 190 x 8 mm (x -155..95, y ±95 in the torso frame), 48 holes on a 30 mm grid (x -135..75, y -75..75); holes drawn Ø5.5 in the STL (docs.openarm.dev says "M6 taps") | sections of `third_party/openarm_mujoco/v2/assets/visual/body/body_link0.stl` (cad/ analysis) | SOURCED geometry; thread type conflicting (see README) |
| body_link0 post / shoulder block | 60 x 60 T-slot post (x,y ±30) from z 8 to ~650; shoulder block x -85..65, y ±79, z 640..773 (tapered); gussets measured by section | same STL | SOURCED (envelope simplified) |
| Free bolt positions under body_link0 | clearance above holes: (75, *) and (-135, ±45/±75) free > 600 mm; (±15, ±15..±75) occupied by Enactic brackets | ray casts on the STL | SOURCED |
| Tracer 2.0 plan octagon | front chamfer 57 x 117 mm, rear 69 x 127 mm; body 580 wide, rails ~39 mm wide x ~561 mm long, centred | scaled from the manual's top-view drawing (p.35, 1.078 mm/px) | ESTIMATE ±3 mm |
| OpenArm arm link meshes, poses | official MJCF meshes, recorded mission poses | `cad/sim_export.py` from `giorgio_model.py` + `render/*_v9.npz` | SOURCED (sim) |

Confidence labels: SOURCED = read from an official datasheet, manual or drawing. SECONDARY = from a reseller, forum or third party. NOT FOUND / ESTIMATE = not located, best guess clearly marked.

## 1. AgileX Tracer 2.0 AMR

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| L x W x H | 702 x 610 x 169 mm | Manual s1.2 + datasheet: https://static.generation-robots.com/media/user-manual-tracer-2-0-agilex-robotics.pdf , https://static.generation-robots.com/media/datasheet-tracer-2-0-agilex-robotics.pdf | SOURCED (AgileX manual, distributor-hosted) |
| Mass | 54-56 kg | same | SOURCED |
| Payload | 150 kg rated (datasheet). The manual's safety section says "maximum load ... 100 KG" | same | SOURCED, but the two documents conflict: **design to 100 kg** |
| Payload (other) | global.agilex.ai/products/tracer-2-0 says 80 kg, 1.5 m/s. That page text looks mixed with another product ("four-wheel steering omnidirectional") | https://global.agilex.ai/products/tracer-2-0 | SECONDARY / unreliable |
| Wheelbase (track) | 517.4 mm | manual s1.2 | SOURCED |
| Ground clearance | 27 mm | manual s1.2 | SOURCED |
| Body width without side bumpers | 580 mm | manual s5.1 drawing (top view) | SOURCED |
| Top mounting | 2 longitudinal aluminium rails (T-slot profiles) along the top, 230 mm apart (dimension in the top-view drawing). They run almost the full length of the flat deck. Also 4 small holes/slots near the front between the rails | manual s5.1 drawing p.35 | SOURCED (230 mm spacing; whether it is centre-to-centre or edge-to-edge is not stated, but it reads as rail-to-rail) |
| Rail profile size / slot / thread | not given | - | NOT FOUND. ESTIMATE: 20-series (20x20 or 20x40) slot-6 profile with M5 T-nuts |
| Top-surface height | 169 mm overall height. Treat the rail top as about 169 mm above the floor | manual | SOURCED for overall H. The rail top = deck top is an ESTIMATE |
| Wheel diameter | not stated | - | NOT FOUND. ESTIMATE: about 150-170 mm hub-motor wheel |
| Battery / power out | 24 V 30 Ah LiFePO4; user output 24 V 15 A | datasheet | SOURCED |
| Speed / climb | 2.0 m/s; 8 deg | datasheet | SOURCED |
| Tracer v1 (for reference) | 685 x 570 x 155 mm, 25-30 kg, wheelbase 360 mm, ground clearance 30 mm (drawing shows 34). Same 2-rail top layout, rails 230 mm apart. Manual: https://static.generation-robots.com/media/user-manual-agilex-robotics-tracer-fr.pdf (p.22) | v1 manual | SOURCED |

## 2. SICK nanoScan3 (NANS3-CAAZ30AN1 Pro I/O; Core NANS3-AAAZ30AN1)

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| W x H x D | 106.6 x 80 x 117.5 mm (including system plug). Drawing: height 80.2; housing body 100.6 (W) x 102.5 (D) without plug; optics hood dia. 86 | https://www.sick.com/media/pdf/0/80/980/dataSheet_NANS3-CAAZ30AN1_1100334_en.pdf p.4-5 | SOURCED |
| Weight | 0.67 kg | same | SOURCED |
| Scan plane height above base | 50.5 mm (= 19 + 31.5). The top of the hood is 29.7 mm above the scan plane | same, dimensional drawing p.5 | SOURCED |
| Mounting threads | 2 x M5 x 7.5 mm deep blind holes on the side face. Holes are 44 mm apart, centres 19 mm above the base. Horizontal position: 26.3 mm from the housing edge to the first hole, then 24 mm from that hole to the mirror axis (so the second hole is 20 mm past the axis). The opposite/rear face also shows 2 holes on the same pattern | same | SOURCED (dimensions read from the drawing; the hole positions are my interpretation of the chain dims) |
| Required viewing slit | a (length), b (min height above scan plane), c (min height below). Values are only in the operating instructions | same | NOT FOUND (numbers). ESTIMATE: keep at least 10 mm above and below the scan plane clear over 275 deg |
| Field of view | 275 deg; Pro: protective field 3 m, warning field 10 m | datasheet | SOURCED |
| Mounting kits | Kit 1a 2111767 (bracket); 1b 2111768 (bracket + optics-cover protection); 2a 2111769 (alignment bracket, cross-wise + depth axis); 2b 2111770 (2a + optics protection) | https://www.seltec.co.uk/products/details/19735.html (and the 19734/19732/19733 pages) | SECONDARY. 2111661 not found |
| Mounting instructions | https://www.sick.com/media/docs/6/76/876/mounting_instructions_nanoscan3_safety_laser_scanner_de_en_im0089876.pdf | sick.com | SOURCED (URL) |
| Operating instructions | www.sick.com/1100334 (Downloads). Third-party copy: https://www.manualslib.com/manual/3196969/Sick-Nanoscan3.html | datasheet note | SOURCED pointer |
| Core (AAAZ) housing | Datasheet https://www.sick.com/media/pdf/9/79/979/dataSheet_NANS3-AAAZ30AN1_1100333_en.pdf. Not checked; assumed identical housing | - | ESTIMATE: identical |

## 3. Orbbec Gemini 336L

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Dimensions | 124 x 29 x 27.7 mm (W x H x D). Drawing: 124.02 ±0.3 long, 29.73 high, 27.70 deep | Gemini 330 series datasheet V1.6, table + Appendix E p.68: https://new-orbbec3d-s3.s3.amazonaws.com/wp-content/uploads/2025/04/22062452/Gemini-330-series-Datasheet-V1.6.pdf | SOURCED |
| Weight | 135 g (335L: 133 g) | same | SOURCED |
| Bottom mount | 1x 1/4-20 UNC, max insertion 8 mm, torque 4.0 N·m | same | SOURCED |
| Back mount | 2x M4, max insertion 4 mm (table says 3 mm), torque 0.4 N·m, **95.00 ±0.3 mm apart** (back-view dimension) | same, Appendix E | SOURCED (I read 95 mm as the M4 spacing from the drawing) |
| Other | 2x M2 (H3.5) for the sync connector cover; USB-C; less than 3 W | same | SOURCED |

## 4. Insta360 X4

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Dimensions | 46 x 37.6 x 123.6 mm (with lenses); 26.3 mm thick without lenses | https://onlinemanual.insta360.com/x4/en-us/faq/specs/hardware | SOURCED |
| Weight | 203 g | same | SOURCED |
| Mount | 1/4"-20 female thread in the base (also the fold-out mount) | not on the specs page | SECONDARY / common knowledge |

## 5. Aluminium profiles

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| item Profil 8 80x80 leicht, natur | Art. 0.0.265.80 (shop also shows 1.1.265.80). m = 5.33 kg/m, A = 19.75 cm², Ix = Iy = 134.06 cm⁴, Wx = Wy = 33.51 cm³ | https://www.item24.com/de-de/profil-8-80x80-leicht-natur-1126580 | SOURCED |
| item Profil 8 80x80 (standard), natur | Art. 1.1.026.27 / 0.0.026.27. m = 7.19 kg/m, A = 26.66 cm², Ix = Iy = 187.7 cm⁴, W = 46.92 cm³ | https://www.item24.com/de-de/profil-8-80x80-natur-1102627 | SOURCED. The "0.0.026.34" number was not confirmed |
| item Profil 8 80x80 E (economy) | 0.0.453.01. 4.01 kg/m, A = 14.86 cm², Ix = Iy = 100.69 cm⁴ | https://www.item24.com/en-de/profile-8-80x80-e-natural-45301 | SOURCED |
| Slot width, item Line 8 | **8 mm** (the "8" in Profile 8 is the slot width; 10 mm is the Bosch 45-series slot) | - | ESTIMATE / standard knowledge |
| Core bore, 80x80 | not on item24 page | - | NOT FOUND. ESTIMATE: Ø 10.2 mm (tap M12) |
| item Nutenstein 8 St M8, verzinkt | 0.0.026.18, 10 g, F_zul = 5000 N, M = 25 Nm. Dimensions not shown | https://www.item24.com/de-ch/nutenstein-8-st-m8-verzinkt-2618 | SOURCED. ESTIMATE dims: about 16 x 22 x 7.5 mm |
| Bosch Rexroth 45x45 / 80x80 | not retrieved (search budget used up) | - | NOT FOUND |

## 6. Enactic OpenArm 2.0

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Payload nominal / peak | 4.1 kg (held 1 min, worst posture) / 6.0 kg (3 s move + 1 s hold). **Includes the end effector** (1.5 kg EE gives 2.6 / 4.5 kg) | https://docs.openarm.dev/hardware/openarm-2.0/general/ | SOURCED |
| Arm mass | about 5.5 kg per arm. URDF nominal: base_link..link6 sum = 5.36 kg | CNX article https://www.cnx-software.com/2026/09/30/openarm-2-0-an-open-source-7-dof-robot-arm-with-qdd-joints-bilateral-force-feedback-in-hand-camera/ ; github enactic/openarm_description assets/robot/openarm_v2.0/config/arm/inertials/nominal.yaml | SECONDARY (5.5) / SOURCED (URDF 5.36) |
| Reach | 606 mm | CNX | SECONDARY |
| Base plate | 190 x 250 mm, 8 mm thick, 48 x M6 taps on a 30 mm grid. Support pillars are MISUMI aluminium frame | docs.openarm.dev general (M6 taps, MISUMI) + CNX (dims) | SOURCED (M6) / SECONDARY (dims) |
| body_link0 (torso) mass | 13.89 kg; Ixx = Iyy = 1.653, Izz = 0.051 kg·m² | openarm_description v2.0 config/body/inertials/nominal.yaml | SOURCED (URDF) |
| Arm mount points | left/right arm mounts at (0, ±0.031, 0.698) m from body_link0 origin | openarm_description v2.0 config/body/struct/reference_points.yaml | SOURCED (URDF) |
| Bimanual total | about 13.89 + 2 x 5.4 = about 24.6 kg, without grippers | derived | ESTIMATE |
| Torso-to-pedestal bolt pattern | not documented; use the 30 mm grid M6 base plate | - | NOT FOUND |

## 7. De'Longhi Inissia EN80

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| W x D x H | 4.7 x 12.6 x 9 in = 119 x 320 x 229 mm. Resellers give 120 x 321 x 230 mm | https://www.delonghi.com/en-us/p/inissia-nespresso-inissia-espresso-machine-by-de-longhi--black/EN80B.html?pid=0132191985 | SOURCED |
| Mass | 5.3 lb = 2.4 kg | same | SOURCED |
| Power | 1200 W (US); 1260 W EU version | same; eBay listing for EN80.CW | SOURCED / SECONDARY |
| Water tank | 0.7 L (23.67 fl oz) | same | SOURCED |

## 8. AMR charging contacts

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Roboteq RoboPad collector RPCOL90-100 | 90 x 56 x 42 mm extended (32 mm retracted; the drawing says 33.5 closed / 44.0 open). **4 mounting holes on a 74 x 56 mm pattern, 4 mm screws**. 2 x M6 terminal studs 40.5 mm apart. 10 mm extension, 100 A max / 75 A continuous, 75 V, ±5 mm L/R tolerance | https://docs.galco.com/techdoc/rbtq/robopads_dat.pdf p.13-15 | SOURCED |
| RoboPad base RPBAS90-100 | 140 x 90 x 10 mm, fixed with 2 x 6 mm (or 1/4") screws | same | SOURCED |
| Conductix Nano+ | 25/50/75 A, 1 or 2 pole. Nominal installed height 48.1 mm. Mounted with 2 x M5 DIN 912 (max 1.2 Nm). M6 connection bolt (5.7 Nm) | https://www.conductix.us/en/products/charging-contacts/nano (catalogue PDF blocked) | SECONDARY |
| TE blind-mating AMR connector | up to 50 A / 125 V; ±15 mm x, ±10 mm y | https://www.te.com/en/products/connectors/pcb-connectors/wire-to-board-connectors/intersection/blind-mating-mobile-charging-connector.html | SECONDARY |

## 9. Threaded inserts (heat-set, for SLS PA12)

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Kerb Konus S-Lok 860 (heat/ultrasonic) | M3: OD 4.6, L 5.8, hole 4.0 (short 861: L 4.0). M4: OD 6.3, L 8.2, hole 5.6 (short L 7.2). M5: OD 7.0, L 9.5, hole 6.4 (short L 8.2). M6: OD 8.6, L 12.7, hole 8.0. Hole tolerance +0.1. Min. wall W: 2.3 / 2.5 / 2.7 mm | https://www.kerbkonus.de/proddb/pdf/en.ds.30.pdf p.31 | SOURCED |
| Kerb Konus S-Lok-KOH 853 2 (tapered) | M3 OD 4.7 L 5.5 hole 4.4; M4 OD 6.1 L 7.5 hole 5.8; M5 OD 7.3 L 9.0 hole 6.9 | same p.33 | SOURCED |
| Ruthex standard | M3 x 5.7 (hole 4.0-4.2, wall ≥1.6); M4 x 8.1 (hole 5.4-5.6, wall ≥2.0); M5 x 9.5 (hole 6.9-7.1, wall ≥2.4) | https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen (length) ; table via https://ch.3ddruckboss.de/collections/ruthex-gewindeeinsatze | SOURCED (M3 L) / SECONDARY (holes) |
| Pull-out force | not published as numbers for PA12 | - | NOT FOUND. ESTIMATE in PA12 SLS: M3 about 0.8-1.2 kN, M4 about 1.5-2 kN, M5 about 2-3 kN (test before relying on it) |

## 10. ISO standard tables

| Size | ISO 273 fine / medium / coarse (mm) | Tap drill (mm) | Stress area As (mm²) | 8.8 proof load (N), ISO 898-1 | A2-70 Rp0.2 load = 450·As (N) |
|---|---|---|---|---|---|
| M3 | 3.2 / 3.4 / 3.6 | 2.5 | 5.03 | 2 920 | 2 260 |
| M4 | 4.3 / 4.5 / 4.8 | 3.3 | 8.78 | 5 090 | 3 950 |
| M5 | 5.3 / 5.5 / 5.8 | 4.2 | 14.2 | 8 230 | 6 390 |
| M6 | 6.4 / 6.6 / 7.0 | 5.0 | 20.1 | 11 600 | 9 050 |
| M8 | 8.4 / 9.0 / 10.0 | 6.8 | 36.6 | 21 200 | 16 470 |
| M10 | 10.5 / 11.0 / 12.0 | 8.5 | 58.0 | 33 700 | 26 100 |

Sources: ISO 273 at https://engineeringhardware.com/fastener/clearance-hole-sizes/ and https://mechcodex.com/reference/metric-clearance-hole-sizes (SECONDARY, standard values). ISO 898-1 proof loads at https://optimas.com/technical-resources/iso-metric-thread-proof-loads/ and https://www.engineeringtoolbox.com/metric-bolts-minimum-ultimate-tensile-proof-loads-d_2026.html (SECONDARY). 8.8 proof stress is 580 MPa for ≤M16. A2-70: Rm 700, Rp0.2 450 MPa (ISO 3506-1). ISO 3506 defines no "proof load"; the last column is computed (450 x As). Tap drills are the standard ISO coarse values (d - P).

## 11. Small linear actuator, about 150 mm stroke

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Actuonix P16-150 | 150 mm stroke, closed length 197 mm hole-to-hole, 125 g. Gear 22:1 / 64:1 / 256:1: peak 40 N@26 / 80 N@9 / 250 N@2.5 mm/s; max lifted 50 / 90 / 300 N; static 500 N. Ships with 2 brackets + #8-32 hardware. -P has potentiometer feedback | https://s3.amazonaws.com/actuonix/Actuonix+P16+Datasheet.pdf | SOURCED |
| Actuonix L16 (max 140 mm stroke) | 140 mm: closed length 208 mm, 84 g. 150:1: 175 N peak, 200 N lifted | https://www.actuonix.com/assets/images/datasheets/ActuonixL16datasheet.pdf | SOURCED |
| P16 body cross-section | not extracted | - | ESTIMATE: about 18 x 28 mm (motor side) |

## 12. 48 V (16S) LiFePO4, about 40 Ah

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Typical dims/mass | 350 x 250 x 200 mm at 15 kg; 470 x 210 x 180 mm at 23 kg (16S2P, 20 Ah cells); 522 x 240 x 224 mm at 25.1 kg (cased) | https://www.himaxelectronics.com/product-item/48v-40ah-lifepo4-battery-pack/ , https://www.lifepo4batterycells.com/sale-35279790-48-volt-40ah-lifepo4-battery-pack-16s2p-waterproof-light-weight.html , https://appbattery.com/product/48v-40ah-lithium-battery/ | SECONDARY |
| Design value | about 2.05 kWh. Use 400 x 220 x 200 mm and 18-20 kg | - | ESTIMATE |

## 13. Electronics

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| Jetson AGX Orin dev kit | 110 x 110 x 71.65 mm (incl. feet); about 1.58 kg without packaging | Weight: NVIDIA staff on https://forums.developer.nvidia.com/t/weight-of-jetson-agx-orin-dev-kit/209142 . Dims: https://www.sparkfun.com/nvidia-jetson-agx-orin-64gb-developer-kit.html | SOURCED (NVIDIA staff) / SECONDARY (dims) |
| Pilz PNOZ m B0 (772100) | W 45 x H 101.4 x D 120 mm; 235 g net; DIN rail 35 x 7.5 EN 50022. PNOZmulti 2 expansion/comms modules are 22.5 mm wide | Pilz datasheet copy https://dienelectric.com/pdf/Pilz-PNOZ-m-B0-772100-Datasheet.pdf | SOURCED (Pilz datasheet, third-party hosted) |
| Mean Well DDR-480C-24 (48 V in, 33.6-67.2 V; 24 V 20 A) | 85.5 x 125.2 x 129.2 mm (W x H x D); 1.375 kg; DIN rail. Note: DDR-480D is the 110 V-input version; use **C** for 48 V | https://www.meanwell.com/Upload/PDF/DDR-480/DDR-480-SPEC.PDF | SOURCED |
