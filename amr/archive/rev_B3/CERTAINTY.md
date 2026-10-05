# AMR rev B3: certainty audit of purchased parts and calculation inputs (2026-10-05)

Owner rule: every value the design uses must come from an official manual or datasheet, with no open questions. This file checks
that rule against `bom_amr.csv`, `out/parts.json`, `CALC.md` (inputs table), `electrical/netlist_amr.yaml`, `VERIFICATION.md`,
`CASTOR_SUSPENSION.md`, `CAD_REV_B3.md` and `ce/GAPS.md`. Sources were reopened in this audit: local PDFs were read with pdftotext
(page numbers are PDF pages unless the document prints its own), and web pages and PDFs were fetched with curl or WebFetch.
Earlier SOURCED tags were not taken on trust. **41 BOM rows were fully spot-checked against the source text**, covering every
safety-rated and every expensive item (column "spot-checked").

This file only reports. No design file was changed (`amr_cad.py`, `amr_params.py`, `electrical/*`, `bom_amr.csv`). New evidence
files were added to `../docs/fonti/` (list at the end, about 6.6 MB).

## Status rules
- **DOCUMENTED:** the technical values the design uses are in an official manufacturer document (or a standard designation for
  standard parts), quoted below. Rows marked "(design value)" in §2 are values that our own CAD or specification defines.
- **TYPE-TEST:** the value cannot be taken from a document. The machine builder measures it on the prototype in the `ce/TEST_PLAN.md`
  test named in the row.
- **PRICE-ONLY:** the technical data are documented, but there is no public price, so a quote is needed.
- **GAP:** a technical value the design relies on has no official document behind it. It must be fixed (fix given in §3).

**Evidence grade.** Some values could only be read on distributor pages (eibabo.de, RS, TME), which reproduce the manufacturer's data,
because the manufacturer site blocks scripted access (Siemens, Phoenix, Eaton, Pilz eshop, Weidmüller, ebm-papst, IDEC). A row
whose only evidence is a distributor page is marked "SECONDARY" in the source column:
- for a non-safety commodity part with a large margin, it is accepted as PRICE-ONLY or DOCUMENTED, with "attach the manufacturer PDF
  at order" in the note;
- for a safety-relevant part it stays a **GAP** until the official PDF is in `docs/fonti`.

## Summary

### BOM (80 rows that count in the totals: 78 "buy" rows plus the two "make" rows with purchased content, H01..H10 and X05)

| Status | Rows | Notes |
|---|---|---|
| DOCUMENTED | **27** | 7 of them also carry residual type tests (column TP), e.g. SWD brake torque and reaction time |
| PRICE-ONLY | **23** | technical data documented; a quote is needed |
| TYPE-TEST (as primary status) | **0** | the type-test items are sub-items of documented parts (§2 lists the CALC ones) |
| GAP | **30** | 20 safety-relevant, 7 function/availability, 3 commodity (§3) |
| Excluded (in_total = N: rev A/B1 references, NPB-1700 option) | 7 | listed but not counted |

### CALC inputs (110 rows of `CALC.md` "Inputs and sources")

| Status | Rows |
|---|---|
| DOCUMENTED (manufacturer or standard document) | **45** |
| DOCUMENTED (design value: our own CAD or specification) | **30** |
| TYPE-TEST (TP-xx named) | **25** |
| GAP | **10** |

CALC tags as written: SOURCED 41, ASSUMED 33, SECONDARY 14, ESTIMATE 13, CAD 9. Three ASSUMED Kassow values are **closed in this
audit** (Kassow brochure); they change the C48 numbers (§2, rows 61–63).

### Answer to "no open questions"
**Not met yet.** The README claim "every purchased-part technical value is SOURCED" does not hold.
- **30 BOM rows and 10 CALC inputs are GAPs.** Most need only an exact P/N plus the official PDF; §3 gives the exact fix for each.
- **This audit found five design findings (F1–F5, §5) where a documented value is not yet respected by the design.** These
  matter more than the GAPs. The most important ones:
  - **F1:** the protective fields omit SICK's ground-clearance supplement Z_F = 150 mm.
  - **F3:** the ez-Wheel SWD is rated 0…+40 °C but sits in bays computed at 44–46 °C.

## 1. BOM matrix (every purchased row of `bom_amr.csv`)

Columns:
- **In total:** Y = counted in the BOM totals, N = reference row.
- **Price status:** "public" = the BOM row already has a SOURCED/SECONDARY price; "found in this audit" = a public price exists that
  the BOM does not use yet; "QUOTE needed" = no public price.
- **TP:** residual type tests that belong to a documented part.

