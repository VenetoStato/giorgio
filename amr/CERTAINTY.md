# AMR rev B4: certainty audit of purchased parts and calculation inputs (2026-10-05)

Owner rule: every value the design uses must come from an official manual or datasheet, with no open questions. The rev B3 audit
(`archive/rev_B3/CERTAINTY.md`) found 30 BOM GAP rows, 10 CALC GAP inputs and findings F1–F10. **Rev B4 implements every fix that the
documents in `../docs/fonti/` (or a documented replacement part) allow** (`CAD_REV_B4.md`, `CALC.md`, `electrical/CHECKS_AMR.md`).
This file re-audits every row that rev B4 touched: the new sources were opened with pdftotext (or read as saved official web pages)
and the quotes below are verbatim. 61 official documents (19.4 MB) were added to `../docs/fonti/` (§6). Rows not touched keep their
rev B3 evidence.

## Status rules
- **DOCUMENTED:** the technical values the design uses are in an official manufacturer document (or a standard designation for
  standard parts), quoted below. "(design value)" = a value our own CAD or specification defines.
- **TYPE-TEST:** the value cannot be taken from a document; it is measured on the prototype in the `ce/TEST_PLAN.md` test named.
- **PRICE-ONLY:** the technical data are documented, but there is no public price, so a quote is needed.
- **GAP:** a technical value the design relies on has no official document behind it (fix in §3).
- **OPEN (checks only):** a check whose input is a GAP; it is neither PASS nor FAIL until the type test closes it.
- Evidence grade: a value read only on a distributor page is "SECONDARY"; for a safety-relevant part it stays a GAP. In rev B4 no
  safety-relevant technical value rests on a distributor page any more (Siemens, Eaton, Phoenix, Weidmüller, Pilz and Mersen PDFs
  were fetched from the makers' own domains).

## Summary (after rev B4)

### BOM (82 rows that count in the totals: 80 "buy" rows incl. the new SR3 and tunnel fans, plus H01..H10 and X05)

| Status | rev B3 | **rev B4** | Notes |
|---|---|---|---|
| DOCUMENTED | 27 | **49** | 7 also carry residual type tests (column TP) |
| PRICE-ONLY | 23 | **32** | technical data documented; a quote is needed |
| TYPE-TEST (as primary status) | 0 | **0** | |
| GAP | 30 | **1** | H01..H10 harness ampacity table (G-14: standard to buy, see `DOWNLOAD_LIST.md`) |
| Excluded (in_total = N) | 7 | 7 | rev A/B1 references, NPB-1700 option |

### CALC inputs (116 rows of `CALC.md` "Inputs and sources"; rev B3 had 110)

| Status | rev B3 | **rev B4** |
|---|---|---|
| DOCUMENTED (manufacturer or standard document) | 45 | **51** |
| DOCUMENTED (design value) | 30 | **35** |
| TYPE-TEST (TP-xx named) | 25 | **28** |
| GAP | 10 | **2** (G-15 gripper length beyond the payload point, G-18 coffee machine power) |

### Netlist input (electrical): 1 GAP
- **G-29 (new):** prospective short-circuit current of the B48 bus. The rev B3 "≥ 20 kA DC" bound (V:D6) was never documented, and
  the documented IEC 60269-6 breaking capacity of the Mersen HP10M links is **10 kA DC** (brochure; 50 kA DC I.R. to UL 2579). The 11
  B48 branch-fuse rows of `CHECKS_AMR.md` are **OPEN** until TP-14 measures the pack-pair Isc (acceptance ≤ 10 kA). Discover publishes
  no short-circuit current or internal resistance (manual 805-0027 searched).

### Checks after rev B4
- CAD: 0 interferences, 0 keep-out violations (3,608 pairs), 0 castor-travel overlaps, docked dock 0, slide paths empty; superstructure 0.
- CALC: **53 PASS / 7 WARN / 1 FAIL** (FAIL = cup held by friction, rule: tray). New WARN vs rev B3: Kassow peak per pack 61 A with the
  brochure's 1200 W per arm at the documented 40 V LVD (≤ 90 A 10 s, BMS trips only after 10 s > 58 A: energy-manager rule).
- Electrical: **242 PASS / 0 FAIL**, 11 OPEN (G-29) and INFO rows.

### Answer to "no open questions"
**Still not met, but reduced to items that no document can close today:** 1 BOM GAP (harness ampacity: buy EN 60204-1 / DIN VDE 0298-4),
2 CALC GAPs (gripper length: measure or OpenArm gripper CAD; coffee machine: not chosen), 1 netlist GAP (B48 Isc: measure in TP-14),
G-27 (ISO 3691-4 test-piece sizes: buy the standard) and G-28 evidence (Pilz PNOZ m B0 certificate, Discover UN 38.3 summary). Every
other item is a price quote or a named type test. Findings F1–F5 are implemented (§5). Manual downloads and purchases: `DOWNLOAD_LIST.md`.

## 1. BOM matrix (every purchased row of `bom_amr.csv`, rev B4)

Columns as in rev B3. Rows re-audited in rev B4 carry "rev B4" in the note; rows 88–89 are new.

| # | BOM id | qty | in total | technical data used by the design | official source (doc + page / URL, local file) | verbatim quote | status | type tests (TP) | note / fix | price tag (BOM) → price status | spot-checked |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `K05_rubber_edge` | 1 | Y | EPDM profile 25 x 20 mm, 70 ±5 Shore A (bumper/edge cover, non-safety) | Angst+Pfister APSOseal 1025058803 product page (official; no PDF exists): ../docs/fonti/AngstPfister_APSOseal_1025058803_EPDM_finger-protection-profile_product_page_2026-10-05.txt | "1025058803 / 70 ±5 Shore A / 335 g/m / … 25.00 x 20.00 mm" (table cells) | **PRICE-ONLY** | - | rev B4: P/N fixed; price behind login (quote) | QUOTE → QUOTE needed | yes |
| 2 | `D01_ezwheel_SWD125_*` | 2 | Y | 4:1, 7.9 Nm nom / 13 Nm peak, 380 rpm, 200 W S1, 250 kg static / 200 kg @ 6 km/h, L 196 mm + 7 kg with brake, STO PL e Cat 4 PFHd 1.42E-9, SLS/SLSa/SDI pair PL d Cat 3 2.29E-7, UV/OV/OC thresholds, 0..+40 C | ez-Wheel SWD manual v2.0.2 p.13, p.28, p.34, p.89-90 (docs/fonti/ezwheel_SWD_user_manual_v2.0.2_EN.pdf); datasheet EW2A-125HN04x 07/2024 (docs/fonti/ezwheel_EW2A-125HN04x_datasheet_2024-07.pdf) | "Nominal performance 7.9 Nm at 380 rpm" "Peak torque 13 Nm" (p.13); "111 ✓ 196 7" (p.28, 1-stage + brake: L 196 mm, 7 kg); "Safe Torque Off (STO) STO1 et STO2 inputs Category 4 PL e 1,42E-9"; "Safely limited speed (SLS) Pair of SafeInput Category 3 PL d 2,29E-7" (p.89); "250 kg (static) 200 kg at 6 km/h"; "Temperatures 0 to +40 °C" (datasheet) | **DOCUMENTED** | TP-01 (SFRT), TP-03a/03b (brake), TP-03/14 (regen) | rev B4: CAD at L 196 mm coaxial, 7.0 kg (F4 closed); SWD in its own tunnel on room air at a rated room 0..+35 °C (F3 closed, TP-11). EU DoC/DoI 2024-04-01 + INERIS EC type-examination 0080.5493 520 03.22.0075 Ext 001.09.23 saved (G-28). Datasheet typo "7,9 daN" noted | SECONDARY → public | yes |
| 3 | `C01_castor_*_Blickle_L-ALST_80K` | 4 | Y | D80 x 30 Softhane 75 ShA, 200 kg @ 4 km/h, 500 kg static, H 102, plate 100 x 85, holes 80 x 60 d9, offset 38, 0.7 kg, -20..+70 C | blickle.com/product/l-alst-80k-754464 (docs/fonti/Blickle_L-ALST_80K_754464_product_page_2026-10-05.txt); public 3D model PDF https://cdn.blickle.info/7/75/754/754464/l-alst_80k_754464.pdf (docs/fonti/Blickle_L-ALST_80K_754464_3D-model.pdf, new) | "Load capacity at 4 km/h 200 kg … Load capacity (static) 500 kg … Total height (H) 102 mm … Plate size 100 x 85 mm … Bolt hole spacing 80 x 60 mm … Offset (F) 38 mm … Unit weight 0.7 kg"; guide: "capable of exceeding speeds of 4 km/h with a reduced load capacity" | **PRICE-ONLY** | TP-23 (swivel radius 360°), TP-22 (rolling) | rev B4 (G-04 closed): top speed capped at 1.1 m/s = 3.96 km/h ≤ the 4 km/h rating point, so the published 200 kg applies (CALC §3 row). Swivel radius 79.4 mm calculated → TP-23. Price: QUOTE | QUOTE → QUOTE needed | yes |
| 4 | `C03_bump_pad_*` | 4 | Y | PU pad 30x30x3 die-cut from APSOplast PUR D15 90A sheet (end stop) | Angst+Pfister APSOplast PUR D15 90A technical data sheet (../docs/fonti/AngstPfister_APSOplast_PUR-D15-90_0125103030_technical_data_sheet.pdf) | "Hardness test value 95 Shore A ISO 868"; "Compression set (25% def.) 20 % … 24 h, 70 °C"; "Tensile tear strength 43 N/mm²" | **PRICE-ONLY** | - | rev B4: sheet 0125103030 (sold as 90 ±5 A, tested 95 A); 0.9 MPa contact pressure; TP-23 checks the stop; price quote | QUOTE → QUOTE needed | yes |
| 5 | `C04_springs_D-313J-02` | 8 | Y | d 3.6, De 31.6, Dd 23.6, L0 53.9 ±1.44, R 14.172 N/mm, Fn 327.71 N, Fndyn 300.88 N, Ln 30.78, EN 10270-1 | Gutekunst D-313J-02 datasheet (docs/fonti/Gutekunst_D-313J-02_compression_spring_datasheet.pdf); federnshop.com/en/products/compression_springs/d-313j-02.html | "R 14,172" "Fn 327,71" "Fndyn 300,88" "Ln 30,78" "L0 53,90 + 1,44" "EN 10270-1"; "1 12,3700 € / 17 1,6600 € / 37 1,3900 €" | **DOCUMENTED** | TP-23 (preload per corner) | price public (SOURCED) | SOURCED → public | yes |
| 6 | `C06_droop_stop_*` | 4 | Y | rubber buffer Ganter GN 351-20-15-M6-SS-55 (NR 55 Shore) + 4 mm angle (droop stop, ~5 N) | Ganter GN 351 data sheet + load ratings (../docs/fonti/Ganter_GN351-20-15-M6-SS-55_datasheet_and_load_ratings.pdf) | 55 Shore, SS 20x15: "130 [N/mm] 480 [N] 3,75 [mm]"; "Natural rubber (NR)"; "-40 °C to +80 °C" | **PRICE-ONLY** | - | rev B4: the 20 x 10 size does not exist: 20 x 15, angle 5 mm lower (same stop face); 480 N ≫ 5 N; price quote | QUOTE → QUOTE needed | yes |
| 7 | `C07_rail_MGN15R_L190` | 4 | Y | MGN15 rail WR 15, HR 10, P 40, E 15, M3x10, 1.06 kg/m; rail bolt torque in aluminium 98 N·cm | HIWIN catalogue G99TE24-2410 p.91 (docs/fonti/HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p1_p91_MGN.pdf) + p.87 (docs/fonti/HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p87_MGN_bolt_torque.pdf, new) | "16 4 8.5 32 25 3.5 4.5 M3 M3x4 3 15 10 6 4.5 3.5 40 15 M3x10 1.06" (p.91); "MGN15 M3×0.5P×10L 186 (19) 127 (13) 98 (10)" (p.87, Iron/Casting/Aluminum) | **PRICE-ONLY** | - | price QUOTE (no public price). The 98 N·cm torque quoted in CASTOR_SUSPENSION was not in the saved extract: p.87 now saved | QUOTE → QUOTE needed | yes |
| 8 | `C08_blocks_MGN15H` | 8 | Y | MGN15H: C 6.37 kN, C0 9.11 kN, MR 73.5 N·m, MP/MY 57.82 N·m, 0.092 kg, block bolts M3 186 N·cm | HIWIN G99TE24-2410 p.91, p.87 (docs/fonti) | "MGN 15H 25 43.4 58.8 59.4 6.37 9.11 73.50 57.82 57.82 0.092" | **PRICE-ONLY** | - | price QUOTE | QUOTE → QUOTE needed | yes |
| 9 | `C09_castor_fasteners_set` | 1 | Y | M8x16 ISO 10642 10.9, M3x10/M3x8, M6, Loctite 243 | ISO 10642 / ISO 4762 (standard parts) | standard designation | **DOCUMENTED** | - | standard parts defined by ISO designation; property class 10.9 per ISO 898-1 (see CALC M-rows). Price ESTIMATE (catalogue item, quote-free shops exist) | ESTIMATE → QUOTE needed | - |
| 10 | `B01_battery_*_DLP-GC2-48V` | 2 | Y | 51.2 V 30 Ah 1536 Wh, 260 x 180 x 254 (275 incl. terminals), 14 kg, 15 A cont / 58 A 1 h / 90 A 10 s, LVD rec. 48 V, fuse 60 A, 23 mF precharge, lying allowed, >= 50 mm at top cover, <= 20 in parallel, IEC 62619 CB, UN 38.3, CE (EMC+RoHS) | Discover 805-0027 Rev N Table 3-1/3-2 p.4(6-7), §9.2 p.10-11, §3.6 (docs/fonti/Discover_DLP-GC2_Installation_Operation_Manual_805-0027_RevN.pdf); CB cert DK-142118-A1-UL; EU DoC 830-0047; product page .txt | "Max Continuous Discharge Current b … 15 A"; "Max Discharge Current (1 hour) … 58 A"; "Peak Discharge Current (10 seconds) … 90 A RMS"; "Low Voltage Disconnect Recommended … 48.0 V"; "Fuse … 58 V 60 A"; "Do not install upside down."; "Maintain at least 50 mm (2 in)"; "Total Height 275 mm"; "IEC 62619:2022"; DoC: "2014/30/EU EMC Directive" "2011/65/EU" | **DOCUMENTED** | TP-14 (Isc bound, BMS), TP-22 (vibration) | price: USD 1,009 from CONTEXT.md only, BOM tags it ESTIMATE -> quote/public list needed. Note: product page gives peak 90 A for 3 s, manual 10 s: use 3 s (conservative). UN 38.3 summary is not in docs/fonti (cert list only) | ESTIMATE → QUOTE needed | yes |
| 11 | `G01_lynk_gateway` | 1 | Y | P/N 950-0025, 120 x 135 x 44 mm, 13-90 V, CE, IP20 indoor, -20..50 C; relays 0-30 V DC 5 A, R1 NO/NC, R2/R3 NO | LYNK II sell sheet 885-0035 p.2; LYNK II Relay Guide §3.1 p.6, §4.1 p.7 (docs/fonti) | "Part Number 950-0025"; "LxWxH 120 x 135 x 44 mm"; "13 - 90 V"; "Marking CE"; "IP20 (Indoor Use Only)"; "The relays allow 0 to 30 VDC at a maximum of 5 A" | **PRICE-ONLY** | TP-14 (relay chain) | no public price (BOM 350 ESTIMATE). Power draw not published (minor, S24 budget: 0.4 A allowance covers it per netlist; measure TP-14) | ESTIMATE → QUOTE needed | yes |
| 12 | `S01_nanoScan3_ProIO_*` | 2 | Y | Type 3, PL d, SIL 2, PFHd 8.0E-8, tR 70 ms (n=2), field 3 m, TZ 65 mm, 16.8-30 V, 3.9 W / 15.9 W, 0.67 kg, 106.6 x 80 x 117.5 incl. plug, plane 50.5 mm, IP65, -10..+50 C, shipped without system plug | SICK data sheet NANS3-CAAZ30AN1 p.2-5 (docs/fonti/SICK_NANS3-CAAZ30AN1_datasheet_1100334.pdf); OI 8024596 p.130-137 (extracts in docs/fonti) | "Performance level PL d (EN ISO 13849)"; "PFHD … 8.0 x 10-8"; "Response time 70 ms"; "Protective field supplement 65 mm"; "Model Sensor without system plug"; "Dimensions (W x H x D) 106.6 mm x 80 mm x 117.5 mm (including system plug)"; "With maximum output load Typ. 15.9 W" | **DOCUMENTED** | TP-05/05b (plane), TP-01 (stop) | price SECONDARY (surplus dealer, warranty = dealer's). TÜV type-examination certificate not saved in docs/fonti (DoC/cert download on sick.com) - see G-28 | SECONDARY → public | yes |
| 13 | `S02_nanoScan3_system_plug_*` | 2 | Y | NANSX-AAACZZZZ1 (2105107), 300 mm cable, supply + I/O, no Ethernet | SICK OI 8024596 p.143 (extract p.16) | "nanoScan3 Pro I/O 1100334 … Cable with plug connector … NANSX-AAACZZZZ1 2105107" | **DOCUMENTED** | - | price SECONDARY (eibabo) | SECONDARY → public | yes |
| 14 | `E02_estop_*` | 2 | Y | E-stop 40 mm mushroom twist-release, ISO 13850, + holder 3 modules + 2x NC 3SU1400-1AA10-1CA0 positive opening, 10 A thermal | Siemens data sheets 3SU1050-1HB20-0AA0, 3SU1500-0AA10-0AA0, 3SU1400-1AA10-1CA0 (../docs/fonti/Siemens_3SU1050-1HB20-0AA0_datasheet.pdf etc., Siemens mall datasheet generator) | "EMERGENCY STOP mushroom pushbutton, 22 mm, round, metal, shiny, red, 40 mm, positive latching, acc. to EN ISO 13850, rotate-to-unlatch"; "mechanical service life (operating cycles) typical 300 000"; "B10 value with high demand rate according to SN 31920 100 000"; NC module "positive opening Yes"; holder "holder, 3-fold, plastic" | **DOCUMENTED** | - | rev B4 (G-06 closed): official Siemens data incl. B10 (the netlist PFHd 5E-8 stays an estimate until SISTEMA). The datasheet cites EN ISO 13850, not IEC 60947-5-5. ES3 yellow enclosure/label still required | SECONDARY → public (BOM €33.56: eibabo + RS) | yes |
| 15 | `E41_SB1_reset_blue` | 1 | Y | blue illuminated reset, 1 NO (PNOZ input, mA level) | Eaton M22-DL-B (216931) and M22-K10 (216376) specification sheets (../docs/fonti/Eaton_M22-DL-B_216931_specifications.pdf, Eaton_M22-K10_216376_specifications.pdf; eaton.com skuPage PDFs) | "MODEL CODE M22-DL-B", "LIFESPAN, MECHANICAL 5,000,000 Operations", "DEGREE OF PROTECTION (FRONT SIDE) IP67/IP69K", "IEC 60947-5"; M22-K10 "RATED OPERATIONAL CURRENT (IE) AT DC-13, 24 V 3A" | **DOCUMENTED** | - | rev B4 (G-07 closed) | SECONDARY → public (BOM €12.83 eibabo net) | yes |
| 16 | `E41_SK1_key_selector` | 1 | Y | 3-position key selector (AUTO/MANUAL/SERVICE), 2 contacts | Eaton M22-WRS3 (216900) + M22-K10 specification sheets (../docs/fonti/Eaton_M22-WRS3_216900_specifications.pdf) | "M22 Key-operated actuator, maintained, 3 positions, Key withdrawable: I, 0, II"; "LIFESPAN, MECHANICAL 100,000 Operations"; "IP66" | **DOCUMENTED** | - | rev B4 (G-07 closed) | SECONDARY → public (BOM €52.64 eibabo net) | yes |
| 17 | `E41_SE1_M12_pendant_socket` | 1 | Y | M12 A-coded 5-pole panel socket (matches the Euchner pendant plug) | binder 76 0632 1011 00005-0200 data sheet (../docs/fonti/Binder_76-0632-1011-00005-0200_M12-A_female_panel_5pin_datasheet.pdf) | "DIN EN 61076-2-101"; "A-coded"; "IP68/IP69K"; "Rated voltage 60 V"; "Rated current 4 A (3 A UL)" | **PRICE-ONLY** | - | rev B4 (G-08 closed with the pendant): 5-pole, not 8-pole | QUOTE → QUOTE needed | yes |
| 18 | `SE1_enabling_pendant` | 1 | Y | 3-position enabling switch EN 60947-5-8, 2 channels (E1/E2), Cat 3, B10D 3.9E5, IP67, M12 5-pole plug | Euchner ZSA2B4G02CC2322 (169871) / ZSA2B4G10CC2322 (110560): operating instructions 2092781 + data sheet 2127401 (../docs/fonti/Euchner_ZSA-ZSR_operating-instructions_EN_2092781.pdf) | "three-position enabling switch according to EN 60947-5-8"; "2-channel evaluation … category 3 as per EN ISO 13849-1"; "B10D at DC13 400 mA / 24 V — 3.9 x 10^5"; "ZSA2A, ZSA2B — IP67" | **PRICE-ONLY** | - | rev B4 (G-08 closed): no jog buttons on this switch (jog via the HMI while SE1 is held); BOM €500 (distributor range €460-520 net), quote | QUOTE → QUOTE needed | yes |
| 19 | `HL1_signal_tower` | 1 | Y | 24 V signal tower + buzzer: 3 tiers, 2.5 W typ, 93 dB, IP54 | Patlite WME-302DFB-RYG spec (docs/fonti/Patlite_WME-DFB_signal_tower_spec_WME-D-W18.pdf, new); patlite.com/product/detail0000000692.html | "Rated Voltage 24V DC"; "Buzzer 1.0W"; "Sound Pressure Level (Typ.) 93dB"; "Protection Rating IP54 (IEC 60529)"; "Mounting Location Indoor Only" | **PRICE-ONLY** | - | closed by fixing the P/N to Patlite WME-302DFB-RYG (BOM/netlist still say 'Werma/Patlite class': update the P/N). Price: quote | ESTIMATE → QUOTE needed | yes |
| 20 | `E01_robopad_collector_RPCOL90` | 1 | Y | RPCOL90-100, passive, 60 A cont, 75 A 80 s on/60 s off, 60 V max even under fault, ±5 mm L/R, cables <= 2 m, 0-40 C | Roboteq RoboPad datasheet v1.3 p.2, p.7, p.14-15 (docs/fonti/Roboteq_RoboPad_Datasheet_v1.3.pdf) | "RPCOL90-100 RoboPad Extendable Collector, 90mm wide, 100A"; "Continuous Current 60 A"; "shall ensure that the voltage does not exceed 60 V DC even under under fault conditions"; "External cable lengths shall have a maximum length of 2 m" | **PRICE-ONLY** | - | price ESTIMATE (set USD 400-900) -> quote | ESTIMATE → QUOTE needed | yes |
| 21 | `E03_service_disconnect_ED250B` | 1 | Y | ED250B-L: 250 A Ith, breaks 1000 A at 96 V DC, key-lockable, no-load isolator only | Albright ED250 data sheet (docs/fonti/Albright_ED250_datasheet.pdf) | "Thermal Current Rating (Ith) 250A"; "ED250B 1000A at 96V D.C."; "Lockable ○ L"; "Do not use as a regular On-Load Switching Device." | **PRICE-ONLY** | - | price ESTIMATE -> quote | ESTIMATE → QUOTE needed | yes |
| 22 | `E10_F0_fuse_NH00_100A` | 1 | Y | 3NA3830 NH000 100 A gG, 250 V DC, 25 kA DC (tau <= 10 ms) + NH00 base 3NH3030 | Siemens 3NA3830 data sheet p.1 (docs/fonti/Siemens_3NA3830_datasheet.pdf) | "LV HRC fuse element, NH000, In: 100 A, gG, Un AC: 500 V, Un DC: 250 V"; "breaking capacity at DC with time constant ≤ 10 ms 25 kA" | **DOCUMENTED** | - | fuse link and base DOCUMENTED: 3NH3030 "LV HRC fuse base Sz. 00, 1-pole 160 A 690 V", "at DC rated value 25 kA" (../docs/fonti/Siemens_3NH3030_datasheet.pdf, rev B4). Price ESTIMATE (public distributor price exists) | ESTIMATE → QUOTE needed | yes |
| 23 | `E11_K0_contactor_SW80B_on_plate` | 1 | Y | SW80B…A: Ith 100 A / 125 A, 96 V DC with blowouts, breaks 600 A at 96 V, continuous coil 7-13 W, drop-out 50 ms with diode, aux 5 A | Albright SW80 data sheet (docs/fonti/Albright_SW80_datasheet.pdf) | "Thermal Current Rating (Ith) 100A 125A"; "SW80B 600A at 96V"; "SW80B 96V D.C."; "Continuously Rated Types 7 - 13 Watts"; "With Diode Suppression 50ms"; "Auxiliary Thermal Current Rating 5A" | **PRICE-ONLY** | - | price ESTIMATE -> quote | ESTIMATE → QUOTE needed | yes |
| 24 | `E12_K0P_precharge_relay` | 1 | Y | Finder 22.32.0.024.4340 (DC1 5 A @110 V, coil 2.2 W) + Vishay Dale RH-50 47R (50 W on heat sink, 5 x rated power for 5 s); precharge 1.24 A, 3.4 J | Finder S22EN p.7/p.11 + Vishay Dale RH datasheet 30201 (../docs/fonti/Vishay-Dale_RH-NH_RH-50_aluminum-housed_datasheet_30201.pdf) | "Breaking capacity DC1: 24/110/220 V A 25/5/1"; RH050 "RH-50 50 … 0.1 to 96K"; "Short time overload 5 x rated power for 5 s" | **PRICE-ONLY** | - | rev B4 (G-25 closed): Arcol HS50 replaced by Vishay RH-50 because the Arcol/Ohmite HS datasheet (saved) publishes no overload/pulse rating; 3.4 J ≪ 5 x 20 W (free air) x 5 s = 500 J | ESTIMATE → QUOTE needed | yes |
| 25 | `E17_K0T_timer_Finder80` | 1 | Y | on-delay 0.6 s (range 0.1-2 s), supply 12-240 V AC/DC, 16 A, DC1 16 A @24 V (K0 coil <= 0.54 A), -20..+60 C | Finder S80EN p.3, p.8 (docs/fonti/Finder_80-01_datasheet_S80EN_p3_p8.pdf, new) | "Rated current/Maximum peak current A 16/30"; "Breaking capacity DC1: 24/110/220 V A 16/0.3/0.12"; "240 = (12…240)V AC/DC"; "Specified time range (0.1…2)s"; "AI: On-delay" | **PRICE-ONLY** | - | BOM 'DoC (IEC 61812-1)': standard not stated in the extract - cite datasheet values. Inductive DC13 rating not given: SW80 coil has a freewheel diode (D0), so DC1 applies. Price ESTIMATE | ESTIMATE → QUOTE needed | yes |
| 26 | `E18_branch_fuses_10x38_x7` | 1 | Y | Mersen HP10M gPV 10x38 in CUS101HEL holders: F1 6, F2 20, F3/F4 20, F5L/R 15 (OA) / 25 (C48) A; 1000 V DC; holder 32 A 1000 V DC | Mersen HP10M datasheet, HelioProtection brochure p.8-9, time-current curve 720877, CUS101HEL datasheet K1062724 (../docs/fonti/Mersen_HP10M_gPV-10x38-1000VDC_datasheet.pdf etc.) | "Volts: 1000VDC", "Amps: 1 to 32A", "I.R.: 50kA I.R. DC", "Photovoltaic Fuse, gPV", "IEC 60269-6 Approved"; brochure "MAXIMUM BREAKING CAPACITY = 10KA"; holder "Voltage DC 1000 VDC", "Ith 32 A" | **DOCUMENTED** | - | rev B4 (G-13 closed): all P/Ns fixed. IEC breaking capacity 10 kA DC is below the undocumented 20 kA Isc design bound (V:D6): new G-29 (measure Isc, TP-14). No 16 A rating (F2 → 20, F5 → 15) | SECONDARY → public | yes |
| 27 | `E31_F8LR_SWD_fuses` | 1 | Y | F8L/F8R HP10M20 gPV on T24 | Mersen HP10M datasheet (as E18) | as E18 | **DOCUMENTED** | - | rev B4 (G-13): gG → HP10M20 gPV | SECONDARY → public | - |
| 28 | `E33_F7_charge_fuse` | 1 | Y | F7 HP10M32 gPV on B48 (11.3 A charger, 25 A option) | Mersen HP10M datasheet (as E18) | "32 HP10M32* H1062170" | **DOCUMENTED** | - | rev B4 (G-13) | SECONDARY → public | - |
| 29 | `E2F_WF1-3_AUX48_fuses` | 1 | Y | WF1 HP10M6 / WF2 HP10M12 / WF3 HP10M2 on B48 + FJ HP10M4 on 12 V (Jetson J4012, 3.3 A, maker supply 12 V 5 A) | Mersen HP10M datasheet (as E18) | ratings list incl. "4 HP10M4*", "6 HP10M6*", "12 HP10M12*" | **DOCUMENTED** | - | rev B4 (G-13): FJ 8 A gG → HP10M4 (coordination with the 5 A Jetson supply) | SECONDARY → public | - |
| 30 | `E13_U1_dcdc_DDR480C24` | 1 | Y | 24 V 20 A, 30 A 5 s, 33.6-67.2 V in, 92 %, OVP 28.8-35 V, 85.5 x 125.2 x 129.2, vertical only, IEC 62368-1 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | "RATED CURRENT … 20A" (C-24); "CURRENT 5sec. … 30A"; "VOLTAGE CONTINUOUS … 33.6 ~ 67.2Vdc"; "EFFICIENCY (Typ.) … 92%"; "OTHERS DIMENSION 85.5*125.2*129.2mm"; "=(The rated current per unit) x (Number of unit) x 0.9"; "Open or 5.5 ~ 10VDC power supply ON / Short or 0 ~ 0.8VDC power supply OFF"; "SAFETY STANDARDS UL 62368-1, IEC 62368-1"; manual: "mounting orientation … vertical", "40mm above and 20mm below" | **DOCUMENTED** | - | price SECONDARY (DigiKey) | SECONDARY → public | yes |
| 31 | `E14_U2_dcdc_DDR480C24` | 1 | Y | as U1 (parallel, 2 x 20 x 0.9 = 36 A) | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 32 | `E15_U4_dcdc_DDR240C24_S24` | 1 | Y | 24 V 10 A, 15 A / 360 W 3 s, 40 x 125.2 x 113.5, max 50 C (installation manual) | Mean Well DDR-240-SPEC p.2 + installation manual p.4 (docs/fonti) | "RATED CURRENT 10A"; "360W (3sec.)"; "DIMENSION 40*125.2*113.5mm"; "50°C for DDR-240 series" | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 33 | `E2G_U5_DDR120C12` | 1 | Y | 12 V 10 A, 15 A 3 s, 33.6-67.2 V, 32 x 125.2 x 102, max 55 C | Mean Well DDR-120-SPEC p.2-3 (docs/fonti) | "RATED CURRENT … 10A"; "PEAK CURRENT … 15A"; "33.6 ~ 67.2Vdc"; "DIMENSION 32*125.2*102mm"; "55°C for DDR-120 series" | **DOCUMENTED** | - | rev B4: TME price in the BOM (SECONDARY) | SECONDARY → public | yes |
| 34 | `E16_R1_maxon_DSR50-5_x2` | 2 | Y | 12-50 V, threshold 26.1-27.1 V (JP1 open) or 54.3-56.1 V, max current 5 A, R_shunt 5.5 Ω -> ~133 W at 27 V per unit (300 W only on the 56 V setting), 10 W continuous at 25 C derating to 0 W at 75 C, 940 µF, 94 x 41 x 35, ~60-75 g | maxon DSR 50/5 operating instructions 2015-04 p.3, 7, 8 (docs/fonti/maxon_DSR50-5_309687_Operating_Instructions_2015-04.pdf, new, scanned) + maxongroup.com/maxon/view/product/309687 | "Threshold voltage Vth (JP1: open) 26.1...27.1 VDC"; "Max. continuous power loss Pcont without additional cooling at TU=25°C 10 W"; "Max. current 5 A"; "Once the over-temperature deactivation is enabled the supply voltage cannot be limited anymore." | **DOCUMENTED** | TP-03/TP-14 (worst regen) | price public (maxon EUR 145.15 @1-4). Findings F6: VERIFICATION MX1 used 300 W, but at 27 V each unit sinks <= 5 A (~133 W): 2 units ~265 W still >= 208 W peak; continuous ~6 W at 45 C bay; no CE statement in the manual (netlist 'CE [ASSUMED]' -> none) | SOURCED → public | yes |
| 35 | `E30_U3_ORing_DRDN40-24` | 1 | Y | 2 x 40 A in, 60 A 5 s, reverse current <= 1 mA, 55 x 125.2 x 100 | Mean Well DRDN40-SPEC p.2 (docs/fonti) | "RATED CURRENT 0~40A per input Continuous"; "PEAK CURRENT 0~60A per input 5Sec."; "INPUT REVERSE CURRENT (max.) 1mA"; "DIMENSION 55*125.2*100mm" | **DOCUMENTED** | - | rev B4: RS price in the BOM | SECONDARY → public | yes |
| 36 | `E34_U8_ideal_diode_DRDN40-48` | 1 | Y | DRDN40-48: 36-60 V, 40 A per input, reverse 65 V, single input | Mean Well DRDN40-SPEC p.2, p.4 (docs/fonti) | "INPUT REVERSE VOLTAGE (max.) 40Vdc 40Vdc 65Vdc"; "3. Single Use" | **DOCUMENTED** | - | rev B4: RS price in the BOM | SECONDARY → public | yes |
| 37 | `E19_0V_block` | 1 | Y | 0 V distribution block 2x25 / 6x10 mm2 | Weidmüller WPD 100 2X25/6X10 GY data sheet (../docs/fonti/Weidmueller_1561910000_WPD-100-2X25-6X10-GY_datasheet.pdf) | "Nominal current 101 A", "Rated voltage 1000 V", "Rated cross-section 25 mm²", "IEC 60998-2-1" | **DOCUMENTED** | - | rev B4: official datasheet; netlist 125 A → 101 A (≥ F0 100 A) | SECONDARY → public (BOM €36.02) | yes |
| 38 | `E27_XS24_terminals` | 1 | Y | S24 fuse terminals 5x20 (4/2/4/2/2/1 A) + feed-through + bridges | Phoenix PT 4-HESI (5X20) 3211861 data sheet (../docs/fonti/PhoenixContact_3211861_PT-4-HESI_datasheet.pdf) | "Nominal current 6.3 A (the current is determined by the fuse used)", "Nominal voltage 500 V", "fuse type: G / 5 x 20" | **PRICE-ONLY** | - | rev B4: official datasheet; 5x20 links: catalogue items (non-safety S24 sub-fuses); price quote | ESTIMATE → QUOTE needed | - |
| 39 | `E32_T24_terminals` | 1 | Y | T24 power terminals Phoenix PT 16 N (3212138), up to 36 A cont / 54 A peak | Phoenix PT 16 N data sheet (../docs/fonti/PhoenixContact_3212138_PT-16-N_datasheet.pdf) | "Nominal current 76 A", "Nominal voltage 1000 V", "Rated cross section: 16 mm2" | **PRICE-ONLY** | - | rev B4 (G-21): PTPOWER 16 → PT 16 N, 76 A ≥ 54 A | ESTIMATE → QUOTE needed | yes |
| 40 | `E35_RSIG_X0R` | 1 | Y | Vishay PR02 10 kΩ 2 W (0.34 W at 58.4 V) in a component terminal | Vishay PR01/PR02/PR03 datasheet 28729 (../docs/fonti/Vishay_PR01-PR02-PR03_datasheet_28729.pdf) | "Rated dissipation, P70 … PR02 2W" | **PRICE-ONLY** | - | rev B4 (G-21): order code PR02000201002JA100 | ESTIMATE → QUOTE needed | yes |
| 41 | `E37_KS_signature_relay` | 1 | Y | Finder 38.51.7.024.0050: coil 10.4 mA / 0.3 W at 24 V (<= 75 mA PNOZ aux), contact 6 A, DC1 6 A @24 V, min load 500 mW | Finder S38EN p.5, p.13 (docs/fonti/Finder_38-51_datasheet_S38EN_p5_p13.pdf, new) | "Rated current/Maximum peak current A 6/10"; "Breaking capacity DC1: 24/110/220 V A 6/0.2/0.12"; "24 7.024 19.2 28.8 10.4 0.3"; "35 mm rail (EN 60715)" | **PRICE-ONLY** | - | netlist coil 9 mA [ASSUMED] -> 10.4 mA (documented). Check: the KS contact switches the 10 kΩ signature at up to 58 V = 5.8 mA, below the 500 mW (10 mA @12 V) minimum switching load -> contact reliability, not safety; use a gold-contact variant if TP-13 shows flicker | ESTIMATE → QUOTE needed | yes |
| 42 | `E36_CAN1_PCAN-Ethernet_gw` | 1 | Y | IPEH-004010: 2x HS-CAN ISO 11898-2, 8-30 V (100-360 mA), 22.5 x 99 x 114.5 mm, IP20, -40..85 C, CE (EN 55032/55035) | PEAK user manual 2.1.0 p.64-66 (docs/fonti/PEAK_PCAN-Ethernet_Gateway_DR_UserMan_2.1.0_p1-6-64-66.pdf, new) + price list (docs/fonti/PEAK_Pricelist_valid_2026-08-21.pdf, new) | "Supply voltage 8 to 30 V DC"; "Max. current consumption 360 mA at 8 V, 240 mA at 12 V, 100 mA at 30 V"; "EMC EU Directive 2014/30/EU DIN EN 55032:2022-08 DIN EN 55035:2018-04"; price list IPEH-004010 EUR 294.00 net EXW | **DOCUMENTED** | - | rev B4: BOM price €294 SOURCED; CAD envelope 22.5 x 99 x 114.5 (M7 closed), right HIGH rail end | ESTIMATE → public (found in this audit: PEAK price list EUR 294.00 net) | yes |
| 43 | `E25_NET1_switch_FL1008N` | 1 | Y | 8-port switch, 9-32 V DC, 28 mA at 24 V, 22.5 x 140.4 x 92.4 mm | Phoenix FL SWITCH 1008N 1085256 data sheet (../docs/fonti/PhoenixContact_1085256_FL-SWITCH-1008N_datasheet.pdf) | "Supply voltage range 9 V DC ... 32 V DC", "Typical current consumption 28 mA (at 24 V DC)", "Height 140.4 mm" | **DOCUMENTED** | - | rev B4 (G-21, M13 closed): real size in CAD (own rail z 164: too tall for the HIGH rail) | SECONDARY → public (BOM €141.86) | yes |
| 44 | `E26_SR1_RLY3-OSSD100` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | ESTIMATE → QUOTE needed | - |
| 45 | `E2C_K1_contactor_3RT2026` | 1 | Y | DC-1 35 A (2 poles in series, 60 V), coil 5.9 W, mirror contacts, B10 1E6 / 73 % -> B10D 1.37E6, 45 x 85 x 107 | Siemens 3RT2026-1BB40 data sheet p.2-6 (docs/fonti/Siemens_3RT2026-1BB40_datasheet.pdf) | "with 2 current paths in series at DC-1 … at 60 V rated value 35 A"; "holding power of magnet coil at DC 5.9 W"; "mirror contact according to IEC 60947-4-1 Yes"; "B10 value with high demand rate according to SN 31920 1 000 000" with "73 %" dangerous share (B10D = 1.37E6); "width 45 mm" "depth 107 mm" | **DOCUMENTED** | - | rev B4: BOM price RS €202.10 (SECONDARY); B10D 1.37E6 in the netlist | SECONDARY → public | yes |
| 46 | `E2D_K2_contactor_3RT2026` | 1 | Y | as K1 | Siemens 3RT2026-1BB40 data sheet p.2-6 (docs/fonti/Siemens_3RT2026-1BB40_datasheet.pdf) | as E2C | **DOCUMENTED** | - | as K1 | SECONDARY → public | yes |
| 47 | `E0x_din_rails` | 1 | Y | TS35 x 7.5 per EN 60715, 10 pieces | Phoenix NS 35/7,5 via eibabo.de; EN 60715 cited in Finder S38EN | "NS 35/7,5 Unperf 2m"; "35 mm rail (EN 60715)" | **DOCUMENTED** | - | standard section; price public (EUR 9.54 gross per 2 m) | ESTIMATE → public (found in this audit: eibabo NS 35 EUR 9.54 gr / 2 m) | - |
| 48 | `E0C_centre_rails` | 2 | Y | TS35 EN 60715, 2 x 154 mm at z 213 (rev B4: one per spine face) | EN 60715 | - | **DOCUMENTED** | - | rev B4: M3 closed (BOM qty 2 x 154 mm = CAD E0C_L/R_din_rail) | ESTIMATE → QUOTE needed | - |
| 49 | `E58_U6_DDR60L5` | 1 | Y | 5 V 12 A, 18-75 V in, 52.5 x 90 x 54.5 | Mean Well DDR-60-SPEC p.2 (docs/fonti) | "RATED CURRENT … 12A" (DDR-60L-5); "VOLTAGE RANGE … 18 ~ 75Vdc"; "DIMENSION 52.5*90*54.5mm" | **DOCUMENTED** | - | rev B4: RS price in the BOM | SECONDARY → public | yes |
| 50 | `E59_JR1_relays` | 1 | Y | 2x Phoenix EMG 17-OV-TTL/24DC/2 (2943259): TTL input "1" ≥ 2 V at 2.6 mA (Jetson 3.3 V GPIO), output 24 V DC 2 A to the HL1 tiers | Phoenix EMG 17-OV-TTL/24DC/2 data sheet (../docs/fonti/PhoenixContact_2943259_EMG-17-OV-TTL-24DC-2_datasheet.pdf) | "Switching threshold "1" signal voltage 2 V (TTL)"; "Typical input current at UN 2.6 mA"; "Auxiliary voltage TTL input 5 V DC ±20 %"; "Limiting continuous current 2 A" | **PRICE-ONLY** | - | rev B4 (G-22 closed): 5 V aux from U6; price quote | ESTIMATE → QUOTE needed | yes |
| 51 | `E5A_XC_deck_terminals` | 1 | Y | feed-through terminals PT 1.5 / PT 4 (cross-section only) | Phoenix catalogue (not retrieved) | - | **PRICE-ONLY** | - | only cross-section is used; currents <= 16 A coffee, 5 V head. Attach the Phoenix PT datasheet at order (evidence upgrade) | ESTIMATE → QUOTE needed | - |
| 52 | `E40_fan_*` | 4 | Y | San Ace 9WPA0624S4001 60x60x25 24 V IP68: 0.99 m³/min free air, 151 Pa, 4.08 W (50 % effective through the filters ASSUMED, TP-11) | Sanyo Denki San Ace catalogue C1152B001 p.371-373, 625 (../docs/fonti/SanyoDenki_9WPA0624S4001_9WPA0424H6001_9WPA0824H4001_catalog_C1152B001_p1-362-364-371-373-377-379-625.pdf) | "9WPA0624S4001 24 V … 0.17 A, 4.08 W, 7800 min-1, 0.99 m3/min … 151 Pa … -20 to +70 ˚C, 40000/60˚C"; "Ingress protection IP68" | **PRICE-ONLY** | - | rev B4 (G-10 closed); also the 2 tunnel fans E44 | ESTIMATE → QUOTE needed | yes |
| 53 | `E42_gap_fan_*` | 2 | Y | San Ace 9WPA0424H6001 40x40x20 24 V IP68: 0.24 m³/min, 81 Pa, 0.9 W | San Ace catalogue C1152B001 p.362-364 (as E40) | "9WPA0424H6001 24 … 0.038 A, 0.9 W, 8800 min-1, 0.24 m3/min … 81 Pa" | **PRICE-ONLY** | - | rev B4 (G-10 closed) | ESTIMATE → QUOTE needed | yes |
| 54 | `E21_SC0_PNOZ_m_B0` | 1 | Y | 20 safe in, 4 SC out 2 A (0-2.5 A, <= 1 µF), 4 configurable aux outputs 75 mA, PL e Cat 4, PFHd CPU 4.74E-10 / SC out 1.66E-11 / in 7.95E-11, 1.6 A supply, test pulse <= 330 µs, terminals 751008 not included | Pilz PNOZ m B0 manual 1002660-EN-13 p.8, p.29, p.44-48, p.52 (docs/fonti/Pilz_PNOZ_m_B0_OperManual_1002660-EN-13.pdf) | "CPU 2-channel PL e Cat. 4 SIL 3 4,74E-10"; "SC outputs … PL e Cat. 4 SIL 3 1,66E-11"; "Two loads may be connected to each safety output with advanced fault detection"; "Output current 75 mA"; "supply must provide 1,6 A"; "Max. duration of off time during self test 330 µs" | **DOCUMENTED** | - | price SECONDARY (eibabo). TÜV certificate not saved locally (see G-28) | SECONDARY → public | yes |
| 55 | `E22_SX1_PNOZ_m_EF_8DI4DO` | 1 | N | rev B1 reference (not in build) | EF 8DI4DO manual 1002661-EN-08 (docs/fonti) | "CPU 2-channel PL e Cat. 4 SIL 3 2,84E-10" | **EXCLUDED (in_total=N)** | - | in_total = N; BOM source URL is the B0 page (copy-paste) | SECONDARY → public | - |
| 56 | `E20_SC1_PNOZ_m_ES_ETH` | 1 | Y | Modbus/TCP slave, 2x RJ45, standard (non-safety) module, ~1 W | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.458 (extract p.14, docs/fonti) | "Application range Standard"; "Fieldbus interface Modbus/TCP" | **DOCUMENTED** | - | price SECONDARY (BOM source URL points to the B0 page: fix) | SECONDARY → public | yes |
| 57 | `E2H_SR1_PNOZ_m_EF_4DI4DOR` | 1 | Y | 4 safe in, 4 positive-guided relay outputs, DC1 24 V 6 A / min 10 mA, PL e Cat 4 PFH 7.52E-12, 22 ms | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.26-28, p.207-221 (extract p.10-12, docs/fonti) | "Min. current 10 mA"; "Relay outputs 2-channel PL e Cat. 4 SIL 3 7,52E-12"; "tReactionMax = 2 ms + 30 ms + 22 ms = 54 ms"; "772143" | **DOCUMENTED** | - | price SECONDARY (eibabo 379.72 net) | SECONDARY → public | yes |
| 58 | `E2I_SR2_PNOZ_m_EF_4DI4DOR` | 1 | Y | as SR1 | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.26-28, p.207-221 (extract p.10-12, docs/fonti) | as E2H | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 59 | `RB1-10_bleed_resistors` | 10 | Y | Vishay PR01 2.2 kΩ 1 W (0.26 W used), 10 pieces (rev B4: SR3) | Vishay PR01 datasheet 28729 | "Rated dissipation, P70 … PR01 1W" | **PRICE-ONLY** | - | rev B4 (G-21): order code PR01000102201JA100; 100 % rating up to 70 °C (bays ≤ 39 °C) | ESTIMATE → QUOTE needed | yes |
| 60 | `E2J_KI4_interposing_relay` | 1 | Y | PLC-RSC-24DC/21 2966171: 24 V input 9 mA (18.5-33.6 V), contact 6 A 250 V, free-wheel diode | Phoenix PLC-RSC-24DC/21 2966171 data sheet (../docs/fonti/PhoenixContact_2966171_PLC-RSC-24DC-21_datasheet.pdf) | "Typical input current at UN 9 mA", "Limiting continuous current 6A", "Switching capacity 2 A (at 24 V, DC13)", "Freewheeling diode" | **DOCUMENTED** | - | rev B4: official datasheet | SECONDARY → public (BOM €8.69) | yes |
| 61 | `E2K_K0V_LVCO_relay_DUB01CD48500V` | 1 | Y | DUB 01 C D48 500V: ranges 5-50 V (350 V max) / 20-200 V, level 10-110 % FS, hysteresis 0-30 %, delay 0.1-30 s, repeatability ±0.5 % FS, DC13 2.5 A @24 V, 24-48 V supply, 22.5 x 80 x 99.5, EN 60255-6, UL/CSA/CCC | Carlo Gavazzi DUB01/PUB01 data sheet 2025-03-03 p.1-3 (docs/fonti/CarloGavazzi_DUB01-PUB01_datasheet_2025-03-03.pdf) | "DIN-rail SPDT … 2 to 500 V AC/DC … DUB 01 C D48 500V"; "5 to 50 V AC/DC >500 kΩ 350 V"; "Repeatability ± 0.5% on full-scale"; "DC 13 2.5 A @ 24 VDC"; "Dimensions DUB01 22.5 x 80 x 99.5 mm"; "OFF: Normally Energized"; "Product standard EN 60255-6"; "Approvals UL, CSA, CCC" | **DOCUMENTED** | - | price SECONDARY (DigiKey USD 177.65) | SECONDARY → public | yes |
| 62 | `D0_coil_suppression_set` | 1 | Y | Vishay 1N5408 (3 A, 1000 V) across the SW80 coil (0.54 A) + Siemens 3RT2926-1BB00 varistor on K1/K2 | Vishay 1N5400 series datasheet 88516 + Siemens 3RT2926-1BB00 data sheet (../docs/fonti/Vishay_1N5408_1N5400-series_datasheet_88516.pdf, Siemens_3RT2926-1BB00_datasheet.pdf) | "IF(AV) 3.0 A", "IFSM 200 A", VRRM "1000 V"; "surge suppressor, varistor, 24-48 V AC, 50/60 Hz, 24-70 V DC, for contactors", "size of contactor S0" | **PRICE-ONLY** | - | rev B4 (G-23 closed): diode crimped on the coil spades (no diode terminal needed) | ESTIMATE → QUOTE needed | yes |
| 63 | `SCT_PNOZ_terminal_sets` | 1 | Y | 751008 (B0) + 3 x 751004 (SR1-SR3) | Pilz PNOZ m B0 manual 1002660-EN-13 p.8, p.29, p.44-48, p.52 (docs/fonti/Pilz_PNOZ_m_B0_OperManual_1002660-EN-13.pdf); EF manual p.30 | "PNOZ s Set1 spring- Set of plug-in replacement terminals 8-pin of spring-loaded type, 751008"; "… 4-pin of spring-loaded type, 751004" | **DOCUMENTED** | - | rev B4: eibabo net prices in the BOM (€115.23) | SECONDARY → public | yes |
| 64 | `E20_SC0_flexisoft_FX3-CPU1` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 65 | `E24_SC1_flexisoft_FX0-GENT` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 66 | `E21/E22/E28/E29/E2A_SX1-SX5_FX3-XTIO` | 5 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 67 | `E23_SM1_FX3-MOC1` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 68 | `H01..H10` | 1 | Y | harness: H07Z-K / Lapp OLFLEX cable by cross-section, SICK M12 cordsets, lugs | cable_schedule.csv + netlist ampacity table (IEC 60204-1 Table 6 'recalled', ASSUMED); Lapp T12 (docs/fonti/Lapp_T12_Strombelastbarkeit_technical_table.pdf, new) gives only derating factors | Lapp T12: "40 °C … 0,87" (70 °C conductor) | **GAP** | - | G-14 partly closed in rev B4: Lapp T12 base ampacities 0.5-4 mm² and HELUKABEL 6/10 mm² (+ NYY 16-35 mm²) saved; the netlist table (incl. 90 °C and 16-35 mm² flexible PVC) still needs EN 60204-1 Table 6 / DIN VDE 0298-4 (DOWNLOAD_LIST: purchase) | ESTIMATE → QUOTE needed | - |
| 69 | `E53_deck_grommet` | 1 | Y | cable entry frame IP54+, 60 x 110 opening | icotek KEL-DPZ series page icotek.com/en/products/cable-entry-plates/kel-dpz | "Certified protection up to IP66 (acc. to EN 60529)"; "UL94-V0"; "matches exactly the cut-out dimensions of 6-, 10-, 16- and 24-pin standard industrial connectors" | **PRICE-ONLY** | - | DOCUMENTED at series level: fix the size (KEL-DPZ 24 class for 60 x 110) in the BOM. Price: quote | ESTIMATE → QUOTE needed | - |
| 70 | `Z01_fasteners_consumables` | 1 | Y | ISO 4762/7380 screws, PEM, inserts, ties, Lapp Skintop glands, labels | ISO standard designations / catalogue items | standard designation | **DOCUMENTED** | - | standard parts; gland IP rating per Lapp catalogue at order (non-safety). Price ESTIMATE | ESTIMATE → QUOTE needed | - |
| 71 | `X02_robopad_base_RPBAS90` | 1 | Y | RPBAS90-100 charging base, 100 A, 60 V max, EN 61000-6-1/-6-3 tested | Roboteq RoboPad datasheet v1.3 p.2, p.12 (docs/fonti) | "RPBAS90-100 RoboPad Charging Base, 90mm wide, 100A"; "EN IEC 61000-6-3 E3:2021" | **PRICE-ONLY** | - | price ESTIMATE -> quote. BOM P/N 'RPBAS90' -> 'RPBAS90-100' | ESTIMATE → QUOTE needed | yes |
| 72 | `X04_charger_NPB750_48` | 1 | Y | NPB-750-48: CC 11.3 A, DIP 'flooded' 56.8/53.6 V, OVP 82-100 V, EMC Class B, IEC 60335-2-29, CANBus 2.0B, 230 x 158 x 67 mm | Mean Well NPB-750-SPEC p.1-5 (docs/fonti/MeanWell_NPB-750-SPEC.pdf) | "MAX. OUTPUT CURRENT(CC) … 11.3A"; "Pre-defined, flooded battery 56.8 … 53.6"; "Radiated BS EN/EN55032 (CISPR32),BS EN/EN55014-1 Class B"; "IEC60335-1/2-29"; "DIMENSION 230*158*67mm (L*W*H)" | **DOCUMENTED** | - | rev B4: M1 closed (CAD at 230 x 158 x 67, 1.84 kg); BOM price RS €171.72 | SECONDARY → public | yes |
| 73 | `X05_dock_controller_relay` | 1 | Y | Finder OPTA 8A.04.9.024.8320 (12-24 V DC, 4 NO 10 A, DC1 24 V 10 A, Wi-Fi + Ethernet) + Albright SW80B + 1N5408 in a DIN box | Finder S8A datasheet p.3/6/7/11 + EU DoC DOC8AW + instruction sheet (../docs/fonti/Finder_8A.04.9.024.8320_OPTA_datasheet_S8AEN_IX-2026_p3-6-7-11.pdf); Albright SW80 datasheet | "Nominal voltage (UN) V DC 12…24"; "Rated current/Maximum peak current A 10/15"; "Breaking capacity DC1: 24/110/220 V A 10/0.3/0.12"; DoC "EN IEC 61010-2-201:2018"; SW80B "600A at 96V" | **PRICE-ONLY** | - | rev B4 (G-24 closed): no IEC 61131-2 claim (EN 61010-2-201 instead); price Arduino Opta €206 (VAT unchecked) + SW80B quote | ESTIMATE → QUOTE needed | yes |
| 74 | `X06_apriltag_reflector_plate` | 1 | Y | AprilTag + retro-reflective plate at z 380-500 (above the scan plane) | custom print (no technical rating needed) | - | **DOCUMENTED** | - | design-defined part; the only technical rule (no reflector within the scan plane, SICK OI p.27 ZR) is a placement rule | ESTIMATE → QUOTE needed | - |
| 75 | `X08_dock_harness_ac` | 1 | Y | Lapp ÖLFLEX CLASSIC 110 3G1.5 (1119303) + Schurter DD11.0121.1110 inlet/switch/fuse module | Lapp DB1119752EN + Schurter DD11 datasheet (../docs/fonti/Lapp_1119303_OELFLEX-CLASSIC-110-3G1.5_datasheet_DB1119752EN.pdf, Schurter_DD11.0121.1110_datasheet.pdf) | Lapp "Nominal voltage U₀/U: 300/500V", "Class 5"; Schurter "IEC 10 A / 250 VAC", "Rocker switch 2-pole … acc. to IEC 61058-1" | **PRICE-ONLY** | - | rev B4 (G-01 closed for X08); cable €60.15/100 m (Lapp shop), switch quote | ESTIMATE → QUOTE needed | yes |
| 76 | `X09_dock_OV_relay_DUB01CD48500V` | 1 | Y | as K0V, 20-200 V range, bench-set 58.5 V | as E2K | as E2K | **DOCUMENTED** | - | price SECONDARY. ID clash: CAD calls it X08_dock_OV_relay_DUB01 (BOM X08 = dock harness) | SECONDARY → public | yes |
| 77 | `X04b_charger_NPB1700_48_option` | 1 | N | option, not in total | Mean Well NPB-1700-SPEC (docs/fonti) | "MAX. OUTPUT CURRENT(CC) … 25A"; "Radiated … Class A" | **EXCLUDED (in_total=N)** | - | in_total = N (option) | SECONDARY → public | - |
| 78 | `E50_dcdc_arm_*_DDR480C24` | 2 | Y | as E13 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 79 | `E52_arm_ORing_DRDN40-24_x2` | 1 | Y | 2x DRDN40-24 + 2x DSR 50/5 | DRDN40-SPEC + maxon 309687 | as E30 / E16 | **DOCUMENTED** | - | rev B4: CAD ids E52_L/R + E5B_L/R listed in the BOM row (M6); prices RS/maxon in the BOM | SECONDARY → public | - |
| 80 | `E57_FAL_FAR_fuses` | 1 | Y | FAL/FAR HP10M25 gPV on the 24 V arm buses (right MID rail) | Mersen HP10M datasheet (as E18) | "25 HP10M25* D1023825" | **DOCUMENTED** | - | rev B4 (G-13) | SECONDARY → public | - |
| 81 | `SP1_SP2_PSEN_cs3.1` | 2 | Y | PSEN cs3.1 541009 + actuator 541080: Cat 4, PL e, SIL CL 3, PFHd 2.62E-9, 2 OSSD, Sao 8 / Sar 20 mm, coding level Low | TÜV SÜD certificate M6A 020132 0191 (../docs/fonti/Pilz_PSENcode_PSEN-cs3.1_541009_TUV-Sued_EC-type-cert_M6A-020132-0191_1003929-BM-16.pdf, pilz.com/download/open) + Pilz product page (archived 2025-10-31, .txt) | "Tested according to ISO 13849-1:2023 (up to Cat. 4 PL e) … EN ISO 14119:2013, EN 60947-5-3:2013"; "PSEN cs3.1 M12/8-0.15m / PSEN cs3.1 (541009) … Category 4, PL e, SIL CL 3, PFHd 2,62·10-09"; page "Coding level to ISO 14119 Low" | **DOCUMENTED** | - | rev B4 (G-09 closed): actuator P/N is 541080 ("PSEN cs3.11" does not exist); ISO 14119 type 4 is inferred from "transponder"; the operating manual (series connection, type statement) is on DOWNLOAD_LIST as an evidence upgrade | SECONDARY → public | yes |
| 82 | `E54_U7_DDR480C24_coffee` | 1 | Y | as E13 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | - |
| 83 | `E55_K4_Finder22` | 1 | Y | DC1 25 A at 24 V per contact, coil 2.2 W (92 mA) | Finder 22 p.3 (docs/fonti) | "Breaking capacity DC1: 24/110/220 V A 25/5/1" | **PRICE-ONLY** | - | price ESTIMATE | ESTIMATE → QUOTE needed | - |
| 84 | `E56_FCF_fuse` | 1 | Y | FCF HP10M15 gPV on the 24 V coffee feed | Mersen HP10M datasheet (as E18) | "15 HP10M15* N1018590" | **DOCUMENTED** | - | rev B4 (G-13): 16 A gG → HP10M15 | SECONDARY → public | - |
| 85 | `E28_SX2_PNOZ_m_EF_8DI4DO_C48` | 1 | Y | 8 safe in, 4 SC out, PL e, CPU 2.84E-10, inputs 4.27E-11, SC out 2.12E-11, pulse suppression 0.5 ms | Pilz EF 8DI4DO manual 1002661-EN-08 p.24, 27 (docs/fonti) | "CPU 2-channel PL e Cat. 4 SIL 3 2,84E-10"; "Pulse suppression 0,5 ms" | **DOCUMENTED** | - | price SECONDARY (BOM URL = B0 page) | SECONDARY → public | yes |
| 86 | `K3_arm_precharge_C48` | 1 | Y | Finder 22.32 + Vishay RH-50 12R: 58.4 V / 12 Ω = 4.87 A ≤ 5 A DC1 @110 V | Finder S22EN p.7 + Vishay RH datasheet | "Breaking capacity DC1: 24/110/220 V A 25/5/1"; "Short time overload 5 x rated power for 5 s" | **PRICE-ONLY** | - | rev B4 (G-11, G-25 closed) | ESTIMATE → QUOTE needed | yes |
| 87 | `E51_jetson_orin_nx_carrier` | 1 | Y | Seeed reComputer J4012 (Orin NX 16 GB, J401 carrier): 9-19 V input, 10-25 W, -10..60 °C | Seeed datasheet + EU DoC 2023-03-27 + Morlab CE EMC VoC (../docs/fonti/Seeed_reComputer-J4012_110110145_datasheet_p1-2-3-4-5-23.pdf, ..._EU_DoC_2023-03-27.pdf) | "Power 9-19V"; "Power supply DC 12V/5A"; "Power … 10W - 25W"; DoC "Directive 2014/30/EU, ROHS directive 2011/65/EU" | **DOCUMENTED** | - | rev B4 (G-26 closed): no radio (no RED); FJ HP10M4 on the 12 V feed; superstructure | SECONDARY → public (USD 1,399 Seeed store) | yes |
| 88 | `E2M_SR3_PNOZ_m_EF_4DI4DOR` | 1 | Y | SR3 (rev B4): 4 safe in, 4 positive-guided relay outputs DC1 24 V 6 A / min 10 mA, PL e Cat 4 PFH 7.52E-12 → SWD INSafe_3/4 (SLS[2] 0.7 m/s) | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.207-221 (extract, docs/fonti) | as E2H | **DOCUMENTED** | - | new rev B4 row (G-04 bands) | SECONDARY → public (eibabo €379.72 net) | yes |
| 89 | `E44_tunnel_fan_*` | 2 | Y | San Ace 9WPA0624S4001 on the SWD tunnels (rev B4, F3) | San Ace catalogue C1152B001 (as E40) | as E40 | **PRICE-ONLY** | TP-11 | new rev B4 row | QUOTE → QUOTE needed | yes |

### 1.1 BOM ↔ `out/parts.json` mismatches (rev B3 list) - all closed in rev B4

| # | Mismatch (rev B3) | rev B4 |
|---|---|---|
| M1 | CAD modelled an NPB-1700-class charger box | **closed:** `X04_charger_NPB750_48` 230 × 158 × 67 mm, 1.84 kg |
| M2 | CAD `X08_dock_OV_relay_DUB01` vs BOM X08 = dock harness | **closed:** CAD renamed `X09_dock_OV_relay_DUB01` (netlist XD3 too) |
| M3 | centre rails: BOM 2 × 130 mm vs CAD 4 rails | **closed:** CAD now 2 centre rails (z 213) = BOM `E0C_centre_rails` 2 × 154 mm; side-bay rails 13 pieces in `E0x_din_rails` |
| M4 | `E18…x7` vs CAD x6 | **closed:** BOM `E18_branch_fuses_10x38_x6` (F1–F4, F5L, F5R) |
| M5 | FJ separate CAD part | **closed:** BOM E2F row names CAD `E2L` (FJ HP10M4) |
| M6 | E52/E5B split | **closed:** BOM E52 row lists `E52_L/R` + `E5B_L/R` |
| M7 | PCAN 45 × 90 × 100 | **closed:** 22.5 × 99 × 114.5 (PEAK manual p.65) on the right HIGH rail, 0 keep-out violations |
| M8 | SWD 6.0 kg, box envelope | **closed:** 7.0 kg, coaxial, L 196 mm (manual p.28); CALC mass +2 kg |
| M9 | K06 not in the BOM | **closed:** make row `K06_jetson_cover` |
| M10 | K05 classification | unchanged (purchased profile) |
| M11 | deck "10 mm" in BOM/CALC text | **closed:** 15 mm in BOM A02 and CALC |
| M12 | RPBAS90 order code | **closed:** RPBAS90-100 |
| M13 | NET1 P/N and size | **closed:** 1085256, 22.5 × 140.4 × 92.4 mm (own rail z 164) |

New purchased/made parts in rev B4: `E2M_SR3` (BOM row 88), `E44_tunnel_fan_*` (row 89), make rows `A09_deck_doubler`,
`A10_rail_bracket_FR`, `E43_swd_tunnel_*`, `D02_swd_cheek_*` (replaces the spacer), `K06_jetson_cover`.

## 2. CALC inputs matrix (`CALC.md` "Inputs and sources", 116 rows; rows 1–110 keep the rev B3 numbering, 111–116 are new)

| # | input | value | CALC tag | status | evidence / test |
|---|---|---|---|---|---|
| 1 | drive wheel contact /y/ | 232 mm | ESTIMATE | **DOCUMENTED (design value)** | design value amr_params.WHEEL_Y; tread width per SWD manual p.27 figure; verified in TP-23 (wheel scales) |
| 2 | drive wheel radius | 62.5 mm | SOURCED | **DOCUMENTED** | datasheet EW2A-125HN04x: "Diameter 125 mm" |
| 3 | castor swivel axis (x, y) | (±275, ±180) | ESTIMATE | **DOCUMENTED (design value)** | design value (CAD); tag should read CAD |
| 4 | castor trail (offset F) | 38 mm | SOURCED | **DOCUMENTED** | Blickle 754464: "Offset (F) 38 mm" |
| 5 | scan plane height | 184.5 mm | SOURCED | **DOCUMENTED** | roof 134 (CAD) + 50.5 (SICK data sheet p.5 dimensional drawing "50,5"); static check TP-05 |
| 6 | scanner origin /x/ | 290 mm | CAD | **DOCUMENTED (design value)** | design value |
| 7 | superstructure yaw | 0 deg | CAD | **DOCUMENTED (design value)** | design (no waist) |
| 8 | payload per hand (product rating) | 3 kg | SECONDARY | **DOCUMENTED (design value)** | own product rating, cad/params.py PRODUCT_PAYLOAD_ARM (software-limited) |
| 9 | tray payload (6 flasks) | 2.1 kg | SECONDARY | **DOCUMENTED (design value)** | own product rating, cad/params.py |
| 10 | tray payload CoG | (190, 0, 990) | SECONDARY | **DOCUMENTED (design value)** | superstructure CAD |
| 11 | shoulder /y/ | 162.5 mm | CAD | **DOCUMENTED (design value)** | integration.json |
| 12 | hand reach, worst pose | 550 mm | SECONDARY | **DOCUMENTED (design value)** | cad/validate.py worst pose (own kinematic model) |
| 13 | arm links shift, worst pose | 150 mm | SECONDARY | **DOCUMENTED (design value)** | cad/validate.py |
| 14 | hand payload, nominal work pose | (300, ±150, 1030) | SECONDARY | **DOCUMENTED (design value)** | cad/validate.py |
| 15 | hand payload, worst forward pose | (550, ±250, 1100) | SECONDARY | **DOCUMENTED (design value)** | cad/validate.py |
| 16 | hand payload, worst side pose | (0, ±712, 1100) / (250, ±300, 1100) | ESTIMATE | **TYPE-TEST TP-04** | conservative envelope; TP-04(a) static tilt in the worst configuration |
| 17 | hand payload, worst rear pose | (-550, ±250, 1100) | ESTIMATE | **TYPE-TEST TP-04** | mirror of the validated forward pose (conservative); TP-04 |
| 18 | gripper/fingers beyond the payload point | 50 mm | ESTIMATE | **GAP** | G-15 still open: the OpenArm 2.0 dimension drawing (saved, ../docs/fonti/OpenArm_2.0_dimensions_drawing_docs.openarm.dev_2026-10-05.jpg) gives "606mm Arm Reach" to the fingertip and ≈ 170 mm wrist → fingertip (derived), not the length beyond the payload point; take it from the gripper CAD or measure |
| 19 | harness + small parts, base | 3 kg @ z 200 | ASSUMED | **TYPE-TEST TP-04** | weigh the built base (mass/CoG check in TP-04); CAD harness parts are 0 kg |
| 20 | harness on the superstructure | 0.5 kg @ z 450 | ASSUMED | **TYPE-TEST TP-04** | as above |
| 21 | SWD nominal torque (wheel) | 7.9 Nm | SOURCED | **DOCUMENTED** | SWD manual v2.0.2 p.13: "Nominal performance 7.9 Nm at 380 rpm" (the CALC URL is the web page; the manual is the saved evidence; the datasheet's "7,9 daN" is a typo) |
| 22 | SWD peak torque (wheel) | 13 Nm | SOURCED | **DOCUMENTED** | manual p.13 / datasheet: "Peak torque 13 Nm" |
| 23 | SWD nominal speed | 380 rpm | SOURCED | **DOCUMENTED** | datasheet "Nominal speed 380 rpm" (exact ratio 62/17, manual p.13) |
| 24 | SWD static load per wheel | 250 kg | SOURCED | **DOCUMENTED** | datasheet "250 kg (static)" |
| 25 | SWD S1 power | 200 W | SOURCED | **DOCUMENTED** | datasheet "Nominal power 200 W (S1)" |
| 26 | tyre/floor friction PU on concrete | 0.5 | ASSUMED | **TYPE-TEST TP-01** | TP-01 stopping distance + threshold climbing; TP-03b slope |
| 27 | rolling resistance drive wheels | 0.015 | ASSUMED | **TYPE-TEST TP-22** | energy only; measured in TP-22 |
| 28 | rolling resistance castors | 0.025 | ASSUMED | **TYPE-TEST TP-22** | Blickle publishes words only ("Rolling resistance very good") |
| 29 | traction efficiency | 0.75 | ASSUMED | **TYPE-TEST TP-22** | energy/runtime only |
| 30 | DC-DC efficiency DDR-480C-24 | 0.92 | SOURCED | **DOCUMENTED** | DDR-480-SPEC p.2 "EFFICIENCY (Typ.) … 92%" |
| 31 | SS1-t stop ramp (quick-stop 604Ah) | 1.5 m/s² | ASSUMED | **DOCUMENTED (design value)** | design parameter written into the drive (non-safe ramp per VERIFICATION E4); achieved decel verified in TP-01/TP-01b |
| 32 | SS1-t PNOZ STO delay | 1.2 s | ESTIMATE | **DOCUMENTED (design value)** | design parameter (PNOZ configuration); timer element P15 in the free Configurator |
| 33 | SWD t_SLS (6691h) | 1 s | ESTIMATE | **DOCUMENTED (design value)** | configurable parameter, SWD manual p.109-110; value = design choice |
| 34 | commanded accel/decel limit | 1.5 m/s² | ASSUMED | **DOCUMENTED (design value)** | design limit (further reduced per band, CALC §7b) |
| 35 | ramps | 6 % / 8 % | ASSUMED | **DOCUMENTED (design value)** | site specification (manual); TP-03b at 6 % |
| 36 | castor carriage travel | -2.5 / +17 mm | CAD | **DOCUMENTED (design value)** | CAD; TP-23 |
| 37 | castor spring rate per corner | 28.34 N/mm | SOURCED | **DOCUMENTED** | Gutekunst "R 14,172" x 2 |
| 38 | castor installed spring force | 76 N | CAD | **TYPE-TEST TP-23** | set on a scale per corner (TP-23); L0 tolerance ±1.44 mm documented |
| 39 | D-313J-02 Fn / Fndyn | 327.711 / 300.878 N | SOURCED | **DOCUMENTED** | Gutekunst "Fn 327,71" "Fndyn 300,88" |
| 40 | castor load capacity 4 km/h / static | 200 / 500 kg | SOURCED | **DOCUMENTED** | Blickle 754464: "Load capacity at 4 km/h 200 kg" - rev B4: top speed 1.1 m/s = 3.96 km/h, so the published value applies (G-04 closed) |
| 41 | MGN15H C0 / C / MR | 9.11 / 6.37 kN / 73.5 N·m | SOURCED | **DOCUMENTED** | HIWIN G99TE24-2410 p.91 |
| 42 | floor unevenness under one castor | 5 mm | ASSUMED | **TYPE-TEST TP-23** | site requirement (manual) + TP-23 drive share with a 5 mm shim |
| 43 | scan plane height limit | 200 mm | SOURCED | **DOCUMENTED** | SICK OI p.40 "maximum height of 200 mm everywhere" |
| 44 | scan-plane mounting tolerance | 5 mm | ASSUMED | **TYPE-TEST TP-05** | acceptance 184.5 ± 5 mm at every field edge |
| 45 | pitch dynamic amplification | 1.2 | ASSUMED | **TYPE-TEST TP-05b** | measured while accelerating per band |
| 46 | battery energy (2 packs) | 3.08 kWh | SOURCED | **DOCUMENTED** | 805-0027 Table 3-1 "Energy … 1536 Wh" x 2 = 3.07 kWh |
| 47 | usable fraction above 48 V | 0.88 | ESTIMATE | **TYPE-TEST TP-22** | runtime/energy only, measured in TP-22 |
| 48 | bus nominal | 51.2 V | SOURCED | **DOCUMENTED** | Table 3-1 "Nominal Voltage … 51.2 V" |
| 49 | bus minimum under peak load | 40 V | SOURCED | **DOCUMENTED** | rev B4 (G-16 closed): 805-0027 Table 3-1 "Low Voltage Disconnect … 40.0 V" (CALC V_MIN) |
| 50 | application LVCO K0V | 48 V | SOURCED | **DOCUMENTED** | Table 3-1 "Low Voltage Disconnect Recommended … 48.0 V" |
| 51 | pack continuous discharge | 15 A | SOURCED | **DOCUMENTED** | Table 3-1 |
| 52 | pack 1 h discharge | 58 A | SOURCED | **DOCUMENTED** | Table 3-1 |
| 53 | pack peak discharge | 90 A RMS (10 s) | SOURCED | **DOCUMENTED** | Table 3-1 10 s; product page says 3 s: use 3 s where duration matters |
| 54 | BMS over-discharge trip | > 58 A for 10 s | SOURCED | **DOCUMENTED** | Table 3-4 |
| 55 | pair ratings | 30 / 116 / 180 A | SOURCED | **DOCUMENTED** | Table 3-9 |
| 56 | DDR-480C-24 rated current | 20 A | SOURCED | **DOCUMENTED** | DDR-480-SPEC p.2 |
| 57 | DDR-480C-24 peak (5 s) | 30 A | SOURCED | **DOCUMENTED** | DDR-480-SPEC p.2 "CURRENT 5sec. … 30A" |
| 58 | OpenArm per arm typ | 70 W | SECONDARY | **TYPE-TEST TP-22** | rev B4 (G-17): Damiao spec pages + manuals saved (DM-J8009P "Rated current 20A Peak current 50A", DM-J4340(P) "2.5A / 8A", DM-J4310 "2.5A / 7.5A" at 24 V): nameplate sum ≈ 1.32 kW rated / 3.5 kW peak per arm = upper bound only; the duty value is measured (arm power log in TP-22, arm-bus current in TP-14) |
| 59 | OpenArm per arm cont | 360 W | SECONDARY | **TYPE-TEST TP-22** | as row 58 |
| 60 | OpenArm per arm peak (5 s) | 720 W | SECONDARY | **TYPE-TEST TP-14** | as row 58; the DDR-480 current limit (30 A 5 s) caps the bus peak |
| 61 | Kassow Edge per arm typ | 350 W | ASSUMED | **DOCUMENTED** | CLOSED by Kassow Edge brochure p.4 (docs/fonti/Kassow_EdgeEdition_brochure_p1_p4_power.pdf): "Typical … avg. power consumption 200/300" W -> replace 350 by 300 |
| 62 | Kassow Edge per arm idle | 40 W | ASSUMED | **DOCUMENTED** | brochure: "Standstill power consumption, brakes applied (W) 65" / released 75 -> replace 40 by 75 (CALC value was optimistic) |
| 63 | Kassow Edge per arm peak | 1000 W | ASSUMED | **DOCUMENTED** | brochure: "Power consumption (with max. load; W) 400–600 / 400–1200" -> use 1200 (KR1018/1410/1805) or 600 (KR810/1205); recheck C48 feed vs "Max external fuse (A) 25" |
| 64 | Jetson Orin NX average | 25 W | SECONDARY | **DOCUMENTED** | nvidia.com Jetson Orin: "Power 10W - 15W - 25W - 40W" (module; carrier extra) |
| 65 | Jetson Orin NX max | 40 W | SECONDARY | **DOCUMENTED** | as above (40 W = MAXN Super) |
| 66 | 2 x nanoScan3 at max output load | 31.8 W | SOURCED | **DOCUMENTED** | OI p.130 "Typ. 15.9 W" |
| 67 | Pilz station + bleed + relays | 16 W | ESTIMATE | **TYPE-TEST TP-22** | energy only; sizing uses the documented B0 1.6 A max supply |
| 68 | Ethernet switch + cameras | 12 W | ASSUMED | **TYPE-TEST TP-22** | energy only |
| 69 | 2 x SWD standby electronics | 10 W | ASSUMED | **TYPE-TEST TP-22** | energy only |
| 70 | DC-DC no-load losses | 10 W | ASSUMED | **TYPE-TEST TP-22** | energy only |
| 71 | coffee module brewing | 300 W | SECONDARY | **GAP** | G-18: coffee machine not chosen (CE gap G5); use its datasheet when chosen |
| 72 | coffee module peak | 720 W | SOURCED | **DOCUMENTED** | converter limit DDR-480 "24Vo / 48Vo : 720W" (5 s) |
| 73 | arm 24 V feed length | 1.5 m | ESTIMATE | **DOCUMENTED (design value)** | cable_schedule WW3L/R (design) |
| 74 | arm 24 V feed cross-section | 4 mm² | ASSUMED | **DOCUMENTED (design value)** | rev B4: design value; ampacity documented by Lapp T12 Table 12-1 (../docs/fonti/Lapp_T12_current-ratings_technical_table_EN.pdf): 4 mm² multi-core "34" A at 30 °C × 0.87 (40 °C) = 29.6 A ≥ 15 A; the netlist uses 6 mm² (WW3) |
| 75 | NPB-750-48 CC current | 11.3 A | SOURCED | **DOCUMENTED** | NPB-750-SPEC p.2 |
| 76 | NPB-1700-48 CC current | 25 A | SOURCED | **DOCUMENTED** | NPB-1700-SPEC p.2 |
| 77 | charging voltage mid CC | 54 V | ASSUMED | **TYPE-TEST TP-13** | charge-time only; measured in TP-13 |
| 78 | robot consumption docked | 150 W | ASSUMED | **TYPE-TEST TP-13** | charge-time only |
| 79 | RoboPad continuous rating | 60 A | SOURCED | **DOCUMENTED** | RoboPad v1.3 p.15 |
| 80 | pack max continuous charge | 15 A | SOURCED | **DOCUMENTED** | Table 3-1 |
| 81 | acceptable 20->90 % charge time | 8 h | ASSUMED | **DOCUMENTED (design value)** | product requirement (single shift) |
| 82 | nanoScan3 response time | 70 ms | SOURCED | **DOCUMENTED** | data sheet p.2 "Response time 70 ms" |
| 83 | nanoScan3 field supplement TZ | 65 mm | SOURCED | **DOCUMENTED** | data sheet p.2 "Protective field supplement 65 mm" |
| 84 | nanoScan3 field range | 3000 mm | SOURCED | **DOCUMENTED** | data sheet p.2 "Protective field range 3m" |
| 85 | reflector supplement ZR | 0 mm | ASSUMED | **DOCUMENTED (design value)** | valid under the documented condition (OI p.27): no retroreflector within 6 m of the plane -> placement rule in the manual; TP-05 |
| 86 | PNOZ logic, relay path | 54 ms | SOURCED | **DOCUMENTED** | Pilz catalogue "tReactionMax = 54 ms" |
| 87 | SWD reaction to ramp/STO | 40 ms | ASSUMED | **TYPE-TEST TP-01** | SFRT measured, keep >= 2x margin |
| 88 | braking-distance factor | 1.1 | ASSUMED | **TYPE-TEST TP-01** | replaced by measured stopping distances (TP-01/TP-03a) |
| 89 | approach speed K (ISO 13855) | 1600 mm/s | SOURCED | **DOCUMENTED** | SICK OI p.30 "S = 1,600 mm/s × T + TZ + ZR + CRO" (saved extract, new) |
| 90 | arm stopping time | 0.2 s | ASSUMED | **TYPE-TEST TP-07** | EN ISO 13855 stopping-time measurement |
| 91 | OpenArm gripper grip force | 50 N | ASSUMED | **TYPE-TEST TP-10** | measure (carry rule: tray) |
| 92 | grip pad friction on cup | 0.4 | ASSUMED | **TYPE-TEST TP-10** |  |
| 93 | cup/flask on tray friction | 0.3 | ASSUMED | **TYPE-TEST TP-10** | TP-10 E-stop with full cups |
| 94 | E 6082-T6 | 70 GPa | SOURCED | **DOCUMENTED** | Aalco 6082-T6/T651 plate data (EN 485-2): "Modulus of Elasticity: 70 GPa" (web page; not saveable as PDF) |
| 95 | Rp0.2 6082-T6 plate | 240 MPa | SOURCED | **DOCUMENTED** | Aalco: 255 MPa min for 6-12.5 mm, 240 MPa above 12.5 mm (deck is 15 mm -> 240 is the right value; CALC label '10 mm' is stale) |
| 96 | ReH S355MC | 355 MPa | SOURCED | **DOCUMENTED** | SSAB Domex 355MC data sheet 2276: "meets or exceeds the requirements of S355MC in EN 10149-2", ReH 355 (docs/fonti, new) |
| 97 | deck span between spines | 274 mm | CAD | **DOCUMENTED (design value)** | CAD |
| 98 | column foot centre x | -60 mm | SECONDARY | **DOCUMENTED (design value)** | superstructure CAD |
| 99 | deck effective strip width | 62 mm + 15 mm doubler | CAD | **DOCUMENTED (design value)** | rev B4 (G-19 closed): lower bound = bolt pitch (no spread credited) + A09 doubler in CAD; δ 0.36 mm ≤ 0.55 mm (CALC §9) |
| 100 | M6 8.8 preload in tapped 6082 | 7000 N | ASSUMED | **DOCUMENTED** | rev B4 (G-20 closed): Bossard VDI 2230 table (../docs/fonti/Bossard_060_074_Preload_tightening_torques_VDI2230_EN_01-2025_p1-3.pdf): M6 8.8 μ 0.14 "FM … 9.9 kN", "MA 11.3 Nm"; 7000 N = 71 % of FM max (through bolts into nuts / the doubler) |
| 101 | coffee uprights on the deck | (-228,-118),(-228,175) | CAD | **DOCUMENTED (design value)** | integration.json |
| 102 | arm hazard radius | 762.5 mm | ESTIMATE | **DOCUMENTED (design value)** | computed from the poses above (depends on G-15) |
| 103 | base swept radius | 436.3 mm | CAD | **DOCUMENTED (design value)** | out/stl |
| 104 | superstructure swept radius | 440 mm | CAD | **DOCUMENTED (design value)** | integration.json |
| 105 | logistics drive cycle | 1.0 m/s, stop every 10 m | ASSUMED | **DOCUMENTED (design value)** | use-case definition (runtime claim conditions) |
| 106 | duty profiles | logistics / barista / idle-heavy | ASSUMED | **DOCUMENTED (design value)** | use-case definition |
| 107 | main fuse F0 | 100 A | SOURCED | **DOCUMENTED** | Siemens 3NA3830 data sheet |
| 108 | SW80B Ith | 100 A | SOURCED | **DOCUMENTED** | Albright SW80 "Thermal Current Rating (Ith) 100A 125A" |
| 109 | tower roof effective width | 2 x 43 + 30 mm | ESTIMATE | **DOCUMENTED (design value)** | bounded: with the 30 mm pad width alone the roof stress is 51 x 116/30 = 197 MPa <= 237 MPa, so the PASS does not depend on the estimate |
| 110 | roof flange bolts M6 8.8 As / Rp0.2 | 20.1 mm², 640 MPa | SOURCED | **DOCUMENTED** | rev B4 (G-20 closed): Bossard ISO 898-1 sheet (../docs/fonti/Bossard_012_016_Screws_property_class_ISO898-1_EN_01-2025_p1-2.pdf): "M6 20,1" mm², "Rp0,2 … 640" |
| 111 | top speed (SMS) = castor rating speed | 1.1 m/s | SOURCED | **DOCUMENTED** | rev B4 (G-04): Blickle 754464 "Load capacity at 4 km/h 200 kg"; 1.1 m/s = 3.96 km/h |
| 112 | SLS speed bands SLS[1] / SLS[2] / SMS | 0.3 / 0.7 / 1.1 m/s | CAD | **DOCUMENTED (design value)** | design; SWD manual: INSafe pairs 1-2 / 3-4, SLS[1..8], permanent SMS (netlist swd_permanent) |
| 113 | supplement Z_F for lack of ground clearance | 150 mm | SOURCED | **DOCUMENTED** | rev B4 (F1): SICK OI 8024596 p.37-38 "The lump supplement for ground clearance under 120 mm is 150 mm"; fig. 24 B_F ≤ 50 mm → 150 mm |
| 114 | lateral turning allowance per side | 100 / 150 / 200 mm | CAD | **DOCUMENTED (design value)** | design allowance (SICK OI p.37: "the impact of turning must be considered separately") |
| 115 | arm-work field resolution | 50 mm | SOURCED | **DOCUMENTED** | rev B4 (F2): SICK OI p.31 "If the scan plane is lower than 300 mm, you must use a resolution finer than 70 mm", "dr = HD / 15 +50 mm" = 62 mm |
| 116 | deck doubler A09 thickness | 15 mm | CAD | **DOCUMENTED (design value)** | rev B4 (G-19): CAD part A09, no composite action credited |

Kassow rows 61–63 (closed in the rev B3 audit) are now used by `amr_calc.py`: typ 300 W, standstill 75 W, peak 1200 W per arm →
C48 runtimes 6.4 h (logistics) / 3.3 h (barista) (rev B3 text: 6.7 / 3.0 h).

## 3. GAP list after rev B4

| GAP | Rows | Sev. | rev B4 status / remaining action |
|---|---|---|---|
| G-01 | K05, C03, C06, X08 | C/C/C/S | **closed:** APSOseal 1025058803 (product page), APSOplast PUR D15 90A (datasheet), Ganter GN 351-20-15-M6 (480 N), Lapp ÖLFLEX CLASSIC 110 3G1.5 + Schurter DD11 (IEC 61058-1) |
| G-04 | C01 castor rating above 4 km/h | S | **closed by design:** top speed 1.1 m/s = 3.96 km/h; bands 0.3 / 0.7 / 1.1 m/s (SLS[2] on SR3); fields, limits, runtimes re-run |
| G-06 | E02 E-stop actuator | S | **closed:** Siemens 3SU1050-1HB20-0AA0 / 3SU1500-0AA10-0AA0 data sheets (EN ISO 13850, B10 100 000) |
| G-07 | SB1, SK1 | S | **closed:** Eaton 216931 / 216376 / 216900 specification sheets |
| G-08 | SE1 pendant + socket | S | **closed:** Euchner ZSA2B4G02CC2322 (EN 60947-5-8, B10D 3.9E5) + binder M12 5-pole socket; price quote |
| G-09 | SP1/SP2 PSEN cs3.1 | S | **closed:** TÜV SÜD certificate (Cat 4 PL e, PFHd 2.62E-9) + Pilz page (coding Low). Manual = evidence upgrade (DOWNLOAD_LIST) |
| G-10 | fans | S | **closed:** San Ace 9WPA0624S4001 / 9WPA0424H6001 (IP68, airflow, pressure); 50 % effective flow ASSUMED → TP-11 |
| G-11 | K3 | S | **closed:** 12 Ω, 4.87 A ≤ 5 A DC1 |
| G-13 | 10 × 38 fuses | S | **closed:** Mersen HP10M + CUS101HEL official datasheets, every position has a P/N. Breaking-capacity question moved to G-29 |
| G-14 | H01..H10 ampacity, arm-feed cross-section | S | **partly closed:** Lapp T12 base table (0.5–4 mm²) and HELUKABEL (6/10 mm², NYY 16–35) saved; the netlist's 90 °C and 16–35 mm² flexible values still need EN 60204-1 Table 6 or DIN VDE 0298-4 (purchase). CALC row 74 closed |
| G-15 | gripper length beyond the payload point | S | **open:** OpenArm drawing saved (606 mm reach, ≈ 170 mm wrist → fingertip); measure or take the gripper CAD |
| G-16 | bus minimum 44 V | F | **closed:** 40 V BMS LVD (Table 3-1) in CALC |
| G-17 | OpenArm 70/360/720 W | F | **reclassified TYPE-TEST:** Damiao motor data saved (upper bound ≈ 1.32 kW rated per arm); duty power measured in TP-22 / TP-14 |
| G-18 | coffee module 300 W | F | **open:** machine not chosen (CE gap G5) |
| G-19 | deck strip width | S | **closed:** lower bound 62 mm + 15 mm doubler A09 in CAD: 0.36 mm ≤ 0.55 mm |
| G-20 | M6 preload, As, Rp0.2 | F | **closed:** Bossard VDI 2230 table and ISO 898-1 sheet |
| G-21 | T24 terminals, resistors, NET1 | F | **closed:** Phoenix PT 16 N (76 A), Vishay PR01/PR02, FL SWITCH 1008N datasheet |
| G-22 | JR1 | F | **closed:** 2 × Phoenix EMG 17-OV-TTL/24DC/2 ("1" ≥ 2 V, 2.6 mA) |
| G-23 | D0 coil suppression | S | **closed:** Vishay 1N5408 (3 A) on the SW80 coil + Siemens 3RT2926-1BB00 on K1/K2 |
| G-24 | X05 dock controller + contactor | S | **closed:** Finder OPTA 8A.04.9.024.8320 (datasheet + EU DoC) + Albright SW80B |
| G-25 | precharge resistor pulse rating | F | **closed by replacement:** Vishay Dale RH-50 ("5 x rated power for 5 s"); the Arcol/Ohmite HS datasheet (saved) has no overload rating |
| G-26 | Jetson carrier | F | **closed:** Seeed reComputer J4012 datasheet + EU DoC (EMC/RoHS, no radio) |
| G-27 | ISO 3691-4 test pieces | S | **open:** buy EN ISO 3691-4:2023 (DOWNLOAD_LIST) |
| G-28 | certificates for the technical file | evidence | **mostly closed:** SICK DoC + 2 TÜV certificates, ez-Wheel DoC/DoI + INERIS certificate, Pilz PSEN TÜV, Finder/Seeed DoCs saved. Open: Pilz PNOZ m B0 certificate/DoC, Discover UN 38.3 test summary (DOWNLOAD_LIST) |
| G-29 (new) | B48 prospective Isc vs HP10M 10 kA (IEC) | S | **open:** measure the pack-pair Isc in TP-14 (acceptance ≤ 10 kA); if higher, add a current-limiting upstream device documented for cascading, or a fuse with a higher IEC DC breaking capacity |

## 4. Price status (rev B4)

Basis: `bom_amr.csv` @1, rows with in_total = Y, scope AMR incl. dock (SUBTOTAL_base €22,583 + SUBTOTAL_dock €1,748 = **€24,331**).

| Scope (@1) | Value | Public price (SOURCED/SECONDARY in the BOM) | Quote needed |
|---|---|---|---|
| Purchased parts (buy rows) | €20,359 | €15,118 (**74.3 %**; rev B3 65.4 %) | €5,241 |
| Make parts | €3,971 | €0 | €3,971 (ESTIMATE by nature) |
| **AMR incl. dock** | **€24,331** | €15,118 (**62.1 %**) | €9,213 |

The rev B3 price corrections are applied: 3RT2026-1BB40 €202.10 × 2 (was €90), PEAK IPEH-004010 €294 (was €520), DDR-240C-24 €134.08
(was €79), DUB01CD48500V €144.90 × 2 (was €163), terminal sets €115.23 (3 EF modules), pendant €500 (was €250, quote), plus RS/TME/eibabo
prices for DDR-120/60, DRDN40, NPB-750, FL SWITCH, KI4, WPD 100, E-stop, Eaton M22, Mersen HP10M/CUS101HEL, PNOZ prices with corrected
URLs. Net effect with the rev B4 additions (SR3, tunnels, tunnel fans, doubler, A10, cheeks, K06): **+€1,056 @1** vs rev B3 (€23,275).
Largest quote items: Discover packs (€1,860), LYNK II (€350), RoboPad collector + base (€700), Albright SW80B/ED250B, Blickle/HIWIN,
enabling switch (€500), Patlite tower, fans. Variants (@1): arm_OA €1,009 (all public), barista €225 (€185 public), arm_C48 €367
(€322 public), superstructure Jetson J4012 €1,287 (public, Seeed store).

## 5. Design findings from the rev B3 audit - status after rev B4

| # | Finding | rev B4 implementation |
|---|---|---|
| F1 | fields without Z_F | **done:** Z_F 150 mm in length and width (SL = SA + TZ + ZR + ZF + ZB, SB = FB + 2 (TZ + ZR + ZF)); fields 401 / 613 / 943 mm, sides 357 / 407 / 457 mm, rotation circle R 912 mm; §7b limits 1.36/0.79, 1.15/0.69, 0.97/0.61 m/s²; field table, manual, TP-05/05b updated |
| F2 | arm field without T_Z, resolution | **done:** S = K·T + T_Z + C_RO → R 2472 mm (2498 mm from the scanner ≤ 3000); resolution 50 mm ≤ d_r 62 mm in config (netlist FS2), CALC row, TP-05 |
| F3 | SWD 0…+40 °C vs bays 44–46 °C | **done (both measures):** SWD tunnels E43 on room air + E44 fans; rated room 0…+35 °C; tunnel outlet 35.9 / 37.9 °C; TP-11 heat-run criteria; RISK H45 |
| F4 | SWD mass / length | **done:** 7.0 kg, L 196 coaxial in CAD; interference re-checked (0); centre bay rearranged |
| F5 | DSR 50/5 5 A at 27 V | **done:** 2 × 135 W = 270 W ≥ 200 W peak; continuous derated at 43 °C; over-temperature cut-out = INFO row + RISK H20 + TP-14; "CE [ASSUMED]" removed; VERIFICATION MX1-B4 row |
| F6 | Kassow power | **done:** brochure values in CALC (C48 6.4 / 3.3 h), netlist c48 feed 1200 W, F5L/R HP10M25 (= "Max external fuse 25 A") |
| F7 | netlist value corrections | **done:** KS 10.4 mA, K0V/K4 coil, 0 V block 101 A, K1/K2 B10D 1.37E6, NET1 P/N, KI4 9 mA (official) |
| F8 | PSEN coding level Low | **recorded** in the netlist/BOM; defeat assessment item stays in `ce/RISK_ASSESSMENT.md` (OA variant) |
| F9 | stale text | **done:** README status sentence replaced; CALC 15 mm deck and Rp0.2 label; BOM PNOZ URLs; ELECTRICAL/SAFETY_FUNCTIONS speed and field values |
| F10 | datasheet inconsistencies | unchanged (conservative readings kept) |

## 6. Evidence added to `../docs/fonti/` in rev B4 (61 files, 19.4 MB; each PDF checked with pdftotext)

| Group | Files |
|---|---|
| Fuses | `Mersen_HP10M_gPV-10x38-1000VDC_datasheet.pdf`, `Mersen_HelioProtection_brochure_EN_p1_p8-9_HP10M_CUS101HEL.pdf`, `Mersen_HP10M8-32_time-current-curve_720877.pdf`, `Mersen_CUS101HEL_K1062724_PV-fuse-holder_datasheet.pdf` |
| Siemens | `Siemens_3SU1050-1HB20-0AA0_datasheet.pdf`, `Siemens_3SU1500-0AA10-0AA0_datasheet.pdf`, `Siemens_3RT2926-1BB00_datasheet.pdf`, `Siemens_3NH3030_datasheet.pdf`, `Siemens_5TL1240-0_datasheet_p1-2.pdf` |
| Eaton | `Eaton_M22-DL-B_216931_specifications.pdf`, `Eaton_M22-K10_216376_specifications.pdf`, `Eaton_M22-WRS3_216900_specifications.pdf` |
| Phoenix / Weidmüller / binder | `PhoenixContact_1085256_FL-SWITCH-1008N_datasheet.pdf`, `PhoenixContact_2966171_PLC-RSC-24DC-21_datasheet.pdf`, `PhoenixContact_2943259_EMG-17-OV-TTL-24DC-2_datasheet.pdf`, `PhoenixContact_3211861_PT-4-HESI_datasheet.pdf`, `PhoenixContact_3212138_PT-16-N_datasheet.pdf`, `Weidmueller_1561910000_WPD-100-2X25-6X10-GY_datasheet.pdf`, `Binder_76-0632-1011-00005-0200_M12-A_female_panel_5pin_datasheet.pdf` |
| Passive parts | `Vishay_1N5408_1N5400-series_datasheet_88516.pdf`, `Vishay_PR01-PR02-PR03_datasheet_28729.pdf`, `Vishay-Dale_RH-NH_RH-50_aluminum-housed_datasheet_30201.pdf`, `Ohmite-Arcol_HS-series_HS50_aluminium-housed_datasheet.pdf` |
| Fans | `SanyoDenki_9WPA0624S4001_9WPA0424H6001_9WPA0824H4001_catalog_C1152B001_p1-362-364-371-373-377-379-625.pdf` |
| Safety devices | `Euchner_ZSA-ZSR_operating-instructions_EN_2092781.pdf`, `Euchner_ZSA2B4G10CC2322_110560_datasheet_2127401.pdf`, `Pilz_PSENcode_PSEN-cs3.1_541009_TUV-Sued_EC-type-cert_M6A-020132-0191_1003929-BM-16.pdf`, `Pilz_PSEN-cs3.1_541009_eshop_technical_data_wayback_2025-10-31.txt` |
| Certificates (G-28) | `SICK_nanoScan3_EU_DoC_9433543_00_2026-03-31.pdf`, `SICK_nanoScan3_EC_type-examination_TUV_01-205-5757.02-24_E263205_02.pdf`, `SICK_nanoScan3_EU-2023-1230_type-examination_TUV_01-205-5757.03-26_E456701_00.pdf`, `ezwheel_SWD_EC_DoC-DoI_2024-04-01_EN.pdf`, `ezwheel_SWD_EC_type-examination_INERIS_0080.5493.520.03.22.0075_Ext001.09.23.pdf`, `Discover_Lithium_SDS_rev2025-07-10_p1-13-17_UN38.3_statement.pdf` |
| Dock / compute | `Finder_8A.04.9.024.8320_OPTA_datasheet_S8AEN_IX-2026_p3-6-7-11.pdf`, `Finder_8A.04.9.024.8320_EU_DoC_DOC8AW_rev3_2026-01-19.pdf`, `Finder_8A.04.9.024.83xx_instruction_sheet_IB8A04EN.pdf`, `Seeed_reComputer-J4012_110110145_datasheet_p1-2-3-4-5-23.pdf`, `Seeed_reComputer-J4012_110110145_EU_DoC_2023-03-27.pdf`, `Seeed_reComputer-J4012_110110145_CE_EMC_VoC_Morlab_SZ23020261C01.pdf`, `Lapp_1119303_OELFLEX-CLASSIC-110-3G1.5_datasheet_DB1119752EN.pdf` (+ API .txt), `Schurter_DD11.0121.1110_datasheet.pdf` |
| Mechanical / tables | `AngstPfister_APSOplast_PUR-D15-90_0125103030_technical_data_sheet.pdf`, `AngstPfister_APSOseal_1025058803_EPDM_finger-protection-profile_product_page_2026-10-05.txt`, `Ganter_GN351-20-15-M6-SS-55_datasheet_and_load_ratings.pdf`, `Bossard_060_074_Preload_tightening_torques_VDI2230_EN_01-2025_p1-3.pdf`, `Bossard_012_016_Screws_property_class_ISO898-1_EN_01-2025_p1-2.pdf`, `Lapp_T12_current-ratings_technical_table_EN.pdf`, `HELUKABEL_Technical-Reference-Guide_current-carrying-capacity_Ed1_EN_p1-6-12-15-17.pdf` |
| OpenArm / Damiao (G-15, G-17) | `Damiao_DM-J8009P-2EC_V1.0_*`, `Damiao_DM-J4340P-2EC_V1.0_*`, `Damiao_DM-J4340-2EC_V1.0_*`, `Damiao_DM-J4310-2EC_V1.1_*` (user manual PDF + spec page .txt each), `OpenArm_2.0_docs_motor_gripper_general_2026-10-05.txt`, `OpenArm_2.0_motor_location_*.jpg`, `OpenArm_2.0_dimensions_drawing_*.jpg` |

The rev B3 evidence list (SICK OI extracts, HIWIN p.87, Blickle 3D model, Finder 22/38/80, PEAK manual + price list, maxon DSR,
Lapp T12 German, SSAB, Patlite, Kassow) is unchanged: `archive/rev_B3/CERTAINTY.md` §6.
