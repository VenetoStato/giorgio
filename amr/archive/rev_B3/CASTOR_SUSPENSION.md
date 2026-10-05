# Castor suspension: sprung D80 castor with the tower roof kept at z 134 (scan plane stays at 184.5 mm)

Status: design proposal, 2026-10-05. It closes VERIFICATION CA1 and replaces design change 8. The change from the
+30–40 mm tower is in the "Result" section below. Frame: base frame, origin on the floor, x forward, y left, z up, mm.
Geometry is given for the **front-left (FL) corner**. The other corners are mirror images in local coordinates (see §6).
**Implemented in CAD rev B3** (`CAD_REV_B3.md`, 0 interferences, 0 keep-out violations, travel check 0). Deviations found while
implementing: (a) post A04 at (±360, **±106**) instead of ±110 (the RL post hit the rear exhaust fan), and **no post at RR**: a post
there hits the RoboPad collector E01 (y −182…−92), so bracket A07 (spine extension x −340…−262) carries the RR deck corner and roof;
(b) the cover bottom-edge trim at the chamfers is **8 mm** (z 62…70, ~50 mm long), not 2 mm, for the full 5 mm margin of the swept
envelope; (c) the castor-to-scanner geometry is unchanged (scanner centres stay at (±290, ±208)).

## Result
1. **Scan-plane limit (sourced, SICK):** the plane must be **≤ 200 mm everywhere** in the protective field. 150 mm is
   SICK's recommended height. 184.5 mm is allowed, so the old +30–40 mm tower option (plane 215–225 mm) is **not
   allowed**. Body pitch already uses most of the 15.5 mm margin (§1.3).
2. **The roof stays at 128…134, and the scan plane stays at 184.5.** The springs and the guide are taken out from under the
   roof and moved into the 41 mm gap between the spine and the battery (|y| 90…131), next to each castor:
   - castor: Blickle **L-ALST 80K** (D80 Softhane, 200 kg, H 102);
   - guide: 1 vertical **HIWIN MGN15** rail with 2 × **MGN15H** blocks, screwed to the spine;
   - springs: 2 × **Gutekunst D-313J-02** (14.172 N/mm each, 28.34 N/mm per castor);
   - bump stop: a PU pad that hits the roof underside after **17 mm** of travel. The droop stop is a rubber buffer.
   - At the castor, the stack above the castor plate is only a 6 mm carriage plate plus the 3 mm pad: 102 + 6 + 3 + 17 = 128.
3. **New blocker found and solved: in plan view, no swivel castor ever fitted at (±280, ±198).**
   - Checked with the CAD (rev B2 STEP, swept swivel envelope plus 5 mm): at that position the swivel circle of any castor
     with D ≥ 75 and ≥ 90 kg hits the pan, the spine end, post A04, the front/rear cover chamfer and the K05 edge.
   - This was true for the D100 baseline as well.
   - The castor axis must move to **(±275, ±180)**. Five other changes are needed (§5):
     - notch the spine ends;
     - cut the pan corner;
     - move post A04;
     - move the gap DSR clamps E5B/E16;
     - move the RR converter E34.
4. **Load split (CALC §3) with k = 28.34 N/mm and F_inst = 76 N:**
   - each drive wheel carries **40.2 %** of the empty robot's weight, and still **35.6 %** with a 5 mm bump under one castor (target ≥ 35 %);
   - k is inside the rev-B limit (≤ 29.5 N/mm);
   - the spring force at the bump stop is 558 N, after which the hard stop carries the load.
5. **Threshold capability gets worse with D80.** A 20 mm step is 25 % of the wheel diameter. Cross 20 mm thresholds at
   ≤ 0.3 m/s, or change the README limit to ≤ 10 mm at speed (§4).

## 1. Scan-plane height limit

### 1.1 Primary source: SICK nanoScan3 I/O operating instructions 8024596/1W27/2026-05-26
Extract saved as `docs/fonti/SICK_nanoScan3_IO_OI_8024596_scan_plane_pages_1-31-40-52-137.pdf`. Full manual:
https://www.sick.com/media/docs/7/37/137/operating_instructions_nanoscan3_i_o_en_im0087137.pdf