| # | BOM id | qty | in total | technical data used by the design | official source (doc + page / URL, local file) | verbatim quote | status | type tests (TP) | note / fix | price tag (BOM) → price status | spot-checked |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `K05_rubber_edge` | 1 | Y | EPDM edge profile 22 mm (bumper/edge cover, non-safety) | none (generic 'seal distributor') | - | **GAP** | - | no P/N, no datasheet: order a catalogue profile with a datasheet (profile dims, Shore A) - non-safety, cosmetic/edge protection | ESTIMATE → QUOTE needed | - |
| 2 | `D01_ezwheel_SWD125_*` | 2 | Y | 4:1, 7.9 Nm nom / 13 Nm peak, 380 rpm, 200 W S1, 250 kg static / 200 kg @ 6 km/h, L 196 mm + 7 kg with brake, STO PL e Cat 4 PFHd 1.42E-9, SLS/SLSa/SDI pair PL d Cat 3 2.29E-7, UV/OV/OC thresholds, 0..+40 C | ez-Wheel SWD manual v2.0.2 p.13, p.28, p.34, p.89-90 (docs/fonti/ezwheel_SWD_user_manual_v2.0.2_EN.pdf); datasheet EW2A-125HN04x 07/2024 (docs/fonti/ezwheel_EW2A-125HN04x_datasheet_2024-07.pdf) | "Nominal performance 7.9 Nm at 380 rpm" "Peak torque 13 Nm" (p.13); "111 ✓ 196 7" (p.28, 1-stage + brake: L 196 mm, 7 kg); "Safe Torque Off (STO) STO1 et STO2 inputs Category 4 PL e 1,42E-9"; "Safely limited speed (SLS) Pair of SafeInput Category 3 PL d 2,29E-7" (p.89); "250 kg (static) 200 kg at 6 km/h"; "Temperatures 0 to +40 °C" (datasheet) | **DOCUMENTED** | TP-01 (SFRT), TP-03a/03b (brake), TP-03/14 (regen) | price SECONDARY (Generation Robots). Findings: CAD SWD_MASS 6.0 kg ESTIMATE vs documented 7 kg with brake; rated 0..+40 C vs bay air 44-46 C (see F3); datasheet line '7,9 daN at 9 km/h' is a datasheet typo, the manual table governs | SECONDARY → public | yes |
| 3 | `C01_castor_*_Blickle_L-ALST_80K` | 4 | Y | D80 x 30 Softhane 75 ShA, 200 kg @ 4 km/h, 500 kg static, H 102, plate 100 x 85, holes 80 x 60 d9, offset 38, 0.7 kg, -20..+70 C | blickle.com/product/l-alst-80k-754464 (docs/fonti/Blickle_L-ALST_80K_754464_product_page_2026-10-05.txt); public 3D model PDF https://cdn.blickle.info/7/75/754/754464/l-alst_80k_754464.pdf (docs/fonti/Blickle_L-ALST_80K_754464_3D-model.pdf, new) | "Load capacity at 4 km/h 200 kg … Load capacity (static) 500 kg … Total height (H) 102 mm … Plate size 100 x 85 mm … Bolt hole spacing 80 x 60 mm … Offset (F) 38 mm … Unit weight 0.7 kg"; guide: "capable of exceeding speeds of 4 km/h with a reduced load capacity" | **GAP** | TP-23 (swivel radius 360°), TP-22 (rolling) | load rating at the 5.4 km/h top speed is NOT published (only 'reduced'); swivel radius 79.4 mm calculated. Price: QUOTE. See G-04 | QUOTE → QUOTE needed | yes |
| 4 | `C03_bump_pad_*` | 4 | Y | PU pad 30x30x3, 90 ShA, bonded (end stop, load path to the roof) | none (generic die-cut) | - | **GAP** | - | no P/N/datasheet for hardness and compressive load; low risk (815 N on 900 mm2 = 0.9 MPa). Fix: buy a catalogue PU sheet with datasheet (Shore 90A) or verify in TP-23 | ESTIMATE → QUOTE needed | - |
| 5 | `C04_springs_D-313J-02` | 8 | Y | d 3.6, De 31.6, Dd 23.6, L0 53.9 ±1.44, R 14.172 N/mm, Fn 327.71 N, Fndyn 300.88 N, Ln 30.78, EN 10270-1 | Gutekunst D-313J-02 datasheet (docs/fonti/Gutekunst_D-313J-02_compression_spring_datasheet.pdf); federnshop.com/en/products/compression_springs/d-313j-02.html | "R 14,172" "Fn 327,71" "Fndyn 300,88" "Ln 30,78" "L0 53,90 + 1,44" "EN 10270-1"; "1 12,3700 € / 17 1,6600 € / 37 1,3900 €" | **DOCUMENTED** | TP-23 (preload per corner) | price public (SOURCED) | SOURCED → public | yes |
| 6 | `C06_droop_stop_*` | 4 | Y | rubber buffer type A d20 x 10 M6 + 4 mm angle (droop stop, ~5 N) | none (generic) | - | **GAP** | - | no P/N; non-safety (carries ~5 N). Fix: catalogue buffer with datasheet (e.g. a type A d20x10 M6 buffer from a norm-parts maker) - any datasheet value > 50 N is enough | ESTIMATE → QUOTE needed | - |
| 7 | `C07_rail_MGN15R_L190` | 4 | Y | MGN15 rail WR 15, HR 10, P 40, E 15, M3x10, 1.06 kg/m; rail bolt torque in aluminium 98 N·cm | HIWIN catalogue G99TE24-2410 p.91 (docs/fonti/HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p1_p91_MGN.pdf) + p.87 (docs/fonti/HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p87_MGN_bolt_torque.pdf, new) | "16 4 8.5 32 25 3.5 4.5 M3 M3x4 3 15 10 6 4.5 3.5 40 15 M3x10 1.06" (p.91); "MGN15 M3×0.5P×10L 186 (19) 127 (13) 98 (10)" (p.87, Iron/Casting/Aluminum) | **PRICE-ONLY** | - | price QUOTE (no public price). The 98 N·cm torque quoted in CASTOR_SUSPENSION was not in the saved extract: p.87 now saved | QUOTE → QUOTE needed | yes |
| 8 | `C08_blocks_MGN15H` | 8 | Y | MGN15H: C 6.37 kN, C0 9.11 kN, MR 73.5 N·m, MP/MY 57.82 N·m, 0.092 kg, block bolts M3 186 N·cm | HIWIN G99TE24-2410 p.91, p.87 (docs/fonti) | "MGN 15H 25 43.4 58.8 59.4 6.37 9.11 73.50 57.82 57.82 0.092" | **PRICE-ONLY** | - | price QUOTE | QUOTE → QUOTE needed | yes |
| 9 | `C09_castor_fasteners_set` | 1 | Y | M8x16 ISO 10642 10.9, M3x10/M3x8, M6, Loctite 243 | ISO 10642 / ISO 4762 (standard parts) | standard designation | **DOCUMENTED** | - | standard parts defined by ISO designation; property class 10.9 per ISO 898-1 (see CALC M-rows). Price ESTIMATE (catalogue item, quote-free shops exist) | ESTIMATE → QUOTE needed | - |
| 10 | `B01_battery_*_DLP-GC2-48V` | 2 | Y | 51.2 V 30 Ah 1536 Wh, 260 x 180 x 254 (275 incl. terminals), 14 kg, 15 A cont / 58 A 1 h / 90 A 10 s, LVD rec. 48 V, fuse 60 A, 23 mF precharge, lying allowed, >= 50 mm at top cover, <= 20 in parallel, IEC 62619 CB, UN 38.3, CE (EMC+RoHS) | Discover 805-0027 Rev N Table 3-1/3-2 p.4(6-7), §9.2 p.10-11, §3.6 (docs/fonti/Discover_DLP-GC2_Installation_Operation_Manual_805-0027_RevN.pdf); CB cert DK-142118-A1-UL; EU DoC 830-0047; product page .txt | "Max Continuous Discharge Current b … 15 A"; "Max Discharge Current (1 hour) … 58 A"; "Peak Discharge Current (10 seconds) … 90 A RMS"; "Low Voltage Disconnect Recommended … 48.0 V"; "Fuse … 58 V 60 A"; "Do not install upside down."; "Maintain at least 50 mm (2 in)"; "Total Height 275 mm"; "IEC 62619:2022"; DoC: "2014/30/EU EMC Directive" "2011/65/EU" | **DOCUMENTED** | TP-14 (Isc bound, BMS), TP-22 (vibration) | price: USD 1,009 from CONTEXT.md only, BOM tags it ESTIMATE -> quote/public list needed. Note: product page gives peak 90 A for 3 s, manual 10 s: use 3 s (conservative). UN 38.3 summary is not in docs/fonti (cert list only) | ESTIMATE → QUOTE needed | yes |
| 11 | `G01_lynk_gateway` | 1 | Y | P/N 950-0025, 120 x 135 x 44 mm, 13-90 V, CE, IP20 indoor, -20..50 C; relays 0-30 V DC 5 A, R1 NO/NC, R2/R3 NO | LYNK II sell sheet 885-0035 p.2; LYNK II Relay Guide §3.1 p.6, §4.1 p.7 (docs/fonti) | "Part Number 950-0025"; "LxWxH 120 x 135 x 44 mm"; "13 - 90 V"; "Marking CE"; "IP20 (Indoor Use Only)"; "The relays allow 0 to 30 VDC at a maximum of 5 A" | **PRICE-ONLY** | TP-14 (relay chain) | no public price (BOM 350 ESTIMATE). Power draw not published (minor, S24 budget: 0.4 A allowance covers it per netlist; measure TP-14) | ESTIMATE → QUOTE needed | yes |
| 12 | `S01_nanoScan3_ProIO_*` | 2 | Y | Type 3, PL d, SIL 2, PFHd 8.0E-8, tR 70 ms (n=2), field 3 m, TZ 65 mm, 16.8-30 V, 3.9 W / 15.9 W, 0.67 kg, 106.6 x 80 x 117.5 incl. plug, plane 50.5 mm, IP65, -10..+50 C, shipped without system plug | SICK data sheet NANS3-CAAZ30AN1 p.2-5 (docs/fonti/SICK_NANS3-CAAZ30AN1_datasheet_1100334.pdf); OI 8024596 p.130-137 (extracts in docs/fonti) | "Performance level PL d (EN ISO 13849)"; "PFHD … 8.0 x 10-8"; "Response time 70 ms"; "Protective field supplement 65 mm"; "Model Sensor without system plug"; "Dimensions (W x H x D) 106.6 mm x 80 mm x 117.5 mm (including system plug)"; "With maximum output load Typ. 15.9 W" | **DOCUMENTED** | TP-05/05b (plane), TP-01 (stop) | price SECONDARY (surplus dealer, warranty = dealer's). TÜV type-examination certificate not saved in docs/fonti (DoC/cert download on sick.com) - see G-28 | SECONDARY → public | yes |
| 13 | `S02_nanoScan3_system_plug_*` | 2 | Y | NANSX-AAACZZZZ1 (2105107), 300 mm cable, supply + I/O, no Ethernet | SICK OI 8024596 p.143 (extract p.16) | "nanoScan3 Pro I/O 1100334 … Cable with plug connector … NANSX-AAACZZZZ1 2105107" | **DOCUMENTED** | - | price SECONDARY (eibabo) | SECONDARY → public | yes |
| 14 | `E02_estop_*` | 2 | Y | E-stop 40 mm mushroom twist-release, ISO 13850, + holder 3 modules + 2x NC 3SU1400-1AA10-1CA0 positive opening, 10 A thermal | Siemens 3SU1400-1AA10-1CA0 data sheet p.1-2 (docs/fonti/Siemens_3SU1400-1AA10-1CA0_NC_contact_datasheet.pdf); actuator 3SU1050-1HB20-0AA0 and holder 3SU1500-0AA10-0AA0 via eibabo.de (SECONDARY) | "product function positive opening Yes"; "Contact module with 1 contact element, 1 NC"; eibabo: "Not-Halt-Pilzdrucktaster 22mm, rund, rot" "Pilzdurchmesser 40 mm" "Drehentriegelung" "Norm DIN EN ISO 13850" "Mechanische Lebensdauer typisch 300000 Schaltspiele" | **GAP** | - | contact block DOCUMENTED (official). Actuator: P/N now fixed (3SU1050-1HB20-0AA0) but only distributor data; B10d for the PL calc not in hand. Fix in G-06 | ESTIMATE → public (found in this audit: eibabo 3SU1050 EUR 22.05 gr + holder 2.25 gr + RS 3SU1400 EUR 6.57 x2) | yes |
| 15 | `E41_SB1_reset_blue` | 1 | Y | blue illuminated reset, 1 NO (PNOZ input, mA level) | Eaton M22-DL-B + M22-K10 via eibabo.de (SECONDARY; datasheet.eaton.com returns an empty shell) | M22-K10: "Kontaktelement 1 Schließer… Bemessungsbetriebsstrom Ie bei AC-15, 230 V 6 A"; M22-DL-B: "Leuchtdrucktaste flach blau… tastend" | **GAP** | - | manufacturer datasheet not retrieved; see G-07 | ESTIMATE → public (found in this audit: eibabo M22-DL-B 10.26 gr + M22-K10 5.01 gr) | - |
| 16 | `E41_SK1_key_selector` | 1 | Y | 3-position key selector (AUTO/MANUAL/SERVICE), 2 contacts | Eaton M22-WRS3 (216900) via eibabo.de (SECONDARY) | "Schlüsseltaste (MS1) 3 Stell." "drei festen Schaltstellungen" | **GAP** | - | manufacturer datasheet not retrieved; see G-07 | ESTIMATE → public (found in this audit: eibabo M22-WRS3 52.62 gr + M22-K10 5.01 gr) | - |
| 17 | `E41_SE1_M12_pendant_socket` | 1 | Y | M12 8-pole panel socket for the pendant | none (no P/N) | - | **GAP** | - | no P/N; must match the pendant (G-08) | ESTIMATE → QUOTE needed | - |
| 18 | `SE1_enabling_pendant` | 1 | Y | 3-position enabling switch IEC 60947-5-8, 2 channels, jog, M12 plug | none (only 'IDEC HE1G/HE5B class') | candidates found only on eibabo (Euchner ZSM2100-106103, ED1G-L20MB-1N): "Drei-Stufen-Aktivierungsschalter… Ausgänge: 2x Schließer… IP65… M20 x 1.5 Stecker" | **GAP** | - | no P/N, no official datasheet (IEC 60947-5-8, B10d). BOM 250 EUR is ~2x low (distributor 460-520 net). See G-08 | ESTIMATE → public (found in this audit: eibabo 547.98-620.61 gr (candidates)) | - |
| 19 | `HL1_signal_tower` | 1 | Y | 24 V signal tower + buzzer: 3 tiers, 2.5 W typ, 93 dB, IP54 | Patlite WME-302DFB-RYG spec (docs/fonti/Patlite_WME-DFB_signal_tower_spec_WME-D-W18.pdf, new); patlite.com/product/detail0000000692.html | "Rated Voltage 24V DC"; "Buzzer 1.0W"; "Sound Pressure Level (Typ.) 93dB"; "Protection Rating IP54 (IEC 60529)"; "Mounting Location Indoor Only" | **PRICE-ONLY** | - | closed by fixing the P/N to Patlite WME-302DFB-RYG (BOM/netlist still say 'Werma/Patlite class': update the P/N). Price: quote | ESTIMATE → QUOTE needed | yes |
| 20 | `E01_robopad_collector_RPCOL90` | 1 | Y | RPCOL90-100, passive, 60 A cont, 75 A 80 s on/60 s off, 60 V max even under fault, ±5 mm L/R, cables <= 2 m, 0-40 C | Roboteq RoboPad datasheet v1.3 p.2, p.7, p.14-15 (docs/fonti/Roboteq_RoboPad_Datasheet_v1.3.pdf) | "RPCOL90-100 RoboPad Extendable Collector, 90mm wide, 100A"; "Continuous Current 60 A"; "shall ensure that the voltage does not exceed 60 V DC even under under fault conditions"; "External cable lengths shall have a maximum length of 2 m" | **PRICE-ONLY** | - | price ESTIMATE (set USD 400-900) -> quote | ESTIMATE → QUOTE needed | yes |
| 21 | `E03_service_disconnect_ED250B` | 1 | Y | ED250B-L: 250 A Ith, breaks 1000 A at 96 V DC, key-lockable, no-load isolator only | Albright ED250 data sheet (docs/fonti/Albright_ED250_datasheet.pdf) | "Thermal Current Rating (Ith) 250A"; "ED250B 1000A at 96V D.C."; "Lockable ○ L"; "Do not use as a regular On-Load Switching Device." | **PRICE-ONLY** | - | price ESTIMATE -> quote | ESTIMATE → QUOTE needed | yes |
| 22 | `E10_F0_fuse_NH00_100A` | 1 | Y | 3NA3830 NH000 100 A gG, 250 V DC, 25 kA DC (tau <= 10 ms) + NH00 base 3NH3030 | Siemens 3NA3830 data sheet p.1 (docs/fonti/Siemens_3NA3830_datasheet.pdf) | "LV HRC fuse element, NH000, In: 100 A, gG, Un AC: 500 V, Un DC: 250 V"; "breaking capacity at DC with time constant ≤ 10 ms 25 kA" | **DOCUMENTED** | - | fuse link DOCUMENTED; base 3NH3030 rating not in docs/fonti (passive, 160 A class) - add its data sheet at order. Price ESTIMATE -> public distributor price exists (fork C) | ESTIMATE → QUOTE needed | yes |
| 23 | `E11_K0_contactor_SW80B_on_plate` | 1 | Y | SW80B…A: Ith 100 A / 125 A, 96 V DC with blowouts, breaks 600 A at 96 V, continuous coil 7-13 W, drop-out 50 ms with diode, aux 5 A | Albright SW80 data sheet (docs/fonti/Albright_SW80_datasheet.pdf) | "Thermal Current Rating (Ith) 100A 125A"; "SW80B 600A at 96V"; "SW80B 96V D.C."; "Continuously Rated Types 7 - 13 Watts"; "With Diode Suppression 50ms"; "Auxiliary Thermal Current Rating 5A" | **PRICE-ONLY** | - | price ESTIMATE -> quote | ESTIMATE → QUOTE needed | yes |
| 24 | `E12_K0P_precharge_relay` | 1 | Y | Finder 22.32.0.024.4340: DC1 25 A @24 V / 5 A @110 V, coil 2.2 W (83 mA table); precharge 58.4 V / 47 Ω = 1.24 A; Arcol HS50 47R (3.4 J per precharge) | Finder S22EN p.7, p.11 (docs/fonti/Finder_22-32_datasheet_S22EN_p7_p11.pdf, new) + p.3 (docs/fonti) | "Breaking capacity DC1: 24/110/220 V A 25/5/1"; "24 0.024 19.2 26.4 83"; "4 = AgSnO2", "3 = All NO contacts" | **GAP** | - | relay DOCUMENTED; G-25: Arcol HS50 short-time overload / pulse energy not documented (netlist R_pulse_J_max 50 [ASSUMED]; arcolresistors.com unreachable) | ESTIMATE → QUOTE needed | yes |
| 25 | `E17_K0T_timer_Finder80` | 1 | Y | on-delay 0.6 s (range 0.1-2 s), supply 12-240 V AC/DC, 16 A, DC1 16 A @24 V (K0 coil <= 0.54 A), -20..+60 C | Finder S80EN p.3, p.8 (docs/fonti/Finder_80-01_datasheet_S80EN_p3_p8.pdf, new) | "Rated current/Maximum peak current A 16/30"; "Breaking capacity DC1: 24/110/220 V A 16/0.3/0.12"; "240 = (12…240)V AC/DC"; "Specified time range (0.1…2)s"; "AI: On-delay" | **PRICE-ONLY** | - | BOM 'DoC (IEC 61812-1)': standard not stated in the extract - cite datasheet values. Inductive DC13 rating not given: SW80 coil has a freewheel diode (D0), so DC1 applies. Price ESTIMATE | ESTIMATE → QUOTE needed | yes |
| 26 | `E18_branch_fuses_10x38_x7` | 1 | Y | 10x38 gPV links 1000 V DC, >= 20 kA DC (V:D6) + DC-rated holders, on B48 | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | HP10M20: "Rated Voltage DC: 1000 VDC" "Breaking Capacity: 50 kA" | **GAP** | - | BOM says 'USM1 + HP10M class' (no exact P/N per position). Fix G-13: fix P/Ns HP10Mxx + CUS101HEL per position and attach the Mersen HP10M PDF (official). Technical risk low (50 kA >> 20 kA) | ESTIMATE → public (found in this audit: eibabo HP10M ~12-14 + CUS101HEL ~10.29 gr) | yes |
| 27 | `E31_F8LR_SWD_fuses` | 1 | Y | F8L/F8R 20 A on T24 (24 V DC) | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | no DC rating found for ordinary gG 10x38 links | **GAP** | - | 'gG' links have no documented DC rating: replace with HP10M20 gPV (G-13) | ESTIMATE → public (found in this audit: as E18) | - |
| 28 | `E33_F7_charge_fuse` | 1 | Y | F7 charge path on B48 (11.3 A charger, 25 A option) | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | as E18 | **GAP** | - | fix P/N (HP10M15/20) - G-13 | ESTIMATE → public (found in this audit: as E18) | - |
| 29 | `E2F_WF1-3_AUX48_fuses` | 1 | Y | WF1 6 A / WF2 12 A / WF3 2 A on B48 + FJ 8 A on 12 V | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | listed ratings HP10M1, 2, 6, 10, 12, 15, 20, 25, 30 | **GAP** | - | 6/12/2 A exist as HP10M; 8 A (FJ) does not -> HP10M10 with re-checked coordination vs the Jetson cable (G-13) | ESTIMATE → public (found in this audit: as E18) | - |
| 30 | `E13_U1_dcdc_DDR480C24` | 1 | Y | 24 V 20 A, 30 A 5 s, 33.6-67.2 V in, 92 %, OVP 28.8-35 V, 85.5 x 125.2 x 129.2, vertical only, IEC 62368-1 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | "RATED CURRENT … 20A" (C-24); "CURRENT 5sec. … 30A"; "VOLTAGE CONTINUOUS … 33.6 ~ 67.2Vdc"; "EFFICIENCY (Typ.) … 92%"; "OTHERS DIMENSION 85.5*125.2*129.2mm"; "=(The rated current per unit) x (Number of unit) x 0.9"; "Open or 5.5 ~ 10VDC power supply ON / Short or 0 ~ 0.8VDC power supply OFF"; "SAFETY STANDARDS UL 62368-1, IEC 62368-1"; manual: "mounting orientation … vertical", "40mm above and 20mm below" | **DOCUMENTED** | - | price SECONDARY (DigiKey) | SECONDARY → public | yes |
| 31 | `E14_U2_dcdc_DDR480C24` | 1 | Y | as U1 (parallel, 2 x 20 x 0.9 = 36 A) | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 32 | `E15_U4_dcdc_DDR240C24_S24` | 1 | Y | 24 V 10 A, 15 A / 360 W 3 s, 40 x 125.2 x 113.5, max 50 C (installation manual) | Mean Well DDR-240-SPEC p.2 + installation manual p.4 (docs/fonti) | "RATED CURRENT 10A"; "360W (3sec.)"; "DIMENSION 40*125.2*113.5mm"; "50°C for DDR-240 series" | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 33 | `E2G_U5_DDR120C12` | 1 | Y | 12 V 10 A, 15 A 3 s, 33.6-67.2 V, 32 x 125.2 x 102, max 55 C | Mean Well DDR-120-SPEC p.2-3 (docs/fonti) | "RATED CURRENT … 10A"; "PEAK CURRENT … 15A"; "33.6 ~ 67.2Vdc"; "DIMENSION 32*125.2*102mm"; "55°C for DDR-120 series" | **PRICE-ONLY** | - | price ESTIMATE (DigiKey price exists: fork C) | ESTIMATE → public (found in this audit: TME USD 69.20) | yes |
| 34 | `E16_R1_maxon_DSR50-5_x2` | 2 | Y | 12-50 V, threshold 26.1-27.1 V (JP1 open) or 54.3-56.1 V, max current 5 A, R_shunt 5.5 Ω -> ~133 W at 27 V per unit (300 W only on the 56 V setting), 10 W continuous at 25 C derating to 0 W at 75 C, 940 µF, 94 x 41 x 35, ~60-75 g | maxon DSR 50/5 operating instructions 2015-04 p.3, 7, 8 (docs/fonti/maxon_DSR50-5_309687_Operating_Instructions_2015-04.pdf, new, scanned) + maxongroup.com/maxon/view/product/309687 | "Threshold voltage Vth (JP1: open) 26.1...27.1 VDC"; "Max. continuous power loss Pcont without additional cooling at TU=25°C 10 W"; "Max. current 5 A"; "Once the over-temperature deactivation is enabled the supply voltage cannot be limited anymore." | **DOCUMENTED** | TP-03/TP-14 (worst regen) | price public (maxon EUR 145.15 @1-4). Findings F6: VERIFICATION MX1 used 300 W, but at 27 V each unit sinks <= 5 A (~133 W): 2 units ~265 W still >= 208 W peak; continuous ~6 W at 45 C bay; no CE statement in the manual (netlist 'CE [ASSUMED]' -> none) | SOURCED → public | yes |
| 35 | `E30_U3_ORing_DRDN40-24` | 1 | Y | 2 x 40 A in, 60 A 5 s, reverse current <= 1 mA, 55 x 125.2 x 100 | Mean Well DRDN40-SPEC p.2 (docs/fonti) | "RATED CURRENT 0~40A per input Continuous"; "PEAK CURRENT 0~60A per input 5Sec."; "INPUT REVERSE CURRENT (max.) 1mA"; "DIMENSION 55*125.2*100mm" | **PRICE-ONLY** | - | price ESTIMATE | ESTIMATE → public (found in this audit: RS EUR 55.59) | yes |
| 36 | `E34_U8_ideal_diode_DRDN40-48` | 1 | Y | DRDN40-48: 36-60 V, 40 A per input, reverse 65 V, single input | Mean Well DRDN40-SPEC p.2, p.4 (docs/fonti) | "INPUT REVERSE VOLTAGE (max.) 40Vdc 40Vdc 65Vdc"; "3. Single Use" | **PRICE-ONLY** | - | price ESTIMATE | ESTIMATE → public (found in this audit: RS EUR 54.45) | yes |
| 37 | `E19_0V_block` | 1 | Y | 0 V distribution block 2x25 / 6x10 mm2 | Weidmüller WPD 100 2X25/6X10 GY 1561910000 via eibabo.de (SECONDARY) | "Manufacturer Article Number: 1561910000"; "Rated Current: 101 A"; "Rated Voltage: 1000 V" | **PRICE-ONLY** | - | P/N fixed: WPD 100 (not 'WPD 102 class'); documented 101 A, netlist says 125 A [ASSUMED] -> correct to 101 A (still >= F0 100 A). Attach the Weidmüller PDF at order (site blocks bots) | ESTIMATE → public (found in this audit: eibabo WPD 100 EUR 42.86 gr) | - |
| 38 | `E27_XS24_terminals` | 1 | Y | S24 fuse terminals 5x20 (4/2/4/2/2/1 A) + feed-through + bridges | Phoenix PT 4-HESI (5x20) 3211861 via eibabo.de (SECONDARY); PT 2,5 / PT 4 / FBS not retrieved | "Rated Current: 6.3 A"; "Rated Voltage: 500 V"; "G / 5 x 20"; "IEC 60947-7-3" | **PRICE-ONLY** | - | fuse-terminal rating covers the sub-fuses; feed-through terminals carry only cross-section data (no other rating used). The 5x20 fuse links themselves have no P/N -> add (non-safety, S24 branch) | ESTIMATE → QUOTE needed | - |
| 39 | `E32_T24_terminals` | 1 | Y | T24 power terminals, up to 36 A cont / 54 A peak | Phoenix PTPOWER 16: rating not retrieved (phoenixcontact.com 403) | - | **GAP** | - | G-21: rated current not documented. Replace with the documented Weidmüller WPD 100 (101 A) or attach the Phoenix PTPOWER 16 PDF | ESTIMATE → QUOTE needed | - |
| 40 | `E35_RSIG_X0R` | 1 | Y | 10 kΩ 2 W signature resistor in a component terminal | none (generic resistor; component terminal not retrieved) | - | **GAP** | - | non-safety-critical value (signature for the dock); G-21: fix resistor P/N with datasheet (any 2 W metal-film) | ESTIMATE → QUOTE needed | - |
| 41 | `E37_KS_signature_relay` | 1 | Y | Finder 38.51.7.024.0050: coil 10.4 mA / 0.3 W at 24 V (<= 75 mA PNOZ aux), contact 6 A, DC1 6 A @24 V, min load 500 mW | Finder S38EN p.5, p.13 (docs/fonti/Finder_38-51_datasheet_S38EN_p5_p13.pdf, new) | "Rated current/Maximum peak current A 6/10"; "Breaking capacity DC1: 24/110/220 V A 6/0.2/0.12"; "24 7.024 19.2 28.8 10.4 0.3"; "35 mm rail (EN 60715)" | **PRICE-ONLY** | - | netlist coil 9 mA [ASSUMED] -> 10.4 mA (documented). Check: the KS contact switches the 10 kΩ signature at up to 58 V = 5.8 mA, below the 500 mW (10 mA @12 V) minimum switching load -> contact reliability, not safety; use a gold-contact variant if TP-13 shows flicker | ESTIMATE → QUOTE needed | yes |
| 42 | `E36_CAN1_PCAN-Ethernet_gw` | 1 | Y | IPEH-004010: 2x HS-CAN ISO 11898-2, 8-30 V (100-360 mA), 22.5 x 99 x 114.5 mm, IP20, -40..85 C, CE (EN 55032/55035) | PEAK user manual 2.1.0 p.64-66 (docs/fonti/PEAK_PCAN-Ethernet_Gateway_DR_UserMan_2.1.0_p1-6-64-66.pdf, new) + price list (docs/fonti/PEAK_Pricelist_valid_2026-08-21.pdf, new) | "Supply voltage 8 to 30 V DC"; "Max. current consumption 360 mA at 8 V, 240 mA at 12 V, 100 mA at 30 V"; "EMC EU Directive 2014/30/EU DIN EN 55032:2022-08 DIN EN 55035:2018-04"; price list IPEH-004010 EUR 294.00 net EXW | **DOCUMENTED** | - | price now PUBLIC EUR 294 (BOM 520 ESTIMATE is 226 EUR high). CAD envelope 45 x 90 x 100 is wrong: real 22.5 x 99 x 114.5 | ESTIMATE → public (found in this audit: PEAK price list EUR 294.00 net) | yes |
| 43 | `E25_NET1_switch_FL1008N` | 1 | Y | 8-port Ethernet switch, 22.5 x 147.5 x 98.4 mm, IP30 | Phoenix FL SWITCH 1008N 1085256 via eibabo.de (SECONDARY) | "Manufacturer Article Number: 1085256"; "acht RJ45-Ports mit 10/100 MBit/s" | **GAP** | - | G-21: supply range/power not retrieved (netlist '24 V, ~3 W [ASSUMED]'); P/N is 1085256. CAD envelope 40 mm wide is conservative | ESTIMATE → public (found in this audit: eibabo EUR 168.81 gr) | - |
| 44 | `E26_SR1_RLY3-OSSD100` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | ESTIMATE → QUOTE needed | - |
| 45 | `E2C_K1_contactor_3RT2026` | 1 | Y | DC-1 35 A (2 poles in series, 60 V), coil 5.9 W, mirror contacts, B10 1E6 / 73 % -> B10D 1.37E6, 45 x 85 x 107 | Siemens 3RT2026-1BB40 data sheet p.2-6 (docs/fonti/Siemens_3RT2026-1BB40_datasheet.pdf) | "with 2 current paths in series at DC-1 … at 60 V rated value 35 A"; "holding power of magnet coil at DC 5.9 W"; "mirror contact according to IEC 60947-4-1 Yes"; "B10 value with high demand rate according to SN 31920 1 000 000" with "73 %" dangerous share (B10D = 1.37E6); "width 45 mm" "depth 107 mm" | **PRICE-ONLY** | - | price ESTIMATE (public distributor price exists: fork C). B10D now DOCUMENTED (netlist used 1.3E6 'Annex C ASSUMED') | ESTIMATE → public (found in this audit: RS EUR 202.10 / TME USD 96.45) | yes |
| 46 | `E2D_K2_contactor_3RT2026` | 1 | Y | as K1 | Siemens 3RT2026-1BB40 data sheet p.2-6 (docs/fonti/Siemens_3RT2026-1BB40_datasheet.pdf) | as E2C | **PRICE-ONLY** | - | as K1 | ESTIMATE → public (found in this audit: RS EUR 202.10 / TME USD 96.45) | yes |
| 47 | `E0x_din_rails` | 1 | Y | TS35 x 7.5 per EN 60715, 10 pieces | Phoenix NS 35/7,5 via eibabo.de; EN 60715 cited in Finder S38EN | "NS 35/7,5 Unperf 2m"; "35 mm rail (EN 60715)" | **DOCUMENTED** | - | standard section; price public (EUR 9.54 gross per 2 m) | ESTIMATE → public (found in this audit: eibabo NS 35 EUR 9.54 gr / 2 m) | - |
| 48 | `E0C_centre_rails` | 2 | Y | TS35 EN 60715, 130 mm (CAD: 4 pieces 154/154/154/21 mm) | EN 60715 | - | **DOCUMENTED** | - | MISMATCH: BOM qty 2 x 130 mm vs CAD 4 rails E0C_L/R_low/high | ESTIMATE → QUOTE needed | - |
| 49 | `E58_U6_DDR60L5` | 1 | Y | 5 V 12 A, 18-75 V in, 52.5 x 90 x 54.5 | Mean Well DDR-60-SPEC p.2 (docs/fonti) | "RATED CURRENT … 12A" (DDR-60L-5); "VOLTAGE RANGE … 18 ~ 75Vdc"; "DIMENSION 52.5*90*54.5mm" | **PRICE-ONLY** | - | price ESTIMATE | ESTIMATE → public (found in this audit: RS EUR 47.34) | yes |
| 50 | `E59_JR1_relays` | 1 | Y | 2x relay module, 5 V coil, driven by Jetson GPIO | Phoenix PLC-RSC-5DC/21 via eibabo.de (SECONDARY) | input current "0.038A" at 5 V | **GAP** | - | G-22 design finding: 38 mA cannot be driven by a Jetson GPIO directly -> add a driver (e.g. 24 V coil PLC-RSC-24DC/21, 9 mA, switched by a GPIO-driven transistor/opto) and document it | ESTIMATE → public (found in this audit: eibabo EUR 11.53 each gr) | - |
| 51 | `E5A_XC_deck_terminals` | 1 | Y | feed-through terminals PT 1.5 / PT 4 (cross-section only) | Phoenix catalogue (not retrieved) | - | **PRICE-ONLY** | - | only cross-section is used; currents <= 16 A coffee, 5 V head. Attach the Phoenix PT datasheet at order (evidence upgrade) | ESTIMATE → QUOTE needed | - |
| 52 | `E40_fan_*` | 4 | Y | 60x60x25 24 V IP54 fan + filter, ~15 m3/h effective (10 W/K per bay pair) | none ('ebm-papst class'; 614 NGHH page JS-only) | - | **GAP** | - | thermally relevant for S24 (DDR-240 50 C max) and the SWD (40 C max). See G-10 | ESTIMATE → QUOTE needed | - |
| 53 | `E42_gap_fan_*` | 2 | Y | 40x40x20 24 V fan + guard, ~8 m3/h effective | none ('ebm-papst class') | - | **GAP** | - | see G-10 | ESTIMATE → QUOTE needed | - |
| 54 | `E21_SC0_PNOZ_m_B0` | 1 | Y | 20 safe in, 4 SC out 2 A (0-2.5 A, <= 1 µF), 4 configurable aux outputs 75 mA, PL e Cat 4, PFHd CPU 4.74E-10 / SC out 1.66E-11 / in 7.95E-11, 1.6 A supply, test pulse <= 330 µs, terminals 751008 not included | Pilz PNOZ m B0 manual 1002660-EN-13 p.8, p.29, p.44-48, p.52 (docs/fonti/Pilz_PNOZ_m_B0_OperManual_1002660-EN-13.pdf) | "CPU 2-channel PL e Cat. 4 SIL 3 4,74E-10"; "SC outputs … PL e Cat. 4 SIL 3 1,66E-11"; "Two loads may be connected to each safety output with advanced fault detection"; "Output current 75 mA"; "supply must provide 1,6 A"; "Max. duration of off time during self test 330 µs" | **DOCUMENTED** | - | price SECONDARY (eibabo). TÜV certificate not saved locally (see G-28) | SECONDARY → public | yes |
| 55 | `E22_SX1_PNOZ_m_EF_8DI4DO` | 1 | N | rev B1 reference (not in build) | EF 8DI4DO manual 1002661-EN-08 (docs/fonti) | "CPU 2-channel PL e Cat. 4 SIL 3 2,84E-10" | **EXCLUDED (in_total=N)** | - | in_total = N; BOM source URL is the B0 page (copy-paste) | SECONDARY → public | - |
| 56 | `E20_SC1_PNOZ_m_ES_ETH` | 1 | Y | Modbus/TCP slave, 2x RJ45, standard (non-safety) module, ~1 W | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.458 (extract p.14, docs/fonti) | "Application range Standard"; "Fieldbus interface Modbus/TCP" | **DOCUMENTED** | - | price SECONDARY (BOM source URL points to the B0 page: fix) | SECONDARY → public | yes |
| 57 | `E2H_SR1_PNOZ_m_EF_4DI4DOR` | 1 | Y | 4 safe in, 4 positive-guided relay outputs, DC1 24 V 6 A / min 10 mA, PL e Cat 4 PFH 7.52E-12, 22 ms | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.26-28, p.207-221 (extract p.10-12, docs/fonti) | "Min. current 10 mA"; "Relay outputs 2-channel PL e Cat. 4 SIL 3 7,52E-12"; "tReactionMax = 2 ms + 30 ms + 22 ms = 54 ms"; "772143" | **DOCUMENTED** | - | price SECONDARY (eibabo 379.72 net) | SECONDARY → public | yes |
| 58 | `E2I_SR2_PNOZ_m_EF_4DI4DOR` | 1 | Y | as SR1 | Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.26-28, p.207-221 (extract p.10-12, docs/fonti) | as E2H | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 59 | `RB1-7_bleed_resistors` | 7 | Y | 2.2 kΩ 1 W (0.26 W used) | none (generic resistor) | - | **GAP** | - | G-21: fix resistor P/N + datasheet (power rating at 45-55 C bay air); function is availability (relay min. load), not safety | ESTIMATE → QUOTE needed | - |
| 60 | `E2J_KI4_interposing_relay` | 1 | Y | PLC-RSC-24DC/21 2966171: 24 V input 9 mA (18.5-33.6 V), contact 6 A 250 V, free-wheel diode | eibabo.de/phoenix/interface-plc-rsc-24dc-21-eb10458088 (SECONDARY) | "Herstellerartikelnummer 2966171"; "Typischer Eingangsstrom 9 mA"; "Schaltstrom bis 6 A"; "Verpolschutzdiode und Freilaufdiode" | **PRICE-ONLY** | - | P/N no longer ASSUMED; attach the Phoenix PDF at order (evidence upgrade) | ESTIMATE → public (found in this audit: eibabo EUR 10.34 gr) | - |
| 61 | `E2K_K0V_LVCO_relay_DUB01CD48500V` | 1 | Y | DUB 01 C D48 500V: ranges 5-50 V (350 V max) / 20-200 V, level 10-110 % FS, hysteresis 0-30 %, delay 0.1-30 s, repeatability ±0.5 % FS, DC13 2.5 A @24 V, 24-48 V supply, 22.5 x 80 x 99.5, EN 60255-6, UL/CSA/CCC | Carlo Gavazzi DUB01/PUB01 data sheet 2025-03-03 p.1-3 (docs/fonti/CarloGavazzi_DUB01-PUB01_datasheet_2025-03-03.pdf) | "DIN-rail SPDT … 2 to 500 V AC/DC … DUB 01 C D48 500V"; "5 to 50 V AC/DC >500 kΩ 350 V"; "Repeatability ± 0.5% on full-scale"; "DC 13 2.5 A @ 24 VDC"; "Dimensions DUB01 22.5 x 80 x 99.5 mm"; "OFF: Normally Energized"; "Product standard EN 60255-6"; "Approvals UL, CSA, CCC" | **DOCUMENTED** | - | price SECONDARY (DigiKey USD 177.65) | SECONDARY → public | yes |
| 62 | `D0_coil_suppression_set` | 1 | Y | K1/K2 (3RT2026, size S0): suppressor; K0 SW80 coil (<= 0.54 A): freewheel diode | Siemens 3RT2926-1BB00 varistor 24-48 V AC / 24-70 V DC via eibabo.de (SECONDARY); diode terminal: Phoenix UKK 5-DIO/O-U 2791016 rated 0.5 A only | "Überspannungsbegrenzer 24-48VAC24-70VDC 3RT2926-1BB00"; UKK 5-DIO: "Bemessungsstrom In: 0,5 A" | **GAP** | - | G-23: K1/K2 suppressor P/N now 3RT2926-1BB00 (varistor, fast drop-out). SW80 freewheel diode: no documented >= 1 A diode terminal found (UKK 5-DIO 0.5 A < 0.54 A coil). Note Albright states drop-out 50 ms 'with diode suppression' -> a diode is required | ESTIMATE → QUOTE needed | - |
| 63 | `SCT_PNOZ_terminal_sets` | 1 | Y | B0: 751008 (spring); EF: 751004 (spring) | Pilz PNOZ m B0 manual 1002660-EN-13 p.8, p.29, p.44-48, p.52 (docs/fonti/Pilz_PNOZ_m_B0_OperManual_1002660-EN-13.pdf); EF manual p.30 | "PNOZ s Set1 spring- Set of plug-in replacement terminals 8-pin of spring-loaded type, 751008"; "… 4-pin of spring-loaded type, 751004" | **PRICE-ONLY** | - | P/N DOCUMENTED; price ESTIMATE (fork A) | ESTIMATE → public (found in this audit: eibabo 751008 29.61 + 751004 28.54 net) | yes |
| 64 | `E20_SC0_flexisoft_FX3-CPU1` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 65 | `E24_SC1_flexisoft_FX0-GENT` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 66 | `E21/E22/E28/E29/E2A_SX1-SX5_FX3-XTIO` | 5 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 67 | `E23_SM1_FX3-MOC1` | 1 | N | rev A reference (not in build) | - | - | **EXCLUDED (in_total=N)** | - | in_total = N | SECONDARY → public | - |
| 68 | `H01..H10` | 1 | Y | harness: H07Z-K / Lapp OLFLEX cable by cross-section, SICK M12 cordsets, lugs | cable_schedule.csv + netlist ampacity table (IEC 60204-1 Table 6 'recalled', ASSUMED); Lapp T12 (docs/fonti/Lapp_T12_Strombelastbarkeit_technical_table.pdf, new) gives only derating factors | Lapp T12: "40 °C … 0,87" (70 °C conductor) | **GAP** | - | G-14: the B2/E ampacity values are not documented; derating 0.87 at 40 C is now documented. Fix: buy EN 60204-1 (Table 6) or size from the cable maker's own rating table for the chosen cable | ESTIMATE → QUOTE needed | - |
| 69 | `E53_deck_grommet` | 1 | Y | cable entry frame IP54+, 60 x 110 opening | icotek KEL-DPZ series page icotek.com/en/products/cable-entry-plates/kel-dpz | "Certified protection up to IP66 (acc. to EN 60529)"; "UL94-V0"; "matches exactly the cut-out dimensions of 6-, 10-, 16- and 24-pin standard industrial connectors" | **PRICE-ONLY** | - | DOCUMENTED at series level: fix the size (KEL-DPZ 24 class for 60 x 110) in the BOM. Price: quote | ESTIMATE → QUOTE needed | - |
| 70 | `Z01_fasteners_consumables` | 1 | Y | ISO 4762/7380 screws, PEM, inserts, ties, Lapp Skintop glands, labels | ISO standard designations / catalogue items | standard designation | **DOCUMENTED** | - | standard parts; gland IP rating per Lapp catalogue at order (non-safety). Price ESTIMATE | ESTIMATE → QUOTE needed | - |
| 71 | `X02_robopad_base_RPBAS90` | 1 | Y | RPBAS90-100 charging base, 100 A, 60 V max, EN 61000-6-1/-6-3 tested | Roboteq RoboPad datasheet v1.3 p.2, p.12 (docs/fonti) | "RPBAS90-100 RoboPad Charging Base, 90mm wide, 100A"; "EN IEC 61000-6-3 E3:2021" | **PRICE-ONLY** | - | price ESTIMATE -> quote. BOM P/N 'RPBAS90' -> 'RPBAS90-100' | ESTIMATE → QUOTE needed | yes |
| 72 | `X04_charger_NPB750_48` | 1 | Y | NPB-750-48: CC 11.3 A, DIP 'flooded' 56.8/53.6 V, OVP 82-100 V, EMC Class B, IEC 60335-2-29, CANBus 2.0B, 230 x 158 x 67 mm | Mean Well NPB-750-SPEC p.1-5 (docs/fonti/MeanWell_NPB-750-SPEC.pdf) | "MAX. OUTPUT CURRENT(CC) … 11.3A"; "Pre-defined, flooded battery 56.8 … 53.6"; "Radiated BS EN/EN55032 (CISPR32),BS EN/EN55014-1 Class B"; "IEC60335-1/2-29"; "DIMENSION 230*158*67mm (L*W*H)" | **DOCUMENTED** | - | price ESTIMATE (DigiKey price exists: fork C). MISMATCH: CAD still models X04_charger_NPB1700_48 (150 x 100 x 180 mm, 3.3 kg) = neither NPB-750 (230 x 158 x 67) nor NPB-1700 (307.7 x 184 x 70) | ESTIMATE → public (found in this audit: RS EUR 171.72) | yes |
| 73 | `X05_dock_controller_relay` | 1 | Y | dock controller + DC contactor with blowouts ('Albright SW60 class') in a DIN box | none (no P/N) | - | **GAP** | - | G-24: use the already-documented Albright SW80B (600 A at 96 V) as dock contactor and name the controller P/N; the dock is a separate LVD/EMC product (G11) | ESTIMATE → QUOTE needed | - |
| 74 | `X06_apriltag_reflector_plate` | 1 | Y | AprilTag + retro-reflective plate at z 380-500 (above the scan plane) | custom print (no technical rating needed) | - | **DOCUMENTED** | - | design-defined part; the only technical rule (no reflector within the scan plane, SICK OI p.27 ZR) is a placement rule | ESTIMATE → QUOTE needed | - |
| 75 | `X08_dock_harness_ac` | 1 | Y | mains cable, switch, glands | none ('Lapp Oelflex + switch') | - | **GAP** | - | no P/N for the mains switch / cable; part of the dock LVD file (G11). Fix: define cable type (e.g. Lapp ÖLFLEX CLASSIC 110 3G1.5) and a rated switch with datasheet | ESTIMATE → QUOTE needed | - |
| 76 | `X09_dock_OV_relay_DUB01CD48500V` | 1 | Y | as K0V, 20-200 V range, bench-set 58.5 V | as E2K | as E2K | **DOCUMENTED** | - | price SECONDARY. ID clash: CAD calls it X08_dock_OV_relay_DUB01 (BOM X08 = dock harness) | SECONDARY → public | yes |
| 77 | `X04b_charger_NPB1700_48_option` | 1 | N | option, not in total | Mean Well NPB-1700-SPEC (docs/fonti) | "MAX. OUTPUT CURRENT(CC) … 25A"; "Radiated … Class A" | **EXCLUDED (in_total=N)** | - | in_total = N (option) | SECONDARY → public | - |
| 78 | `E50_dcdc_arm_*_DDR480C24` | 2 | Y | as E13 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | yes |
| 79 | `E52_arm_ORing_DRDN40-24_x2` | 1 | Y | 2x DRDN40-24 + 2x DSR 50/5 | DRDN40-SPEC + maxon 309687 | as E30 / E16 | **DOCUMENTED** | - | price: DSR public (maxon), DRDN40 ESTIMATE. CAD splits this row into E52_L/R + E5B_L/R | ESTIMATE → QUOTE needed | - |
| 80 | `E57_FAL_FAR_fuses` | 1 | Y | FAL/FAR 25 A on the 24 V arm buses | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | HP10M25 listed | **GAP** | - | replace 'gG' by HP10M25 gPV (G-13) | ESTIMATE → public (found in this audit: as E18) | - |
| 81 | `SP1_SP2_PSEN_cs3.1` | 2 | Y | PSEN cs3.1 541009 + cs3.11: 2 OSSD, Sao 8 mm / Sar 20 mm, IP67, M12 8-pole, coding 'Low' (ISO 14119) | eibabo.de/pilz/sicherheitssensor-m12-8-0.15m-psen-cs3.1-541009-eb16315335 (SECONDARY; Pilz eshop 403) | "Kodierstufe nach ISO 14119: Low"; "Anzahl sichere Ausgänge 2 OSSD"; "gesicherter Ansprechabstand 8 mm… gesicherter Abschaltabstand 20 mm"; "Schutzart IP67" | **GAP** | - | PL / PFHd / ISO 14119 type not in hand from Pilz (OA variant, superstructure). See G-09 | SECONDARY → public | - |
| 82 | `E54_U7_DDR480C24_coffee` | 1 | Y | as E13 | Mean Well DDR-480-SPEC p.2-4 (docs/fonti/MeanWell_DDR-480-SPEC.pdf) + DDR installation manual p.2-4 | as E13 | **DOCUMENTED** | - | price SECONDARY | SECONDARY → public | - |
| 83 | `E55_K4_Finder22` | 1 | Y | DC1 25 A at 24 V per contact, coil 2.2 W (92 mA) | Finder 22 p.3 (docs/fonti) | "Breaking capacity DC1: 24/110/220 V A 25/5/1" | **PRICE-ONLY** | - | price ESTIMATE | ESTIMATE → QUOTE needed | - |
| 84 | `E56_FCF_fuse` | 1 | Y | FCF 16 A on the 24 V coffee feed | Mersen HP10M gPV 10x38 via eibabo.de (SECONDARY: "Rated Voltage DC: 1000 VDC"; "Breaking Capacity: 50 kA"; "gPV"; "IEC 60269-6"), holder CUS101HEL "10x38 DC1000V 32A"; Mersen PDF not reachable (us.mersen.com 404) | no HP10M16 in the listing | **GAP** | - | HP10M15 or HP10M20 after coordination check (G-13) | ESTIMATE → public (found in this audit: as E18) | - |
| 85 | `E28_SX2_PNOZ_m_EF_8DI4DO_C48` | 1 | Y | 8 safe in, 4 SC out, PL e, CPU 2.84E-10, inputs 4.27E-11, SC out 2.12E-11, pulse suppression 0.5 ms | Pilz EF 8DI4DO manual 1002661-EN-08 p.24, 27 (docs/fonti) | "CPU 2-channel PL e Cat. 4 SIL 3 2,84E-10"; "Pulse suppression 0,5 ms" | **DOCUMENTED** | - | price SECONDARY (BOM URL = B0 page) | SECONDARY → public | yes |
| 86 | `K3_arm_precharge_C48` | 1 | Y | Finder 22.32 + Arcol HS50 10R on the 48 V arm feed: 58.4 V / 10 Ω = 5.8 A | Finder 22 p.3 / S22EN (docs/fonti) | "Breaking capacity DC1: 24/110/220 V A 25/5/1" | **GAP** | - | 5.8 A at 58 V exceeds the documented 5 A @110 V row (24 V row does not apply). G-11: 12 Ω (4.9 A) or 3RT2026; plus G-25 resistor pulse rating | ESTIMATE → QUOTE needed | - |
| 87 | `E51_jetson_orin_nx_carrier` | 1 | Y | Orin NX 16 GB module 10/15/25/40 W; carrier not chosen | nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/ | "Power 10W - 15W - 25W - 40W" (Orin NX 16GB column) | **GAP** | - | module DOCUMENTED; carrier P/N, its power-input connector rating (netlist 8 A ASSUMED) and its EMC/RED DoC are not defined (superstructure, G6) | ESTIMATE → QUOTE needed | - |

### 1.1 BOM ↔ `out/parts.json` mismatches (purchased parts)

`parts.json` has 106 purchased parts and 10 harness centre lines. Every purchased CAD part maps to a BOM row except the ones below.

| # | CAD (`parts.json`) | BOM | Mismatch | Fix |
|---|---|---|---|---|
| M1 | `X04_charger_NPB1700_48` (150 × 100 × 180 mm, 3.3 kg) | `X04_charger_NPB750_48` (default) | CAD still models the NPB-1700 option, and with an envelope that matches neither charger: NPB-750 is 230 × 158 × 67 mm, NPB-1700 is 307.7 × 184 × 70 mm (Mean Well specs) | model NPB-750-48 at 230 × 158 × 67, mass from Mean Well (packing 1.84 kg) |
| M2 | `X08_dock_OV_relay_DUB01` | `X09_dock_OV_relay_DUB01CD48500V` (BOM `X08` = dock harness) | ID clash | rename CAD part to X09 |
| M3 | `E0C_L_din_rail_low/high`, `E0C_R_din_rail_low/high` (4 rails: 154/154/154/21 mm) | `E0C_centre_rails` qty 2 × 130 mm | quantity and length | BOM qty 4 (3 × 154 + 1 × 21 mm) |
| M4 | `E18_branch_fuses_10x38_x6` | `E18_branch_fuses_10x38_x7` | 6 vs 7 positions | count the netlist positions and align |
| M5 | `E2L_FJ_fuse_Jetson12V` (separate part) | FJ is inside `E2F_WF1-3_AUX48_fuses` (x4) | ID split | fine for cost; add the CAD id to the BOM note |
| M6 | `E5B_arm_clamp_L/R_DSR50-5`, `E52_arm_ORing_L/R_DRDN40-24` | one bundle row `E52_arm_ORing_DRDN40-24_x2` | ID split | fine for cost; list the CAD ids in the BOM row |
| M7 | `E36_CAN1_PCAN-Ethernet_gw` 45 × 90 × 100 mm | – | real device 22.5 × 99 × 114.5 mm (PEAK manual p.65): 14.5 mm deeper than modelled | update the envelope and re-run the keep-out check |
| M8 | `D01_ezwheel_SWD125_*` mass 6.0 kg ("not published") | – | published: 7 kg with brake, L 196 mm (SWD manual p.28) | SWD_MASS = 7.0 (CALC mass +2 kg) |
| M9 | `K06_jetson_cover` (custom) | none | custom part missing from the BOM | add a make row |
| M10 | `K05_rubber_edge` category custom | BOM make_buy = buy | classification only | – |
| M11 | `A02_top_deck` 15 mm (amr_params DECK_T = 15) | BOM process "waterjet **10 mm** 6082-T6" | thickness (and cost) | BOM text 15 mm; the CALC §1 intro also still says 10 mm |
| M12 | – | `X02_robopad_base_RPBAS90` | order code is **RPBAS90-100** (RoboPad v1.3 p.2) | fix the P/N |
| M13 | `E25_NET1_switch_FL1008N` | P/N not given | Phoenix P/N is **1085256**, 22.5 mm wide (CAD 40 mm, conservative) | add the P/N |

Purchased BOM rows with no CAD solid, by design: S02 system plugs, E41 rear-panel devices other than the three modelled, SE1, HL1,
SP1/SP2, C09, Z01, D0, SCT, RB1-7 (inside E27), E28/K3 (C48 slot), X06/X08 dock items. This is consistent.


## 2. CALC inputs matrix (`CALC.md` "Inputs and sources", all 110 rows)

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
| 18 | gripper/fingers beyond the payload point | 50 mm | ESTIMATE | **GAP** | G-15: take from the OpenArm gripper CAD (open source) or measure; feeds the 762 mm hazard radius |
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
| 40 | castor load capacity 4 km/h / static | 200 / 500 kg | SOURCED | **DOCUMENTED** | Blickle 754464 (at 5.4 km/h: see BOM C01 / G-04) |
| 41 | MGN15H C0 / C / MR | 9.11 / 6.37 kN / 73.5 N·m | SOURCED | **DOCUMENTED** | HIWIN G99TE24-2410 p.91 |
| 42 | floor unevenness under one castor | 5 mm | ASSUMED | **TYPE-TEST TP-23** | site requirement (manual) + TP-23 drive share with a 5 mm shim |
| 43 | scan plane height limit | 200 mm | SOURCED | **DOCUMENTED** | SICK OI p.40 "maximum height of 200 mm everywhere" |
| 44 | scan-plane mounting tolerance | 5 mm | ASSUMED | **TYPE-TEST TP-05** | acceptance 184.5 ± 5 mm at every field edge |
| 45 | pitch dynamic amplification | 1.2 | ASSUMED | **TYPE-TEST TP-05b** | measured while accelerating per band |
| 46 | battery energy (2 packs) | 3.08 kWh | SOURCED | **DOCUMENTED** | 805-0027 Table 3-1 "Energy … 1536 Wh" x 2 = 3.07 kWh |
| 47 | usable fraction above 48 V | 0.88 | ESTIMATE | **TYPE-TEST TP-22** | runtime/energy only, measured in TP-22 |
| 48 | bus nominal | 51.2 V | SOURCED | **DOCUMENTED** | Table 3-1 "Nominal Voltage … 51.2 V" |
| 49 | bus minimum under peak load | 44 V | ASSUMED | **GAP** | G-16: use the documented BMS LVD 40.0 V (Table 3-1) for worst-case peak currents (the netlist already does) |
| 50 | application LVCO K0V | 48 V | SOURCED | **DOCUMENTED** | Table 3-1 "Low Voltage Disconnect Recommended … 48.0 V" |
| 51 | pack continuous discharge | 15 A | SOURCED | **DOCUMENTED** | Table 3-1 |
| 52 | pack 1 h discharge | 58 A | SOURCED | **DOCUMENTED** | Table 3-1 |
| 53 | pack peak discharge | 90 A RMS (10 s) | SOURCED | **DOCUMENTED** | Table 3-1 10 s; product page says 3 s: use 3 s where duration matters |
| 54 | BMS over-discharge trip | > 58 A for 10 s | SOURCED | **DOCUMENTED** | Table 3-4 |
| 55 | pair ratings | 30 / 116 / 180 A | SOURCED | **DOCUMENTED** | Table 3-9 |
| 56 | DDR-480C-24 rated current | 20 A | SOURCED | **DOCUMENTED** | DDR-480-SPEC p.2 |
| 57 | DDR-480C-24 peak (5 s) | 30 A | SOURCED | **DOCUMENTED** | DDR-480-SPEC p.2 "CURRENT 5sec. … 30A" |
| 58 | OpenArm per arm typ | 70 W | SECONDARY | **GAP** | G-17: internal ARCHITECTURE.md, no manufacturer document (OA variant only) |
| 59 | OpenArm per arm cont | 360 W | SECONDARY | **GAP** | G-17 |
| 60 | OpenArm per arm peak (5 s) | 720 W | SECONDARY | **GAP** | G-17 |
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
| 74 | arm 24 V feed cross-section | 4 mm² | ASSUMED | **GAP** | G-14: ampacity basis (IEC 60204-1 Table 6) not documented |
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
| 99 | deck effective strip width | 100 mm | ESTIMATE | **GAP** | G-19: result depends on it (b = 62 mm lower bound gives 0.71 mm > 0.55 mm limit); plate FE or the rib CALC §9 proposes |
| 100 | M6 8.8 preload in tapped 6082 | 7000 N | ASSUMED | **GAP** | G-20: no free ISO 898-1 / VDI 2230 table retrieved; fix: tighten to a documented preload table at order, or verify by torque-tension test |
| 101 | coffee uprights on the deck | (-228,-118),(-228,175) | CAD | **DOCUMENTED (design value)** | integration.json |
| 102 | arm hazard radius | 762.5 mm | ESTIMATE | **DOCUMENTED (design value)** | computed from the poses above (depends on G-15) |
| 103 | base swept radius | 436.3 mm | CAD | **DOCUMENTED (design value)** | out/stl |
| 104 | superstructure swept radius | 440 mm | CAD | **DOCUMENTED (design value)** | integration.json |
| 105 | logistics drive cycle | 1.0 m/s, stop every 10 m | ASSUMED | **DOCUMENTED (design value)** | use-case definition (runtime claim conditions) |
| 106 | duty profiles | logistics / barista / idle-heavy | ASSUMED | **DOCUMENTED (design value)** | use-case definition |
| 107 | main fuse F0 | 100 A | SOURCED | **DOCUMENTED** | Siemens 3NA3830 data sheet |
| 108 | SW80B Ith | 100 A | SOURCED | **DOCUMENTED** | Albright SW80 "Thermal Current Rating (Ith) 100A 125A" |
| 109 | tower roof effective width | 2 x 43 + 30 mm | ESTIMATE | **DOCUMENTED (design value)** | bounded: with the 30 mm pad width alone the roof stress is 51 x 116/30 = 197 MPa <= 237 MPa, so the PASS does not depend on the estimate |
| 110 | roof flange bolts M6 8.8 As / Rp0.2 | 20.1 mm², 640 MPa | SOURCED | **GAP** | G-20: ISO 898-1 values not retrieved from a free document in this audit (standard values; fix with a fastener-maker table at order) |

Effect of the three Kassow rows closed here (C48 variant only):
- idle 40 → 75 W per arm raises the idle-heavy C48 draw;
- typ 350 → 200–300 W lowers the working draw;
- peak 1000 → 1200 W per arm (KR1018/1410/1805) or 600 W (KR810/1205), against the brochure's "Max external fuse (A) 25" and
  "Supply voltage (VDC) 42-58".

Re-run `amr_calc.py` with these values before the C48 runtimes (README: 6.7 / 3.0 h) are quoted again.


## 3. GAP list and how to close each one (target: zero)

"Closed now" means this audit found the document. "Replace" gives the exact documented alternative. "S" = safety-relevant,
"F" = function or availability, "C" = commodity.

| GAP | Rows | Sev. | What is missing | Closed now / exact fix |
|---|---|---|---|---|
| G-01 | K05, C03, C06, X08 | C/C/C/S | no P/N or datasheet: EPDM edge profile, PU pad, rubber buffer; dock mains cable and switch | Order catalogue items with a datasheet. X08 (mains, LVD): a rated cable (e.g. Lapp ÖLFLEX CLASSIC 110 3G1.5) and a mains switch with a datasheet, inside the dock's LVD file (CE G11). The PU pad and buffer are non-safety (0.9 MPa and 5 N); TP-23 checks them. |
| G-04 | C01 Blickle L-ALST 80K | S | rating at the 5.4 km/h top speed: Blickle only writes "reduced load capacity". Swivel radius 79.4 mm is calculated. | **Partly closed now:** the official 3D model is public without login (`docs/fonti/Blickle_L-ALST_80K_754464_3D-model.pdf`, U3D): measure the swivel radius, plate thickness and kingpin head from it. **Rating, documented fix:** cap the top SLS band at 4 km/h = **1.1 m/s**, where the published 200 kg applies (116 kg needed with S = 3), until Blickle states the 5.4 km/h value in writing. |
| G-06 | E02 E-stop actuator | S | Siemens 3SU1050-1HB20-0AA0 data only from a distributor; B10d for the PL calculation not in hand. The contact blocks are documented. | Download the Siemens datasheet and the SISTEMA library (B10d) in a browser (SiePortal blocks scripts). The P/N is fixed now: 3SU1050-1HB20-0AA0 + holder 3SU1500-0AA10-0AA0 + 2 × 3SU1400-1AA10-1CA0. ES3 enclosure 3SU1801-0AA00-0AB1 is grey: use a yellow enclosure or label (ISO 13850). |
| G-07 | E41 SB1 reset, SK1 key selector | S | Eaton M22-DL-B / M22-K10 / M22-WRS3 data only from a distributor (datasheet.eaton.com returns an empty page to scripts) | Download the Eaton PDFs in a browser. Loads are PNOZ inputs (5 mA), so the contact ratings have a large margin. |
| G-08 | SE1 enabling pendant + E41 M12 socket | S | no P/N; IEC 60947-5-8 and B10d not documented; BOM €250 is about 2× low | Choose one of the candidates found (Euchner ZSM2100-106103 or IDEC/Turck ED1G-L20MB-1N; €460–520 net) with its matching cordset and panel socket. Save the manufacturer datasheet (IEC 60947-5-8, B10d). |
| G-09 | SP1/SP2 Pilz PSEN cs3.1 | S | PL, PFHd and ISO 14119 type only from a distributor; coding level documented as **"Low"** | Download the Pilz PSEN cs3.1 operating manual (pilz.com download area). Add the "Low" coding level to the defeat assessment (ISO 14119 §7) in `ce/RISK_ASSESSMENT.md`. OA variant only. |
| G-10 | E40, E42 fans | S | no P/N; airflow, power and IP unverified. The fans are required: S24 (DDR-240 max 50 °C) and see F3 | Fix the exact ebm-papst P/Ns (60 × 60 × 25 24 V with IP54 option; 40 × 40 × 20 24 V) and save the datasheets. The thermal model must use the datasheet airflow at the filter pressure drop. TP-11 heat-run. |
| G-11 | K3 (C48) | S | 58.4 V / 10 Ω = 5.8 A exceeds the Finder 22.32 documented 5 A at 110 V. No rating at 58 V. | Use **12 Ω** (4.9 A ≤ 5 A documented), or switch K3 to a Siemens 3RT2026 (35 A DC-1 at 60 V, documented) |
| G-13 | E18, E31, E33, E2F, E57, E56 (10 × 38 fuses) | S | "gG"/"class" links have no documented DC rating; ≥ 20 kA DC was ASSUMED (V:D6) | **Closed in substance:** Mersen **HP10M** gPV, "1000 VDC", "Breaking Capacity: 50 kA", IEC 60269-6, in holder **CUS101HEL** (10 × 38 DC 1000 V 32 A). Ratings 1/2/6/10/12/15/20/25/30 A exist: F8L/R → HP10M20, FAL/FAR → HP10M25, WF1/2/3 → HP10M6/12/2. **FJ 8 A and FCF 16 A do not exist:** use HP10M10 / HP10M15 after a coordination check. Save the Mersen HP10M PDF (official; this audit only reached the distributor). |
| G-14 | H01..H10 harness, CALC "arm feed 4 mm²" | S | IEC 60204-1 Table 6 ampacities (B2/E columns) are "recalled" in the netlist; no free document reproduces them | Partly closed: the Lapp T12 table (`docs/fonti/Lapp_T12_…pdf`) documents the 40 °C derating 0.87 (70 °C conductor) and 0.91 (90 °C). **Fix:** buy EN 60204-1:2018 (needed for CE anyway) and replace the table, or size each cable from the chosen cable maker's own ampacity table. Re-run `check_amr.py`. |
| G-15 | CALC "gripper beyond payload 50 mm" | S | ESTIMATE | Take it from the OpenArm gripper CAD (open source) and re-run the arm-field radius (762.5 mm). |
| G-16 | CALC "bus minimum under peak 44 V" | F | ASSUMED | Replace with the documented BMS cut-off 40.0 V (805-0027 Table 3-1), as the netlist already does; peak currents +10 %. |
| G-17 | CALC OpenArm 70/360/720 W | F | from the internal `ARCHITECTURE.md` only | Size from the Damiao motor datasheets (rated / peak current × 24 V) per joint, or measure on the bench and record it as a test result (OA variant only). |
| G-18 | CALC coffee module 300 W | F | coffee machine not chosen (CE gap G5) | Use the datasheet of the chosen 24 V machine. |
| G-19 | CALC deck strip width 100 mm | S | ESTIMATE, and the PASS depends on it: with the lower bound b = 62 mm (bolt pitch) the deflection becomes 0.71 mm > 0.55 mm | Plate FE model of the 15 mm deck, or add the transverse rib that CALC §9 already proposes. |
| G-20 | CALC M6 8.8 preload 7000 N; As 20.1 mm², Rp0.2 640 MPa | F | ISO 898-1 / VDI 2230 values not found in a free document in this audit | Use the fastener supplier's preload/torque table (Würth/Bossard catalogue PDF) at order, or a torque-tension test. Standard values; margin is large (630 N vs 4.7 kN). |
| G-21 | E32 T24 terminals, E35 RSIG resistor, RB1-7 bleed resistors, E25 NET1 supply | F | PTPOWER 16 rating not retrieved; generic resistors; FL SWITCH 1008N supply/power not retrieved | E32 → Weidmüller **WPD 100 2X25/6X10** (101 A) or attach the Phoenix PDF. Resistors: fix metal-film P/Ns with a datasheet (2 W / 1 W at 55 °C). NET1: P/N 1085256, attach the Phoenix datasheet. |
| G-22 | E59 JR1 | F | Phoenix PLC-RSC-5DC/21 input 38 mA at 5 V; a Jetson GPIO cannot drive that | Use PLC-RSC-24DC/21 (9 mA documented) switched by an opto or transistor stage from the GPIO. Document the stage in the netlist. |
| G-23 | D0 coil suppression | S | No documented diode terminal ≥ 0.54 A for the SW80 coil (Phoenix UKK 5-DIO is 0.5 A). The K1/K2 suppressor P/N was missing. | K1/K2: **Siemens 3RT2926-1BB00** varistor (fast drop-out; keeps the SS1-t reaction time). SW80: a ≥ 3 A diode (1N5408 datasheet, 3 A / 1000 V) on a component terminal with a documented current. Albright: drop-out "50ms" with diode suppression. |
| G-24 | X05 dock controller + DC contactor | S | "Albright SW60 class", no P/N | Use **Albright SW80B** (already documented: 600 A at 96 V) as the dock contactor, opened by the DUB01 OV relay. Name the controller P/N (EN 62368-1 check, CE G11). |
| G-25 | E12 K0P / K3 resistor Arcol HS50 | F | pulse/short-time overload rating not documented (netlist R_pulse_J_max 50 ASSUMED; precharge 3.4 J) | Download the Arcol HS datasheet in a browser (site down in this audit), or use a resistor whose datasheet states pulse energy. |
| G-26 | E51 Jetson carrier | F | module power documented (NVIDIA: 10/15/25/40 W); carrier not chosen. Its power-input connector (8 A ASSUMED) and EMC/RED DoC are open. | Choose the carrier (superstructure, CE G6) and save its datasheet + DoC. |
| G-27 | TP-05 test pieces | S | ISO 3691-4 test-piece sizes (Ø200 × 600 lying, Ø70 × 400 standing) are "commonly quoted" only; no free document found | Buy EN ISO 3691-4:2023 (required for the CE file anyway). SICK OI p.49: "The diameter must match the configured resolution". |
| G-28 | C01, E2C/D, E02, E21, S01, SWD | evidence | Certificates referenced in the BOM "ce_document" column are not in `docs/fonti`: SICK TÜV type-examination, Pilz TÜV, ez-Wheel/INERIS DoC, Discover UN 38.3 test summary | Download each certificate and DoC for the technical file (no technical value changes). |

**After these fixes the remaining open items are only quotes (§4) and type tests (TP-01…TP-23).** G-28 is evidence for the
technical file and is not counted in the 30 BOM GAP rows.


## 4. Price status

Basis: `bom_amr.csv` @1, rows with in_total = Y, scope **AMR incl. dock** (SUBTOTAL_base + SUBTOTAL_dock = €23,275).

| Scope (@1) | Value | Public price, BOM tags (SOURCED/SECONDARY) | Public after this audit | Quote needed after this audit |
|---|---|---|---|---|
| Purchased parts (buy rows) | €19,762 | €12,924 (65.4 %) | €15,173 (**76.8 %**) | €4,589 (23.2 %) |
| Make parts (laser/CNC/weld, harness, dock frame) | €3,513 | €0 | €0 | €3,513 (ESTIMATE, by nature) |
| **AMR incl. dock, total** | **€23,275** | €12,924 (**55.5 %**) | €15,173 (**65.2 %**) | €8,102 (**34.8 %**) |

Rows whose price was found public in this audit are marked in §1. The BOM still carries its ESTIMATE value for them, and several
differ:
- PEAK IPEH-004010: €294 net (price list) vs €520 ESTIMATE;
- Siemens 3RT2026-1BB40: RS €202.10 (TME USD 96.45) vs €90 ESTIMATE, ×2;
- enabling pendant: €460–520 net vs €250;
- DDR-240C-24: RS €134.08 (TME USD 103.60) vs €79 SECONDARY;
- DUB01CD48500V: RS €144.90 vs €163 SECONDARY;
- terminal sets 751008 + 2 × 751004 = €86.7 net vs €90.

The net effect on the @1 total is small: about +€300 to +€500.

Largest QUOTE-needed items (@1):
- Discover DLP-GC2-48V ×2: €1,860. The only figure is USD 1,009 from `CONTEXT.md`; no public listing was reachable.
- Fixed ESTIMATEs for purchased commodity parts.
- Albright SW80B (€130) and ED250B-L (€150).
- LYNK II (€350).
- RoboPad RPCOL90-100 + RPBAS90-100 (€700).
- Blickle and HIWIN (€460).
- Patlite tower (€120).

Variants (not in the AMR total, @1):

| Variant | Public (BOM) | Public after this audit |
|---|---|---|
| arm_OA €1,041 | €569 | €611 |
| barista €226 | €165 | €186 |
| arm_C48 €367 | €322 | €322 |
| superstructure Jetson €900 | 0 | 0 (quote) |


## 5. Design findings from the source review (documented values the design does not yet respect)

These matter more than the GAP list: the documents exist, but the design numbers do not follow them yet.

| # | Finding | Source (verbatim) | Consequence / fix |
|---|---|---|---|
| F1 | **Protective fields omit the ground-clearance supplement Z_F.** CALC §7: S = v·t + braking + 65 mm (+ Z_R); no Z_F. Ground clearance is 32 mm (`amr_params.GROUND`). | SICK nanoScan3 I/O OI 8024596 §5.3.10.2 p.37–38: "The lump supplement for ground clearance under 120 mm is 150 mm." Fig. 24: B_F ≤ 50 mm → Z_F = 150 mm. §5.3.10.4: "SL = SA + TZ + ZR + ZF + ZB"; §5.3.10.5: "SB = FB + 2 × (TZ + ZR + ZF)". Saved: `docs/fonti/SICK_nanoScan3_IO_OI_8024596_mobile_field_ZF_K_pages_1-29-31-37-39.pdf` | Field lengths from the scanner become about 401 / 685 / 1044 / 1390 mm (+150), and lateral fields +150 mm per side. The fields still fit in 3.0 m. The field edges move outward, so the §7b accel/decel limits fall (rough scaling: 1.5 m/s band ≈ 0.74 m/s² accel, 0.3 m/s band ≈ 1.3 m/s²). **Re-run CALC §7/§7b**, then update the field table, README, the manual and TP-05/05b. |
| F2 | **Arm field (base standstill) omits T_Z, and the resolution is not fixed.** CALC: S = K·T + C. | SICK OI p.30: "S = 1,600 mm/s × T + TZ + ZR + CRO". p.31: below 300 mm "you must use a resolution finer than 70 mm … dr = HD / 15 +50 mm" | S + 65 mm → R ≈ 2472 mm, farthest point ≈ 2.5 m (< 3 m, PASS). HD 184.5 → dr = 62 mm: configure **50 mm** resolution in the arm-work field set (FS2 OSSD2). Mobile fields: 70 mm is allowed (OI p.36: "In a mobile application, a resolution of 70 mm (leg detection) is sufficient"). |
| F3 | **ez-Wheel SWD is rated 0…+40 °C; the side bays are computed at 44–46 °C** (`CHECKS_AMR.md` Thermal, at 40 °C room) and the SWD housing sits in those bays | SWD datasheet 07/2024 and manual p.15: "Temperatures 0 to +40 °C". RoboPad: "Ambient Temperature 0 to 40°C" | Either rate the robot for ≤ 35 °C room ambient (bays ≈ 39–41 °C, verify), or separate the SWD housing from the bay air (baffle/duct to the intake). Verify the SWD housing air ≤ 40 °C in TP-11. Put the room limit in the manual. |
| F4 | **SWD mass** 6.0 kg ESTIMATE in CAD/CALC | SWD manual p.28: 1-stage with brake "196 … 7" (L 196 mm, 7 kg) | +2 kg in the base mass and CoG; re-check the SWD envelope against L 196 mm |
| F5 | **maxon DSR 50/5 at 27 V sinks ≤ 5 A** (~133 W per unit, 300 W only on the 56 V setting). Over-temperature cut-out drops the clamp. No CE statement. | maxon operating instructions 2015-04: "Max. current 5 A"; "Once the over-temperature deactivation is enabled the supply voltage cannot be limited anymore." | 2 units ≈ 265 W ≥ 208 W peak: still PASS, but VERIFICATION MX1 (300 W) should be corrected. Continuous rating derates to ~6 W at 45 °C (calc 2.8 W average: OK). If a clamp trips on temperature, T24 is unclamped: the DDR OVP (28.8–35 V) and the SWD OV alert (32 V) are the backstop. Show this in TP-03/TP-14 worst-case regen. Netlist "CE [ASSUMED]" → no CE claim. |
| F6 | **Kassow Edge power** (C48) | Kassow Edge brochure p.4 (saved) | see §2 rows 61–63; peak up to 1200 W vs 1000 W assumed; "Max external fuse (A) 25" |
| F7 | **Netlist value corrections** | Finder S38EN; Finder S22EN; Weidmüller WPD 100; Siemens 3RT2026 p.6; eibabo FL SWITCH | KS coil 9 → **10.4 mA**. K4/K0P coil 83 mA (table) / 92 mA (2.2 W): still > 75 mA, so KI4 stays. 0 V block 125 → **101 A** (≥ F0 100 A: still OK). K1/K2 B10D = 1E6 / 0.73 = **1.37E6** (documented; netlist "Annex C ASSUMED" 1.3E6). FL SWITCH P/N 1085256. |
| F8 | **PSEN cs3.1 coding level "Low"** (ISO 14119) | eibabo copy of the Pilz data | add to the defeat-incentive assessment (OA variant) |
| F9 | **Stale text** | – | `README.md` "Every purchased-part technical value is SOURCED" (not true: §1). `CALC.md` §1 intro "10 mm 6082 deck" (CAD 15 mm) and input row "Rp0.2 6082-T6 plate 10 mm" (15 mm plate: 240 MPa is the correct value, Aalco/EN 485-2). `ELECTRICAL.md` §3/§6/§8 still carry rev B1 "ASSUMED / ask" lines that B2 closed (F0 DC rating, PL e with one SC output, DDR lying derating, Configurator price). `CASTOR_SUSPENSION.md` §9 still lists open supplier items. `bom_amr.csv` rows E20/E22/E28 cite the B0 page as their price URL. |
| F10 | **Datasheet inconsistencies to note** | SWD datasheet "Nominal performance 7,9 daN at 9 km/h" vs manual p.13 "7.9 Nm at 380 rpm"; Discover peak 90 A "10 seconds" (manual) vs "3 sec" (web page); SICK OI p.52 "at least 200 mm" vs p.40 "maximum height of 200 mm"; maxon weight 60 g (manual) vs 75 g (page) | Use the manual values and the conservative reading: 3 s peak, ≤ 200 mm. |

## 6. Evidence added to `../docs/fonti/` in this audit (each checked with pdftotext for the quoted text, except the scanned maxon manual)

| File | Size | Supports |
|---|---|---|
| `SICK_nanoScan3_IO_OI_8024596_mobile_field_ZF_K_pages_1-29-31-37-39.pdf` | 0.24 MB | F1, F2, K = 1600 mm/s |
| `SICK_nanoScan3_IO_OI_8024596_pages_1-30-36-37_K1600_mobile.pdf` | 0.16 MB | K, 70 mm mobile resolution |
| `HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p87_MGN_bolt_torque.pdf` | 0.04 MB | MGN15 rail bolt torque 98 N·cm in aluminium (quoted in CASTOR_SUSPENSION but missing from the earlier extract) |
| `Blickle_L-ALST_80K_754464_3D-model.pdf` | 0.88 MB | official 3D model (U3D), public; G-04 |
| `Finder_80-01_datasheet_S80EN_p3_p8.pdf`, `Finder_38-51_datasheet_S38EN_p5_p13.pdf`, `Finder_22-32_datasheet_S22EN_p7_p11.pdf` | 0.29 MB | K0T, KS, K0P/K4/K3 |
| `PEAK_PCAN-Ethernet_Gateway_DR_UserMan_2.1.0_p1-6-64-66.pdf`, `PEAK_Pricelist_valid_2026-08-21.pdf` | 1.39 MB | CAN1 data, price €294 |
| `maxon_DSR50-5_309687_Operating_Instructions_2015-04.pdf` | 0.94 MB | DSR 50/5 (F5) |
| `Lapp_T12_Strombelastbarkeit_technical_table.pdf` | 0.27 MB | derating factors (G-14, partial) |
| `SSAB_Domex_355MC_datasheet_2276_2022-02-07.pdf` | 0.10 MB | ReH 355 MPa |
| `Patlite_WME-DFB_signal_tower_spec_WME-D-W18.pdf` | 0.86 MB | HL1 (Patlite WME-302DFB-RYG) |
| `Kassow_EdgeEdition_brochure_p1_p4_power.pdf` | 1.39 MB | C48 arm power |

Web-only evidence (not saveable):
- Aalco 6082-T6/T651 plate data (EN 485-2: 255 MPa for 6–12.5 mm, 240 MPa above 12.5 mm, E 70 GPa);
- NVIDIA Jetson Orin page;
- icotek KEL-DPZ page;
- eibabo.de distributor pages (dated 2026-10-05).

