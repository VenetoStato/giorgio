# Giorgio — base payload acceptance test (ballast, before integration)

Goal: prove on the real chassis (Tracer 2.0, or the alternative base) that it carries Giorgio's mass at Giorgio's CoG
safely, **before** the arms and electronics are mounted. Values come from `out/mass_properties.json` and VALIDATION.md;
re-take them if the design changes.

## Test load (ballast rig)

| Item | Value |
|---|---|
| Superstructure + product payload | **88.8 kg** (current design, both modules); also test at **100 kg** (manual limit) |
| CoG of the load | x = +5 mm, y = +1 mm (nominal), z = 593 mm above the floor = **424 mm above the Tracer deck** (169 mm) |
| Work-posture offset | 2nd configuration with the CoG moved to x = +25 mm (arms holding 2 × 3 kg in front) |

**Rig.** The real P01 adapter plate bolted to the rails exactly as designed: 16 × M5 countersunk into T-nuts at 0.6 N·m. On it sits the real column weldment (W01) with a steel ballast frame. Steel plates are clamped on the frame at heights chosen to reproduce mass, CoG height and the yaw inertia within ±10 %.

**Measure the rig before testing:**
- mass, on a platform scale (±0.2 kg);
- CoG height, by the tilt method (lift one side 100 mm on blocks, read both scales);
- plan CoG, by 4-corner scales (±5 mm).

## Instrumentation

- IMU on the deck: 3-axis acceleration at ≥ 200 Hz, plus roll/pitch.
- Wheel odometry and the chassis CAN log: motor currents, temperatures, battery voltage/current, error frames.
- Video at 60 fps, side and front.
- Safety: a tether or a soft catch frame. Run the first tests at 50 % speed.

## Tests and pass criteria

| # | Test | Procedure | Pass criteria |
|---|---|---|---|
| 1 | Static load | 30 min at rest, rig at 100 kg | No error codes; deck deflection at the column foot < 1 mm (dial gauge); no rail or T-nut slip (marked screws) |
| 2 | Straight braking | 2.0 m/s → normal stop, then e-stop (onboard button + CAN stop); 5 runs each, both directions, at 88.8 kg and 100 kg | No wheel lift (IMU pitch < 2°, no caster unloading on video); e-stop distance ≤ the value AgileX states (manual: 0.9 m empty); peak decel recorded. **Our design assumes ≤ 2.2 m/s² and a static tip limit ≥ 6.2 m/s²** |
| 3 | Acceleration | 0 → 2.0 m/s at maximum command | Pitch < 2°, no wheel slip > 10 % |
| 4 | Turning | Spin in place at max yaw rate; circle at 1.0 / 1.5 / 2.0 m/s on the minimum radius; S-curves | Lateral acceleration recorded ≤ 0.3 g; roll < 2°; no caster lift |
| 5 | Slope 8° | Up/down on an 8° ramp (manual limit), stop and restart mid-ramp, park 5 min | Holds position (brake); no motor over-current fault; motor temperature < manufacturer limit |
| 6 | Slope 15° | **Only on RANGER MINI 3.0** (rated > 15°); not on Tracer 2.0 | Same as test 5 |
| 7 | Obstacles | 10 mm step (manual limit) and 20 mm cable cover, at 0.5 and 1.0 m/s, straight and at 45° | No fault, no ballast shift; IMU vertical peak recorded (design assumes ≤ 2 g bump) |
| 8 | Duty | 1 h office loop at 1.0 m/s average, with 20 stops/starts and 10 spins, at 88.8 kg | Motor and driver temperatures plateau below limits with ≥ 15 °C margin; battery current within rating; no derating events; repeat at 30 °C ambient if possible |
| 9 | Post-check | Re-torque check of all 16 rail screws and the 8 column-foot screws; inspect the rails | No loosening (paint marks intact), no rail deformation |

**Accept the base if all of tests 1–9 pass at 88.8 kg and tests 1–3 pass at 100 kg.** Any wheel lift, fault or slip → stop and reduce mass or speed limits.
Record everything in a test report with the raw logs. It becomes part of the technical file (EN ISO 12100 risk assessment, base limits).
