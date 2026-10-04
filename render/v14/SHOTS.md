# v14 — boxes: front tray, rear rack, bimanual tote

All numbers below were measured in the simulation (MuJoCo, `giorgio_scatole.py` → `render/rec_scatole_v14.pkl`, 5848 frames at 30 fps = 194.9 s).
Nothing is teleported or welded: the small boxes are held by gripper friction, the tote by the two grippers pinching its rims,
and on the tray/rack everything rests on a rubber mat by friction only.

Render style: light studio (like the v11 logistics shots), 1920×1080 JPEG, 48 samples, `--fast`, safety rings hidden.
Commands: `render/run_v14.sh`. Frame `f_0000` = recording frame given in "source frames".

| shot | folder | frames | length | source frames (rec_scatole_v14) |
|---|---|---|---|---|
| bimanual tote pick | `v14/t_pick/` | 250 | 8.3 s | 2460–2709 |
| small box onto the front tray | `v14/t_load/` | 270 | 9.0 s | 1890–2159 |
| small box onto the rear rack | `v14/t_rear/` | 270 | 9.0 s | 560–829 |
| tote set down at the destination bench | `v14/t_unload/` | 230 | 7.7 s | 3330–3559 |

## t_pick — bimanual pick of the tote
Frontal close-up. Both arms come down on the tote, each gripper pinches one side wall at the rim (inner finger inside, outer finger outside),
then both lift together (synchronised straight-line moves, constant hand orientation, so the tote stays level).
Key frames: grippers close at shot frame ~134 (rec 2594), tote leaves the bench ~170 (2630), lifted 12 cm ~206 (2666).

On-screen numbers:
- tote 360 × 240 × 140 mm, **3.1 kg** (1.0 kg tote + 6 bottles × 0.35 kg) → **≈1.55 kg per arm** (product rating 3 kg per arm)
- pinch force per gripper **≈42 N** (mean while carried; minimum 35 N); tote weight 30 N
- tote slip in the grippers **3.6–3.8 mm** over the whole pick → 4.3 m drive → set-down

## t_load — small box onto the front tray
Left arm carries a 160 × 100 × 100 mm, **1.2 kg** box from bench A2 and lowers it into the left slot of the front tray
(gripper tilted 30° forward for reach; same tilt at pick and place, so the box lands flat).
Key frames: box lowered onto the mat by shot frame ~238 (rec 2128), gripper opens ~261 (2151).
Note: the box is still turned in the gripper at the start of the shot (63° at frame 0, < 10° from frame 90 on) — start the cut at frame ~90 for an upright box.

On-screen numbers:
- front tray: 210 × 490 mm at 0.94 m, 3 slots (pitch 145 mm: the fingers fit between boxes)
- box on the tray **13 mm** from the slot centre, **0.0° tilt** (measured at the end of loading)
- box shift on the tray during the 4.3 m drive: **3.8 mm**

## t_rear — small box onto the rear rack
Rear 3/4 view. The right arm brings a 1.2 kg box from the front bench around its side to the rear rack (the rack replaces the coffee backpack,
same mounting uprights) and sets it down; the hand yaws 90° in transit, so the box is stored crosswise.
Key frames: box lowered onto the rack by shot frame ~234 (rec 794), gripper opens ~256 (816).
Note: the box is turned in the gripper at the start (69° at frame 0, < 10° from frame 114 on) — start the cut at frame ~114 for an upright box.

On-screen numbers:
- rear rack 195 × 490 mm at 0.95 m (mid-torso), loaded **by the arm**, no operator
- box placed **7.2 mm** from the slot centre, **0.0° tilt**; moved **4.1 mm** during the drive
- closest arm approach to the rack over the whole mission **49 mm**

## t_unload — tote set down at the destination bench
The robot arrives at bench B2 with the tote in its arms (drive ends at shot frame ~41), lowers it, opens both grippers and withdraws.
Key frames: tote on the bench at shot frame ~92 (rec 3422), grippers open ~113 (3443).

On-screen numbers:
- drive A2 → B2: **4.29 m** in 23.5 s, top speed 0.57 m/s; docking error **21 mm / 0.09°**
- tote set down **0.9 mm** from the planned point (directly below where it was carried), **0.0° tilt**
- whole mission (2 small boxes + tote loaded, drive, everything unloaded on B2): **193 s**;
  small boxes on B2: 1.9 mm and 8.5 mm from their targets