- §5.3.10.6 "Height of the scan plane" (mobile hazardous-area protection), PDF p.40:
  > "The scan plane must be at a maximum height of 200 mm everywhere. Otherwise, persons lying horizontally may not be
  > detected. In many cases, a mounting height of 150 mm above the floor (height of the scan plane) is suitable."
- Thorough check, mobile, PDF p.52:
  > "Check the height of the scan plane. The scan plane must be at a height of at least 200 mm so that people lying down
  > can be reliably detected. For this purpose, position the supplied test object at a number of points at the edges of
  > the largest protective field."

  "At least" contradicts p.40. Read it as "at most", which is what p.40 and the physics say. Ask SICK to correct it.
  The procedure is what matters: **test object at the edges of the largest field**.
- Table 41 "Scan plane", PDF p.137:
  > "Conical error ≤ ± 75 mm at a distance of 3 m … Tilt error ≤ 2° / ≤ ± 105 mm at a distance of 3 m … Deviation from
  > the ideal scan plane taking into account the conical error and the tilt error ≤ ± 180 mm at a distance of 3 m"

  Scaled to our longest field (1144 mm at 1.5 m/s), the device tolerance alone is up to ±69 mm. That is why the
  edge-of-field test-object check is required.
- §5.3.7.4, stationary only, PDF p.31, for information:
  > "If you mount the safety laser scanner at a height of at least 300 mm … the leg is detected at a resolution of 70 mm …
  > dr = HD / 15 + 50 mm"

  At HD 184.5 this gives dr = 62 mm. That is the stationary ISO 13855 rule. For the AGV the 70 mm leg test piece of
  ISO 3691-4 applies (below).

### 1.2 ISO 3691-4 test pieces (not re-verified)
EN ISO 3691-4 is paywalled, and no free primary text could be reached in this session. The test pieces as commonly quoted,
and as already used in `ce/TEST_PLAN.md` TP-05 ("verify dims in standard"), are:
- lying: Ø 200 mm × 600 mm;
- standing (leg): Ø 70 mm × 400 mm.

What follows:
- **Lying piece:** the plane has to cut the Ø 200 lying cylinder, so it must stay below 200 mm minus every tolerance at
  every point of the field. This matches SICK's "≤ 200 mm everywhere".
- **Leg piece:** any plane between the floor and 400 mm crosses it. Configure a resolution of ≤ 70 mm (the nanoScan3
  offers 20 … 70 mm).

**Limit for the design:** nominal plane ≤ 200 mm minus (pitch rise at the field edge + mounting tilt). The tolerance is
then checked with the test piece at the field edges (TP-05).

### 1.3 Margin left at 184.5 mm: action for CALC and safety
- The margin is 15.5 mm.
- CALC §3 already shows up to 1.53° nose-up pitch (rear arm pose, 1.5 m/s² accel). At the edge of the 1144 mm field this
  is 1144 · tan 1.53° = **+31 mm**, so the plane is at 215 mm. That breaks the 200 mm rule while accelerating in the
  1.2/1.5 m/s bands. The softer spring here (28.3 instead of 31 N/mm) makes it about 9 % worse.
- Options for the CALC/safety stream:
  - limit the acceleration in the two top SLS bands so that pitch × field length ≤ ~10 mm (≈ 0.5° at 1144 mm);
  - or switch to a nose-down field set while accelerating;
  - or accept a lower top speed.
- This is independent of the castor hardware, but it is the reason the scan plane must not go up by even a few mm.

## 2. Castor selection (documented candidates)
Method:
- 463 Blickle swivel castors with D 50–85 were scraped from blickle.com series pages.
- All Tente swivel castors of 75–80 mm were read from tente.com.
- The swivel radius r_s is the published value (Tente), or else hypot(F + D/2, w/2) (Blickle does not publish it; Tente's
  values show r_s ≈ F + D/2).

