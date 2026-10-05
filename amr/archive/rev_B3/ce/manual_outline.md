# Instructions for use - outline (MR Annex III 1.7.4, 3.6.3; EN ISO 3691-4 cl. 6; EN ISO 10218-2 info for use)

Language: Italian + language of each destination country (MR Art. 10(7)). Digital allowed (QR on robot, printable,
online >= 10 y, paper free on request within 1 month). **Safety information always on paper** if the robot can be used
by non-professional users (Art. 10(7)) - barista variant: assume yes.

1. **Identification** - manufacturer name/address/contact (1.7.4.2(a)), designation as on nameplate (b), DoC or URL/QR (c).
2. **Description and intended use** (d)(g) - variants C48 (certified arms) / OA (OpenArm R&D), autonomous mode, modes, payloads (2x3 kg + 2.1 kg tray),
   max speeds per mode, environment limits (indoor, slope, floor, temperature, IP), **forbidden uses** (h): outdoor, wet
   floor, climbing/sitting, direct hand-over from grippers, carrying people, towing, ATEX, unsupervised public use.
   ML/AI statement: what is autonomous, what is not safety-relevant; AI disclosure (AI Act Art. 50).
3. **Transport, handling, storage** (p)(o) - mass (total, base, removable parts, battery 14 kg each), lifting points,
   transport locks for arms, storage SoC and temperature for batteries, UN 38.3 shipping note.
4. **Site preparation and installation** (i)(o) - ISO 3691-4 cl. 6 site requirements: operating zones, aisle widths
   and clearances (>= 0.5 m, to fix), hazard zones and restricted zones, marking of floors, barriers at stairs/edges,
   no overhangs, lighting/glass surfaces, dock placement + 230 V supply with RCD, Wi-Fi coverage, map creation.
5. **Commissioning** (k) - field-set validation with test pieces (procedure + checklist), speed limits per zone,
   safety-parameter lock, acceptance record. Who may do it (trained person).
6. **Operation** (k)(f) - roles (supervisor per MR 3.2.4, operator, maintainer), start/stop/reset, modes and key
   selector, HMI and light/sound signals meaning, supervisory function (what it can command), docking/charging,
   barista operation, what to do when blocked.
   **Operating rules (rev B3, enforced partly by design, stated as instructions):**
   - acceleration / braking limits per speed band (scan plane ≤ 200 mm at the protective-field edge, SICK OI 8024596 p.40;
     `../CALC.md` §7b): 0.3 m/s band 1.5 / 1.08 m/s², 0.8 m/s 1.22 / 1.00, 1.2 m/s 1.00 / 0.92, 1.5 m/s 0.81 / 0.86 m/s²
     (accel / decel), configured in the motion profile; do not raise them;
   - floor: sharp thresholds ≤ 10 mm at any speed; thresholds 10-20 mm only bevelled ≤ 1:2 and crossed at ≤ 0.3 m/s;
     nothing higher (D80 castors; site survey before commissioning, slow zones in the map);
   - castor preload: set per corner on a scale (76 N, ±7 N) after any castor/spring service; check the scan plane with the
     test object at every field edge (184.5 ± 5 mm) after any scanner or castor work;
   - reverse travel is limited to <= 0.3 m/s by a permanent safe limit (SLSa) in the drives (SF5); no fast reversing;
   - never drive with the arms extended to the side or rear: arms in front of the body for work, parked for travel;
   - rotate on the spot only with the arms parked (SF4/SF8);
   - objects and drinks travel in the tray, never in the hands (SF8; hand-over only via the tray with OpenArm).
   - Q0 (ED250B-L key disconnect) is an emergency / no-load isolator: switch it only with K0 open (robot in SERVICE or off);
   - the batteries stop the robot at 48 V (application cut-off K0V); dock before that; never let the packs reach the 40 V BMS
     lock-out (manual ON needed); packs within 50 mV at >= 95 % SoC before connecting them in parallel (service);
   - dock charger NPB-750-48: DIP 2 OFF / 3 ON ("flooded", 56.8 / 53.6 V); never the 58.4 V LiFePO4 preset;
   - fans are required (S24 converter max 50 C): replace filters at the interval, an over-temperature alarm parks the robot.
7. **Safety** (l)(m) - safety functions summary: SF1-SF16 (as in `../electrical/SAFETY_FUNCTIONS.md` rev B2, Pilz
   PNOZmulti 2) + SF17 supervisory watchdog, stopping distances table per speed, daily checks
   (E-stop test, field test, warning devices, scanner windows clean), **residual risks** (RISK_ASSESSMENT.md §4),
   PPE for maintainers, laser class 1 statement, RF/implant information (w), noise values (u).
8. **Maintenance and cleaning** (r)(s)(t) - LOTO via key service disconnect, wait time for capacitors, intervals
   (brakes, castors, scanner windows, fan filters, coffee descaling), food-contact cleaning (2.1),
   spare parts affecting safety (scanners, E-stops, brakes, batteries: originals only), safety-function proof tests,
   SW updates (signed, versions log; 1.1.9).
9. **Faults and emergencies** (q)(v) - error codes, releasing a trapped person (manual brake release procedure for
   ez-Wheel; push robot), battery fire (extinguisher type, evacuation), arm stuck.
10. **Decommissioning/disposal** - battery removal, Battery Reg. take-back, WEEE.
11. **Technical data** - nominal power kW, mass, dimensions, swept radius when rotating in place (~440 mm with arms parked), speeds (forward 1.2 m/s max, reverse 0.3 m/s max),
    battery, charging, radio bands/power, noise, IP, vibration N/A.
12. **Annexes** - DoC copy, wiring overview, field-set drawings, cybersecurity guidance (EN 18031: passwords, network
    setup, update policy, support period, vulnerability contact for CRA).

## Marking / labels
**Nameplate (base, visible, indelible)** - MR Art. 10(5)(6), Annex III 1.7.3, 3.6.2:
- CE marking (Art. 24; >= 5 mm)
- Manufacturer name, registered trade name/mark, postal address, website/e-mail
- Designation: "Giorgio - autonomous mobile service robot", model/type, serial number, year of construction
- Nominal power (kW) [3.6.2(1)(a)], mass of the most usual configuration (kg) [3.6.2(1)(b)]
- Nominal voltage 48 V DC (51.2 V nom., 40-58.4 V), battery type LFP 2 x 1.54 kWh
- Max payload (2 x 3 kg + 2.1 kg tray), IP rating
- QR code / URL to digital instructions and DoC (Art. 10(7)(a), 10(8))
**Other labels**: battery labels per Reg. 2023/1542 Art. 13 (from Discover) + crossed-out bin; WEEE bin symbol;
ISO 7010 pictograms: W019 crushing (rotation in place / dock), W017 hot surface (coffee), W012 electricity (battery bay), M002 read
manual, P "do not climb/sit"; "Laser class 1" (if supplier requires); E-stop yellow background; key disconnect
label; mass on removable heavy parts (battery packs 14 kg) per 1.7.3; dock: own nameplate + CE + 230 V data.
