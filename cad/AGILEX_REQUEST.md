# Request to AgileX Robotics (sales / technical support)

**To:** AgileX sales and technical support (via global.agilex.ai contact form / regional distributor)
**Subject:** RANGER AIR (selected) + automatic charging station: written payload, power and docking data for a 60 kg mobile-manipulator superstructure

Dear AgileX team,

We are integrating a bimanual service robot (two 7-DOF arms, column, 48 V battery, sensors) on an AgileX
chassis. We have read the TRACER 2.0 user manual (V1.0.0, 2025-03), the RANGER MINI 3.0 user manual and your
product pages. Before ordering, we need the following answers **in writing**, for each of TRACER 2.0, RANGER MINI 3.0 and RANGER.

**Our load case.** Superstructure 65–90 kg (65–71 kg if powered from your battery), including up to 8 kg handled payload. It is mounted on the top rails.
Its centre of mass is centred on the chassis in plan (within ±20 mm at rest; up to ~25 mm forward while the arms handle objects).
Its height is ≈ **0.42 m above the TRACER 2.0 deck** (0.59 m above the floor). On RANGER MINI 3.0 it is ≈ 0.75 m above the floor, i.e. 0.41 m above the rails; on RANGER ≈ 0.82 m above the floor, i.e. 0.29 m above the rails. Indoor use (offices, labs), flat floors, ramps ≤ 8°.

1. **Allowable payload.**
   - The TRACER 2.0 manual states 100 kg, the datasheet 150 kg and the web page 80 kg. Which value applies?
   - Does it depend on the payload centre-of-mass height? Please give the allowable mass for a CoG 0.42 m above the deck.
   - The same questions apply to RANGER MINI 3.0 (120 kg) and RANGER (150 kg).
2. **Dynamic limits with that payload:**
   - maximum acceleration and deceleration;
   - braking distance from 2.0 m/s fully loaded, both normal stop and e-stop (the manual gives 0.9 m empty);
   - maximum speed and turning rate you recommend for a CoG of that height;
   - slope limits loaded.
3. **Centre of rotation.** The exact position of the drive-wheel axle (or centre of rotation) relative to the top rails, with a dimensioned drawing or a STEP model of the chassis including the top rails (profile, slot size, T-nut type and permissible load per T-nut, rail height above the body).
4. **Safety interface.** Is an **external emergency-stop / protective-stop input** available, i.e. a safety-rated, dual-channel input or STO on the motor drivers? We want our safety relay (Pilz PNOZ, PL d/e, driven by SICK nanoScan3 scanners) to stop the chassis. If none exists, what modification do you support or allow without voiding warranty and CE marking? Do you supply a Declaration of Incorporation and an ISO 3691-4 / ISO 13849-1 assessment of the stop function?
5. **Power.**
   - The accessory output: the manual says ≤ 5 A / 120 W, the datasheet 24 V 15 A. Which is correct?
   - RANGER MINI 3.0 / RANGER: the rating of the 48 V output.
   - Can we charge the chassis battery from our own 48 V system through the charge port, and what charge profile does it need?
6. **Automatic charging station.** Self-charging on *your* station is mandatory for us.
   - The NAVIS API mentions your "autonomous charging kit" and a "wireless charging pile". Modular ALOHA (on RANGER MINI 3.0) is sold with an auto-return charging pile. Please send the **datasheet and price of the charging station and the robot-side kit**, and confirm compatibility with RANGER MINI 3.0, RANGER and TRACER 2.0. (The TRACER 2.0 product page mentions "automatic recharging", but its text appears to be copied from the RANGER AIR page.)
   - Charging method: contacts or wireless (inductive). Charging voltage and current; time from 20 % to 90 %.
   - Robot-side receiver: dimensions, mounting position and height on the chassis, required clear area/window in a body shell (non-metallic?), cable routing.
   - How the robot finds and aligns to the station (lidar profile, reflector, QR/AprilTag, IR), and the alignment tolerance (x, y, yaw).
   - Can the docking run through your open ROS 2 driver, or only through NAVIS? Is NAVIS licensed per robot (cost)?
   - **While docked, can the payload stay powered from the accessory output** (computer, sensors, arms at rest), and does the station then charge the battery at the same time?
7. **Accessory power for our superstructure** (we would run it from your battery):
   - RANGER MINI 3.0 and RANGER rear output 46–50 V, ≤ 15 A / 720 W. Is that continuous? What peak current and duration are allowed?
   - Can we add a second output in parallel?
   - What happens at the 10 % SOC cut-off: is there a warning over CAN, and how long is it before the cut?
   - Battery capacity options: RANGER multi-pack — is it available on RANGER MINI 3.0?
8. **Price and lead time** for qty 1 and qty 10, for each chassis, the charging station/kit, NAVIS, and any safety option.
9. **Data conflicts in your documents:**
   - RANGER mass: 100 kg "curb weight" vs 135 kg "single battery".
   - RANGER height: 475 mm in the table vs about 536 mm to the top of the rails on the drawing.
   - RANGER IP rating: IP22 vs IP55.
   - TRACER 2.0 payload: 80 / 100 / 150 kg.
   Please confirm the correct values.

10. **RANGER AIR specifically.** This is our selected base.
    - **Payload:** is 80 kg allowed with our load (59 kg incl. payload, CoG 0.54 m above the deck, centred within ±20 mm)? What maximum acceleration, deceleration and braking distance from 1.5 m/s apply with that load, and what yaw rate and lateral acceleration in spin and crab modes?
    - **Top plate:** thread size and depth of the 8 top holes (200 × 80 grid); their exact x position from the body centre; deck plate material and thickness; a STEP model of the chassis.
    - **Expansion port:** is the rating 25 A / 600 W (spec table) or 10 A, 23–26.5 V (mating-plug table)? Continuous or peak? What peak current is allowed, and for how long? Can a second output be added? What is the pinout of the top electrical interface?
    - **Automatic charging station:**
      - part number, price, charging voltage/current;
      - how the robot finds and aligns to it (marker, lidar, IR) and the tolerance;
      - does it require the navigation version or NAVIS, and the licence cost;
      - box height and depth from the wall: our robot has a 54 mm overhang behind the rear face above 380 mm;
      - can the payload stay powered while charging;
      - can it run autonomously with our own ROS 2 navigation (we have 2 SICK nanoScan3 scanners on the corners)?
    - **Navigation version:** where exactly are the lidars / "pucks" on the top corners, and is the standard version enough for docking?
    - Runtime with a 250 W continuous accessory load.
    - Availability of an external safety stop input or STO on the RANGER AIR drives.

Thank you — written answers, drawings or STEP files would let us close our design review.

Best regards,
Giorgio project team
