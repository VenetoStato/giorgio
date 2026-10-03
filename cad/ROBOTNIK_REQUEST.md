# Request to Robotnik (RB-THERON) — kept for the record

The owner rejected the RB-THERON on price on 2026-10-03, so this request is **not to be sent** unless that choice is reopened.
The archived CAD state is in `archive_rbtheron/`.

**Subject:** RB-THERON as the base of a bimanual service robot: payload, interfaces, outputs, safety I/O, docking

1. **Payload and CoG (R6).** Is the 200 kg payload allowed with an 84 kg superstructure, CoG 0.71 m above the floor (0.39 m above the top), centred within ±20 mm? Is there a CoG-height limit? What are the loaded accel/decel and braking distance from 1.25 m/s, normal stop and e-stop?
2. **Top interface (R6).** Hole pattern, thread and depth of the top plate; a STEP model; the declaration of incorporation and the ISO 3691-4 / ISO 13482 statements.
3. **Outputs (R1).** VBATT, 24 V and 12 V outputs: current rating continuous and peak, fusing, connector type.
4. **While docked (R3).** Does VBATT stay powered while docked and charging, and can a payload charger draw about 8 A from it?
5. **Charging station (R2).** Power, voltage and current; time to charge 0.72 kWh; contact geometry and height on the robot; alignment tolerance; price of a spare station.
6. **Safety (R4).**
   - Does the safety PLC have a dual-channel external E-stop input, and a safe output ("protective / emergency stop active") for a payload safety relay (Pilz PNOZmulti)?
   - What are the PL and PFHd of the base stop function?
   - What integrity is required for the speed signal used in laser field switching?
   - Can the PLC take our arm stop?
   - May we mount our own scanners at the two free corners?
7. **Battery (R5).** Chemistry, voltage window, maximum discharge current; extra battery modules (capacity, price, mass).
8. **Commercial.** Price of the Safety version, lead time, software licences (Robot Local Control, HMI, navigation).
