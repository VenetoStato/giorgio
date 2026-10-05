# Manual downloads and purchases still needed (rev B4, 2026-10-05)

Everything else in `CERTAINTY.md` was fetched by script from the manufacturers' own sites (`../docs/fonti/`). The items below are
blocked for scripts (Cloudflare challenge), not published, or are paid standards. Save each file to `../docs/fonti/` and update the
CERTAINTY row named.

| # | Part / document | Exact URL (open in a browser) | Value needed | Closes |
|---|---|---|---|---|
| 1 | Pilz PNOZ m B0 (772100): EC type-examination certificate + EU declaration of conformity | https://www.pilz.com/en-INT/eshop/p/772100 → Downloads → Certificates (general area https://www.pilz.com/en-INT/support/downloads) | certificate number, notified body, PL e / SIL CL 3 classification, validity; DoC directives and standards | G-28 (evidence, BOM row 54) |
| 2 | Pilz PSEN cs3.1 M12/8-0.15m (541009) operating manual | https://www.pilz.com/en-INT/eshop/Sensor-technology/Safety-switches/PSENcode-non-contact-coded-safety-switches/PSENcode-compact-design/PSEN-cs3-1-M12-8-0-15m-PSEN-cs3-1-1Unit/p/541009 → Downloads | manual statement of the ISO 14119 type (type 4 inferred from "transponder"), Sao/Sar, PFHd/series-connection rules | evidence upgrade of BOM row 81 (already DOCUMENTED by the TÜV certificate) |
| 3 | Discover DLP-GC2-48V (900-0054) UN 38.3 test summary | https://discoverbattery.com/resource-library (not listed); otherwise request from Discover technical support | test summary ID, lab, date, T1–T8 results for the 48 V pack | G-28 (evidence, BOM row 10) |
| 4 | Pack-pair prospective short-circuit current | not published (Discover 805-0027 has no Isc or internal resistance): ask Discover technical support in writing, **or** measure in TP-14 | Isc of 2 × DLP-GC2-48V in parallel at the B48 fuse comb | G-29 (11 OPEN rows in `electrical/CHECKS_AMR.md`); acceptance ≤ 10 kA (Mersen HP10M IEC 60269-6 breaking capacity) |
| 5 | EN 60204-1:2018 (Table 6) or DIN VDE 0298-4:2013 (Table 11, column C) - **purchase** | https://www.beuth.de (DIN VDE 0298-4) / https://webstore.iec.ch (IEC 60204-1) / UNI-CEI store | ampacity of flexible PVC/90 °C conductors 16–35 mm² (and the 90 °C column used in `netlist_amr.yaml`) | G-14 (BOM row 68 H01..H10) |
| 6 | EN ISO 3691-4:2023 - **purchase** | https://www.iso.org/standard/83545.html (or UNI store) | test-piece sizes for the personnel-detection tests (TP-05) | G-27 |
| 7 | Mersen HP10M I²t / pre-arcing values (optional) | not published (product finder shows "-"); ask Mersen technical support | numeric I²t for selectivity F2/WF2 (curve 720877 already saved) | evidence upgrade (G-13 already closed) |
| 8 | Siemens 3SU1 system manual or certificate citing IEC 60947-5-5 (optional) | https://support.industry.siemens.com/cs/ww/en/ps/3SU1050-1HB20-0AA0 | IEC 60947-5-5 conformity statement (the datasheet cites EN ISO 13850 only) | evidence upgrade of BOM row 14 |

Not downloads (design/measurement items, listed for completeness): G-15 gripper length beyond the payload point (measure or OpenArm
gripper CAD), G-18 coffee machine power (machine not chosen), price quotes (`CERTAINTY.md` §4) and type tests TP-01…TP-23.