| Candidate | D × w | Load @ speed | H | Offset F | r_s | Verdict |
|---|---|---|---|---|---|---|
| **Blickle L-ALST 80K (ID 754464)** | 80 × 30 Softhane 75A, Al centre, ball bearing | 200 kg @ 4 km/h, static 500 | **102** | 38 | **79.4 (calc.)** | **chosen**: lowest H and smallest r_s with ≥ 90 kg and a PU tread |
| Blickle LK-ALST 82K (754775) | 80 × 40 | 230 kg | 110 | 40 | 82.5 | 8 mm taller, larger r_s |
| Blickle LH-ALST 82K (754582) | 80 × 40 | 230 kg | 120 | 45 | 86.3 | too tall |
| Blickle L-ALTH 80K (331116) | 80 × 30 Extrathane | 200 kg | 102 | 38 | 79.4 | equivalent (harder 92A tread), fallback |
| Tente 3470 UOH 080 P62 | 80, nylon/"Mix" | 200 kg @ 4 km/h | 108 | 40 | **80 (published)** | nylon tread (noise), taller |
| Blickle L-ALST 100K (579250) | 100 × 40 | 250 kg | 125 | 36 | 88.3 | does not fit in plan view (§5) and leaves 3 mm under the roof |
| Blickle LHF-ALST 100K-1 (755357) | 100 sprung | 320 kg | 175 | 32 | – | spring 88 N/mm, too stiff and too tall (CA1) |
| Tente 2470 PJO 075 P40 / Blickle LPA-PATH 75KF | 75 | **75 kg @ 3 km/h** | 100 | 24 / 29 | 61.5 / 67.7 | fits in plan view but **< 90 kg**: rejected |

Verbatim sources:
- Blickle L-ALST 80K, https://www.blickle.com/product/l-alst-80k-754464 (text saved:
  `docs/fonti/Blickle_L-ALST_80K_754464_product_page_2026-10-05.txt`):
  > "Wheel Ø (D) 80 mm … Wheel width 30 mm … Load capacity at 4 km/h 200 kg … Load capacity (static) 500 kg … Bearing
  > type ball bearing … Total height (H) 102 mm … Plate size 100 x 85 mm … Bolt hole spacing 80 x 60 mm … Bolt hole Ø
  > 9 mm … Offset (F) 38 mm … Unit weight 0.7 kg"; "Softhane®, hardness 75 Shore A … non-marking"; "double ball bearing in the swivel head".
- The ALST series table confirms it:
  > "L-ALST 80K 80 30 200 ball bearing 102 100 x 85 80 x 60 9 38"

  (`docs/fonti/Blickle_ALST_series_and_load_capacity_guide_2026-10-05.txt`).