## Product stills (dark studio, `--dark --solo`, 96 samples, like `stills_v11/cfg*`)
| file | configuration | boxes |
|---|---|---|
| `stills_v14/tray_front.png` | front box tray (bottle tray and coffee backpack removed) | 3 × 1.2 kg on the tray |
| `stills_v14/tray_rear.png` | rear rack instead of the coffee backpack; standard bottle tray kept in front | 2 × 1.2 kg on the rack (crosswise) |
| `stills_v14/tray_both.png` | front box tray + rear rack | 3 + 2 boxes |
Source: `pose_scatole_v14.py` → `render/rec_cfg_{front,rear,both}_v14.pkl` (boxes dropped 3 mm above their slots and settled by physics for 1.5 s; final tilt ≤ 0.05°).

## Mass budget (Ranger Mini 3.0 payload 120 kg)
Reference: `cad/VALIDATION.md` — superstructure 77.2 kg (includes coffee module 5.89 kg and bottle-tray halves 2 × 0.89 kg) + product payload 8.1 kg = 85.3 kg.
New parts are **simulation masses (estimates, not CAD parts yet)**: front box tray 1.51 kg, rear rack 1.72 kg (aluminium sheet, EPDM mat, lips, uprights/braces).
Product payload counted as 2 × 3 kg (arm rating) + tray/rack contents.

| configuration | superstructure | payload | total | % of 120 kg |
|---|---|---|---|---|
| (a) front box tray, 3 boxes (no coffee, no bottle tray) | 71.0 kg | 6 + 3.6 | 80.6 kg | 67 % |
| (b) rear rack, 2 boxes + bottle tray (2.1 kg) | 73.0 kg | 6 + 2.1 + 2.4 | 83.5 kg | 70 % |
| (c) front tray + rear rack, 3 + 2 boxes | 72.8 kg | 6 + 3.6 + 2.4 | 84.8 kg | 71 % |
| as simulated in the mission (c, with 1 + 1 boxes and the 3.1 kg tote in the arms) | 72.8 kg | 3.1 + 2.4 | 78.3 kg | 65 % |

## Checks
- Contacts (physics, sampled every 10 ms over the whole mission): **no arm contact** with robot shells, tray, rack, benches or non-target boxes.
- True-surface distances (`verifiche/scatole_v14.py`, every 0.1 s, mesh surfaces, shoulder links excluded as in `gusci_reali.py`):
  arms ↔ torso shell **14.6 mm** (left link3) · head shell 48 mm · Gemini 44 mm · front tray 30 mm · rear rack 49 mm · bench tops 49 mm;
  carried boxes ↔ torso shell 33 mm. `verifiche/gusci_reali.py` on the same recording: **14.7 mm**.
- Joint torque (motor PD + gravity and payload compensation) vs Damiao limits: ≤ 56 % everywhere except one 0.2 s event (see caveats).

## Caveats (honest list)
- **The tote cannot be put on the front tray by the two arms**: squeezing a 300 mm object 0.2 m in front of the chest puts the OpenArm elbow at its
  140° limit. So the tote is carried in the arms during the drive; the front tray takes small boxes (single arm).
- A palm squeeze of a closed box was tried first: with the stock wrist gains the squeeze force was only ~11 N per side (not enough for 3 kg),
  so the big item became an open tote pinched at the rims.
- Small-box transfers are slow and not "waiter-like": grasp → release takes 17–19 s each (bench → rack and bench → tray alike), because
  the arm must reconfigure (joint-space path, RRT-Connect with 30 mm clearance margin). In transit the box is held but **turned up to
  67–103°** (measured from the recording); it is level only at pick and place. Constraining the box to ≤ 35° or ≤ 60° in the planner was
  tried: no collision-free path for the front-tray transfer, so it was not used. The tote (bimanual) stays within 4.4° the whole time.
- Outside the rendered shots, two small glitches in the recording: at 48–49 s (rec frames ~1440–1480) the left arm's open fingers grazed the small
  box on its approach and shifted it by 12 mm (it touched the tote, 0.8 mm); the grasp still worked. At 74.2–74.4 s, while withdrawing after the
  release on the front tray, the left gripper dragged the box for 0.2 s (left wrist-roll motor at its 7 Nm limit; box touched the tray side rail, 1.2 mm).
- The arm controller adds a payload feed-forward (Jᵀ·m·g for the known box mass); without it the loaded arm sagged ~16 mm and missed the rack slot.
- The safety scanners slowed the robot 5 times during the drive (warning field hit by bench/furniture legs; no people in this scene).
- Box poses come from the simulator state (no vision in this scenario). Small-box targets are fixed bench/tray/rack slots; the tote target on B2
  is the point under the hands at arrival.
- Tray/rack masses are estimates; CAD parts, bolted-joint checks and tipping for these variants have not been done (the CAD tipping case
  "2 × 3 kg at 0.55 m reach" is heavier than the tote carried here, ≈1.55 kg per hand at ~0.43 m).
