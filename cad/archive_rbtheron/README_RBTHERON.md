# Archived: Giorgio on Robotnik RB-THERON (work in progress, superseded 2026-10-03)

Owner decision: RB-THERON rejected (too expensive, €25,950–31,500 excl. VAT). This folder freezes the CAD state at the time of the switch.
It is **not a finished design**: the last validation (VALIDATION.md here) had **2 FAIL**:
- the backpack e-plate standoffs clashed with the coffee DC-DC;
- one pod-flange hole in the adapter was at 2.4 mm edge distance.

Everything else passed or was a WARN.

Key RB-THERON facts (official datasheet rev AF:02.26, robotnik_description jazzy-devel, charging-station datasheet):
- body 692 (717 incl. E-stops) × 550 × 320 mm; 70 kg; payload 200 kg (no CoG condition published);
- differential drive: wheels Ø152 at y ±251.6, 4 casters at (±235, ±182.5);
- 48 V 15 Ah battery; outputs 12/24 V/VBATT with ratings unpublished;
- 2 picoScan120 at the FR/RL corners (z 238), inside the body;
- docking contacts at the **front**, x +0.32 m, z ≈ 0.166 m; charging station 543 × 292 × 352 mm, 600 W;
- the safety module exposes no safety-rated I/O for a third party (electrical lead) → our 2 × nanoScan3 + PNOZ kept, pods at the FL/RR corners.

Design state:
- fixed column: deck at 320 leaves only 232 mm under the torso, so a 150 mm telescope is impossible;
- our 15s 30 Ah pack charged by a Victron Orion-Tr 48/48-6 from VBATT;
- superstructure + 2 × 3 + 2.1 kg payload ≈ 83.6 kg (42 % of 200 kg);
- tipping nominal ≈ 5.4–5.9 m/s².

Questions for Robotnik, if ever reopened (electrical/ARCHITECTURE.md §16.6, R1–R6):
- output current ratings of the 12 V, 24 V and VBATT outputs;
- station power and charge time;
- whether VBATT stays live while docked, and whether we can draw ~8 A from it there;
- an external dual-channel E-stop input and a safe output, with their PL and PFHd;
- battery chemistry and extra battery modules;
- payload CoG-height limit, mounting interface and STEP model, declaration of incorporation;
- braking distance loaded;
- price, lead time and software licences.
To use these files, copy them back over cad/ (they import geom.py and fasteners.py from cad/).