- Tente 3470 UOH 080 P62, used as the swivel-radius reference (`docs/fonti/Tente_3470UOH080P62_TI_swivel_radius.pdf`,
  https://www.tente.com/en-de/swivel-castor-80-mm/3470uoh080p62):
  > "Offset 40 mm, Swivel radius 80 mm, Load capacity at 4 km/h 200 kg, Overall Height 108 mm"
- Tente 2470 PJO 075 P40 (https://www.tente.com/en-de/swivel-castor-75-mm/2470pjo075p40):
  > "Load capacity at 3 km/h 75 kg … Offset 24 mm Swivel radius 61.5 mm" (€15.00 net).
- Blickle LPA-PATH 75KF (https://www.blickle.com/product/lpa-path-75kf-757092):
  > "Load capacity at 3 km/h 75 kg … Total height (H) 100 mm … Offset (F) 29 mm"

**Price of L-ALST 80K:** not published (Blickle B2B login). Ask for a quote.

**Swivel radius 79.4 mm:** calculated, ESTIMATE until the Blickle CAD (login) is in. The keep-out below adds 5 mm.

## 3. Mechanism and stack-up

### 3.1 Why the spring cannot sit under the roof
- With the castor plate top at z 102 and the roof underside at z 128, there are **26 mm**.
- An in-line slide needs at least:
  - carriage plate 6 mm;
  - + spring at full bump L ≥ Ln;
  - + 17 mm travel.
- The shortest suitable spring (D-313J-02) has Ln = 30.78 mm, so the stack needs ≥ 54 mm. Gutekunst D-350 needs ≥ 54 mm
  too (Ln 30.93).
- Around the castor there is no room for a spring/guide column either: the r 84.4 swivel keep-out fills the whole corner
  between the cover, the chamfer, E13 and the battery.

The only free volume next to each castor is the spine/battery gap (|y| 90…131). That is where the column goes.

### 3.2 Load path
- **Body down to the castor:** body → spine (6 mm 6082) → B1 bracket → 2 springs → shelf → carriage weldment → castor plate → castor.
- **Guidance:** the carriage weldment is bolted to 2 × MGN15H blocks running on a rail screwed to the spine inner face.
  The rail takes every moment from the 157 mm offset between the castor axis and the spring centroid.
- **Bump stop (+17 mm):** the PU pad on top of the carriage plate hits the tower roof underside right above the castor
  axis, so the load path is straight. Up to 815 N at the tip limit (CALC §3).
- **Droop stop (−2.5 mm):** the shelf lands on a rubber buffer bolted to the spine.

### 3.3 Stack-up at the castor axis (z, nominal = robot standing on a flat floor, static)

```
z 134.0  roof top = scanner seat (unchanged)  -> scan plane 134 + 50.5 = 184.5 (unchanged)
z 128.0  roof underside (6 mm S355MC roof 128..134, unchanged)
         17.0 mm free = bump travel
z 111.0  PU bump pad top (pad 30 x 30 x 3, Shore 90A, bonded)
z 108.0  carriage plate top (6 mm S355MC, 102..108; M8 countersunk ISO 10642 into the castor plate holes)
z 102.0  castor top plate top (Blickle H = 102)
z   0    floor (wheel D80, axle at z 40, trail 38 mm)
At full bump: carriage plate 119..125, pad 125..128 = contact. At droop: carriage plate 99.5..105.5.
```

### 3.4 Stack-up of the spring column (in the spine/battery gap, nominal)

```
z 230.0  rail top (MGN15R, L 190, z 40..230)            [body]
z 205.8  upper block top (MGN15H 147.0..205.8)          [carriage]
z 139.2  B1 top (B1 = 8 mm S355 131.2..139.2, plus angle up the spine to z 170, vertical slots +-3 mm)  [body]
z 131.2  spring top seat = B1 underside (spigot Ø23 x 5)
         2 x D-313J-02, installed length 51.2 (L0 53.9, compressed 2.68 mm -> 2 x 38.0 N = 76.0 N)
z  80.0  spring bottom seat = shelf top (spigot Ø23 x 5)
z  72.0  shelf bottom (8 mm S355, 72..80)               [carriage]
z  82.0  lower block bottom (MGN15H 82.0..140.8; 2 mm above the shelf, which passes under it to the mast) [carriage]
z  69.5  droop stop top (rubber buffer on a spine angle) -> 2.5 mm droop
z  40.0  rail bottom                                     [body]
z  37.0  pan top
```

Travel check, carriage from −2.5 to +17:
- lower block 79.5…157.8 and upper block 144.5…222.8, both on the rail (40…230);
- spring length 53.7 (≈ free) … 34.2;
- the shelf never reaches B1 (shelf top 97 at bump, B1 at 131.2).

### 3.5 Spring, Gutekunst D-313J-02
- Product page: https://www.federnshop.com/en/products/compression_springs/d-313j-02.html
- Datasheet: `docs/fonti/Gutekunst_D-313J-02_compression_spring_datasheet.pdf`

> "d 3.6 mm … D 28 mm … De 31.6 mm … Dd 23.6 mm (maximum diameter of mandrel) … Dh 32.6 mm … L0 53.9 mm … Fn 327.711 N
> maximum force in static use … Ln 30.78 mm … sn 23.12 mm … Fndyn 300.878 N … Lndyn 32.67 mm … shdyn 18.18 mm … n 5.5 …
> R 14.172 N/mm … Fntol 25.38 N … L0tol 1.44 mm"

> "Scaled prices … 1 12.3700 EUR … 17 1.6600 EUR … 37 1.3900 EUR"

| Quantity per castor (2 springs in parallel) | Value | Limit / target |
|---|---|---|
| k | 2 × 14.172 = **28.34 N/mm** | CALC rev B ≤ 29.5 (35 % rule); the ≥ 47.5 pitch window is empty anyway |
| F_inst (nominal, set with the B1 slots) | **76.0 N** (2.68 mm). Set 74 N → 2.61 mm if CALC keeps 74 | CALC 74–78 N |
| F at the bump stop (+17 mm, L 34.2) | 2 × 278.9 = **558 N** | ≤ Fn 327.7 per spring (85 %), ≤ Fndyn 300.9 (93 %); L ≥ Ln 30.78 and ≥ Lndyn 32.67 |
| F at the droop stop (−2.5 mm) | ≈ 5 N (springs just seated) | > 0 |
| Spring guidance | Spigots Ø23 in both seats (≤ Dd 23.6). L0/D = 1.9, no buckling | – |
| Fatigue | Daily strokes are ±5 mm. A full 19.5 mm stroke (threshold) is > shdyn 18.18 but rare; order shot-peened springs if the TP shows frequent full strokes | – |
| Tolerance | L0 ±1.44 → ±41 N per pair. **Set each corner on a scale** (robot on 4 load cells or a castor scale) with the B1 slots (±3 mm = ±85 N) | ±7 N after setting |

### 3.6 Guide, HIWIN MGN15
- Rail MGN15R, L 190 (= 15 + 4 × 40 + 15), with 2 × MGN15H blocks.
- Catalogue G99TE24-2410, Table 2-4-19, PDF p.91, saved as `docs/fonti/HIWIN_Linear_Guideway_Catalog_G99TE24-2410_p1_p91_MGN.pdf`.
  Full catalogue: https://hiwin.com/wp-content/uploads/HIWIN-Linear-Guideway-Catalog.pdf

> "MGN 15H … H 16 … W 32 … B 25 … C 25 … L1 43.4 … L 58.8 … WR 15 … HR 10 … P 40 … E 15 … M3x10 … C(kN) 6.37 …
> C0 (kN) 9.11 … MR 73.50 … MP 57.82 … MY 57.82 (N-m) … Block 0.092 kg … Rail 1.06 kg/m"

Rail bolts:
> "MGN15 M3×0.5P×10L … Aluminum 98 (10)" N-cm

The rail goes into the 6 mm 6082 spine as tapped M3, engagement 6 mm.

Load case: castor force at the axis, spring centroid 157 mm away (Δx 140.5, Δy 70).

| Case | Castor force | Moment on the guide | Per block (c/c 65 mm) | Limit |
|---|---|---|---|---|
| Static nominal | 76 N | 12 N·m | 0.18 kN | C 6.37 kN |
| Bump stop reached | 558 N | 88 N·m | 1.35 kN | C0 9.11 kN (SF 6.7) |
| Horizontal castor load 300 N at the floor (threshold) | – | 27 N·m roll | – | 2 × MR 73.5 N·m |

- Seal friction is a few N (ESTIMATE). Plain bushings were rejected: with this offset, iglidur bushings (μ ≈ 0.1–0.15)
  would give ±60–90 N of stiction, which is as large as the 76 N preload.

### 3.7 Rolling, thresholds, speed (L-ALST 80K)
- Blickle (`docs/fonti/Blickle_ALST_series_and_load_capacity_guide_2026-10-05.txt`,
  https://www.blickle.com/guide/load-capacity):
  > "Wheels and castors with ball bearings are capable of exceeding speeds of 4 km/h with a reduced load capacity."
  > "motorized indoors < 5 % of wheel Ø 1.4–2.0 … motorized outdoors > 5 % of wheel Ø 2.0–3.0"

  Our 1.5 m/s is 5.4 km/h. Blickle gives no number for the reduced capacity at 5.4 km/h; ask them.
- **Rating check:**
  - worst commanded castor load 380 N = 38.7 kg; × S 3.0 (obstacle > 5 % of Ø) = 116 kg ≤ 200 kg ✓;
  - tip-limit load 815 N = 83 kg ≤ 500 kg static ✓;
  - the CA1 requirement "≥ 90 kg" is met with margin.
- **Thresholds:**
  - Horizontal force needed to start climbing a sharp step of height h: F/N = √(2Rh − h²)/(R − h).
  - D80, h 20: **1.73**; h 10: 0.88. For comparison, D100 at h 20: 1.33.
  - With the springs the castor rises up to 17 mm against 558 N, then the pad hits the roof and the corner lifts the last
    3 mm of a 20 mm step.
  - Recommendation: README "thresholds ≤ 20 mm" becomes **≤ 10 mm at any speed, 10–20 mm only at ≤ 0.3 m/s**. Validate in
    the prototype tests (add to TP-01/TP-05).
- **Rolling resistance:** Blickle rates Softhane only in words ("Rolling resistance very good"). No coefficient is
  published.

## 4. Keep-out that the castor needs (feeds the CAD keep-out set)
`KO_C01_swivel_<corner>` is a solid of revolution about the castor axis:
- the wheel envelope r_w(z) = hypot(38 + √(40² − (z − 40)²), 15) for z 0…80;
- the fork, r 50 (ESTIMATE), from z 80 to the castor plate at 98;
- swept over the travel −2.5…+17;
- plus 5 mm clearance.

Body-frame radius (nominal):

| z | 37 | 40 | 50 | 62 | 70 | 80 | 90 | 100 | 110 | 119 |
|---|---|---|---|---|---|---|---|---|---|---|
| r keep-out | 84.4 | 84.4 | 84.4 | 84.1 | 82.3 | 77.3 | 67.4 | 55.0 | 55.0 | 0 |

Carriage parts (they move with the castor) only need to clear the castor itself, with no travel sweep: r_w + 3 mm.
All the carriage parts below pass this check.

## 5. Plan-view changes required (checked against the rev B2 STEP files, 2026-10-05 15:57)

| # | Change | Why | Value |
|---|---|---|---|
| P1 | **Castor axis (±280, ±198) → (±275, ±180)** (`CASTER_XY`) | At (280, 198) the swept swivel keep-out hits K01/K02 cover chamfer 5.5 cm³, K05 edge 10.4 cm³, post A04 3.7 cm³, spine 10 cm³, pan. At (275, 180): only 0.1 cm³ into the 5 mm margin at the cover chamfer bottom (real clearance ≈ 3.8 mm at z 62; trim the cover's bottom chamfer edge by 2 mm if 5 mm is wanted) | – |
| P2 | **Spine end notch**, both spines, both ends | Swivel keep-out and carriage tongue | x ±202…±262 (local u −73…−13), z 37…128. The spine remains at full height for \|x\| < 202 and above z 128 at the ends; the roof bolts to that stub |
| P3 | **Pan corner cut** | Wheel at pan level | circle r 86 about the castor axis. It breaks through the pan chamfer edge (the pan corner opens). K05 must be carried by the cover there |
| P4 | **Post A04 (±320, ±115) → (±360, ±110)** | Inside the keep-out (r 84.4) | 30 × 30, x 345…375, \|y\| 95…125: outside the battery top-cover keep-out (\|y\| ≤ 90), outside the scanner footprint (\|y\| ≥ 136), 89 mm from the axis |
| P5 | **Remove E5B L/R and E16 R1a/R1b from the spine/battery gaps** | The spring column takes the gap (x ±100…±245, \|y\| 94…131, z 40…230) | Relocation is up to the electrical/CAD stream |
| P6 | **RR: E34 U8 DRDN40-48 (x −213…−158)** | Inside the RR keep-out (11.3 cm³) | Needs x ≥ −190.6 clear, or move it to another rail |
| P7 | Tower legs A05 removed | 15 × 15 legs at the plate corners are inside the swivel circle | Roof 128…134 carried by the spine stub (P2), A06 (FL), the corner rail bracket (RR) and the moved post (P4). Re-check CALC §9: bump-stop load up to 815 N at the axis, 43–49 mm from the spine line |
| P8 | RR CP tongue vs E0R_din_rail_lower_R | Found in the check | Tongue starts at \|x\| 220 (2 mm from the rail end at −218) |

Everything else was checked with zero overlap against all rev B2 STEP parts at all 4 corners: batteries, top-cover
keep-out, E13/E54 (FL), scanners, E42 gap fans, harnesses and DIN rails. Parts not exported as STEP (keep-out solids)
were not checked. The swivel keep-out may overlap KO_E13 by 4.4 mm: both are free air.

## 6. CAD geometry (FL; local u = sx·(x − xc), v = sy·(y − yc), outboard positive; xc = 275, yc = 180; z absolute, nominal)
**Mirroring:**
- FL and RR use the same parts (RR is FL rotated 180° about z);
- FR and RL use the mirror image.

Boxes are [u0…u1] × [v0…v1] × [z0…z1].

| ID | Part | Geometry | Material / note | Moves |
|---|---|---|---|---|
| C01 | Blickle L-ALST 80K | Plate 100 × 85 (u ±50, v ±42.5), z 98…102 (plate t 4 ESTIMATE). Holes 80 × 60 Ø9. Wheel D80 × 30, axle z 40, trail 38 (draw it trailing toward −u). Fork r 50 envelope z 80…98 | purchased, 0.7 kg | yes |
| C02 | Carriage weldment, part 1: carriage plate | [−50…50] × [−42.5…42.5] × [102…108]. 4 × M8 ISO 10642 countersunk into the castor holes. Ø30 relief at the axis for the kingpin rivet (ESTIMATE until the Blickle CAD) | S355MC 6 mm | yes |
| C02 | Part 2: tongue | [−55…−13] × [−65…−40] × [102…108]. Passes through the spine notch | S355MC 6 mm | yes |
| C02 | Part 3: mast | [−105…−65] × [−73…−65] × [60…184] ∪ [−65…−30] × [−73…−65] × [88…184]. Bolted to both block tops (4 × M3 each) | S355MC 8 mm | yes |
| C02 | Part 4: shelf | [−175…−103] × [−86…−54] × [72…80]; it passes under the lower block (block bottom z 82) and is welded to the mast bottom at u −105…−103. 2 spring spigots Ø23 × 5 at (−158, −70) and (−123, −70) | S355MC 8 mm | yes |
| C03 | PU bump pad | [−15…15] × [−15…15] × [108…111] | PU 90 ShA, bonded | yes |
| G01 | HIWIN MGN15R rail L190 | [−97.5…−82.5] × [−59…−49] × [40…230]. Bottom on the spine inner face (v −49 = y 131), 5 × M3 at pitch 40 | purchased | no |
| G02 | 2 × HIWIN MGN15H | [−106…−74] × [−65…−53] × [82…140.8] and [147…205.8] (c/c 65) | purchased, 0.092 kg each | yes |
| S01 | 2 × Gutekunst D-313J-02 | Coil De 31.6 / Di 24.4, axes at (−158, −70) and (−123, −70), z 80…131.2 | purchased | ends |
| B01 | Spring bracket | Plate [−175…−108] × [−86…−49] × [131.2…139.2] + vertical leg on the spine [−175…−108] × [−55…−49] × [139.2…170]. 4 × M6 in vertical slots ±3 mm. 2 spigots Ø23 × 5 downward | S355MC 6–8 mm, bent | no |
| B02 | Droop stop | Rubber buffer Ø20 × 10 on an angle bolted to the spine. Top at z 69.5 under the shelf at u −160…−140, v −84…−56 | standard buffer + angle | no |
| A05' | Tower roof | z 128…134 (unchanged top). Must cover the pad footprint at the axis and the scanner seat. **No legs inside r 85.** Supports: spine stub (z ≥ 128 at u −73…−13), A06 (FL) / corner bracket (RR), post P4 | S355MC 6 mm | no |

Absolute FL values used in the check:
- castor axis (275, 180);
- rail x 177.5…192.5, y 121…131;
- springs at (117, 110) and (152, 110);
- shelf x 100…172, y 94…126.

**Internal check (cadquery, rev B2 STEP files):**
- carriage parts vs the castor (castor frame): 0;
- body parts and springs vs the swept keep-out: 0;
- carriage swept over the travel vs body parts: 0. The only contacts are block/rail, which is how it is meant, and B1 1 mm into the blocks' x range: use B1 u ≤ −108 as in the table.
- After the check the blocks were raised to z 82/147 so that the shelf clears them. This is a carriage-internal change: the rail and the body parts are unchanged, and the blocks stay within u −106…−74, where nothing else sits at z 82…223.

## 7. Bill of materials, per robot (4 corners)

| Item | Part | Qty | Unit price | Source / status |
|---|---|---|---|---|
| 1 | Blickle L-ALST 80K, ID 754464 | 4 | not published (quote) | SOURCED data, blickle.com |
| 2 | HIWIN MGN15R rail, L 190 | 4 | not published (quote) | SOURCED data, HIWIN catalogue G99TE24-2410 p.91 |
| 3 | HIWIN MGN15H block (Z0 preload, standard seals) | 8 | not published (quote) | SOURCED data |
| 4 | Gutekunst D-313J-02 compression spring | 8 | €1.66 @ 17 pcs; €12.37 @ 1 (net) | SOURCED, federnshop.com |
| 5 | Carriage weldment C02 (carriage plate + tongue + mast + shelf), 2 mirror variants | 4 | ESTIMATE €35–60 (laser + bend + weld + zinc flake) | custom |
| 6 | Spring bracket B01 (bent, slotted) | 4 | ESTIMATE €8–12 | custom |
| 7 | PU pad 30 × 30 × 3, 90 ShA | 4 | ESTIMATE €1 | generic |
| 8 | Rubber buffer Ø20 × 10 M6 + angle | 4 | ESTIMATE €3 | generic |
| 9 | Fasteners: 16 × M8 × 16 ISO 10642 10.9, 20 × M3 × 10 (rail), 32 × M3 × 8 (blocks), 16 × M6 (B01), Loctite 243 | set | ESTIMATE €10 | generic |

Mass change per corner:
- moving: castor 0.7 + carriage ≈ 1.0 + blocks 0.18 = **≈ 1.9 kg**;
- fixed: rail 0.20 + B01 0.2 + springs 0.11 = ≈ 0.5 kg;
- the old CASTER_MASS was 1.6 kg.

## 8. Changes needed elsewhere

| Where | What |
|---|---|
| `amr_params.py` | `CASTER_D = 80`, `CASTER_H = 102` (castor only), `CASTER_XY = (275, 180)`, `CASTER_TRAIL = 38`, `CASTER_SWIVEL_R = 79.4` (ESTIMATE), `SUSP_K = 28.34`, `SUSP_F_INST = 76`, `SUSP_TRAVEL = (-2.5, 17.0)`, `POSTS = [(360, 110)]`. `TOWER_ROOF` stays (128, 134); `SCAN_Z` stays 184.5. Update the `SUSP` text |
| `amr_cad.py` | Draw §6 at the 4 corners. Remove the A05 legs. Add the spine notch, pan cut and post move. Add keep-out `KO_C01_swivel_*` from §4. Re-run the interference and keep-out checks |
| `CALC.md` §2/§3/§9 | New contact points (275, 180), trail 38. k 28.34, F_inst 76, stop at +17 mm. 20 mm threshold: drive share 24.7 % at the stop, lower beyond. Tower roof bump-stop load. Pitch vs the 200 mm scan-plane limit (§1.3) |
| `VERIFICATION.md` CA1 / change 8 | CA1 becomes REPLACED with this design. Change 8: "+30–40 mm tower" is withdrawn |
| `README.md` | Castor D80. Threshold rule from §3.7 |
| Electrical / CAD rev B2 | Relocate E5B L/R, E16 R1a/R1b and E34 (P5, P6) |
| `ce/TEST_PLAN.md` | TP-05: test pieces at the field edges while accelerating in the top SLS band (pitch). New TP: castor preload set per corner on a scale; 20 mm threshold at 0.3 m/s |

## 9. Open items
1. **Blickle:**
   - quote and STEP for L-ALST 80K;
   - confirm the swivel radius (79.4 calc.), plate thickness and kingpin head height;
   - load capacity at 5.4 km/h.
2. **HIWIN or distributor:** price and lead time for MGN15R L190 + MGN15H. A stainless or corrosion-resistant option is not needed indoors.
3. **ISO 3691-4:2023:** confirm the test-piece dimensions (§1.2) from the purchased standard.
4. **SICK:** confirm "at least 200 mm" on OI p.52 is a typo for "at most".
5. **Prototype:**
   - measure the per-corner preload after setting;
   - measure the carriage friction (expected < 5 N);
   - check scan-plane height at the field edges in all SLS bands (TP-05).
