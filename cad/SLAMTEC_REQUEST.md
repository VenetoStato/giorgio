# Request to Slamtec (sales / technical support)

**To:** sales@slamtec.com (cc: support@slamtec.com)
**Subject:** Poseidon Standard Edition: written confirmation of auto-charging dock, 48 V payload output and payload limits for an 85 kg mobile-manipulator superstructure

Dear Slamtec team,

We are designing a wheeled bimanual service robot ("Giorgio"): an aluminium column with two 7-DOF arms, a 3D-vision torso,
two safety laser scanners and its own 48 V LiFePO4 pack (1.44 kWh). We have selected the **Poseidon Standard Edition** as the
mobile base. We have read:

- the *Poseidon Standard Edition datasheet v1.2.1 (2026-09-04)*,
- the *Poseidon Hot-Swap Edition datasheet v1.2.1 (2026-09-04)*,
- the web pages https://www.slamtec.com/en/poseidon and https://www.slamtec.com/en/poseidon/spec.

Before ordering we need the following answers **in writing**.

**Our load case.** Superstructure 77–85 kg including up to 8 kg handled payload, bolted to the Poseidon top deck.
Centre of mass centred in plan within ±20 mm at rest (up to ~25 mm forward while the arms work), about **0.69 m above the
floor** (≈ 0.37 m above the deck). Indoor use (offices, labs, light production), flat floors.

Our superstructure loads: about **1.24 kW sustained** and **2.1 kW peak for up to 5 s** if powered directly at 48 V, or
**about 370 W** if the base only recharges our own 48 V pack through an isolated DC-DC charger.

## 1. Automatic charging (mandatory for us)
1. The Standard Edition datasheet says *"Charging Method: Automatic / Manual"*, while the Hot-Swap Edition datasheet says
   *"Hot-swappable (battery swap), Manual charger"*. Please confirm that **automatic charging is available only on the
   Standard Edition**, or tell us if the Hot-Swap Edition can also be combined with a charging dock.
2. **Charging dock:** product name, part number, datasheet and price. Is it included with the robot or sold separately?
3. Charging method (contacts or wireless), charging voltage, current and power; time from 20 % to 90 %.
4. Where the charging contacts or receiver sit on the robot (front or rear, height), and which end of the robot docks.
   Our body shell must leave the contacts or the docking sensors clear: please send a drawing of the keep-out zones.
5. How the robot finds and aligns to the dock (lidar profile, reflector, camera, IR) and the docking accuracy (x, y, yaw).
   Does a tall 85 kg superstructure, or a shell around the column, affect docking?
6. Does docking run through SLAMWARE only, or can we trigger it from **ROS 2** / your SDK (which API call)? Is any licence fee
   required?
7. Does the dock need wall or floor fixing, a mains supply (230 V / 50 Hz, EU plug), and is it CE-marked?

## 2. 48 V power output for our superstructure
8. The datasheet lists *"Power Output Interface: 48V 30A (rated)"* and battery *"Rated 30A; continuous max. 50A;
   instantaneous peak 110A"*. Please confirm:
   - is 30 A at the output **continuous**, with the robot driving at full payload at the same time?
   - may the output deliver **~44 A (2.1 kW) for 5 s**? What peak current and duration are allowed at the output connector?
   - is the 50 A continuous battery limit shared between the drive motors and the output?
9. **While docked and charging, does the 48 V output stay live?** Is the payload then supplied by the charger or by the
   battery, and does the battery still charge with a 370 W (≈ 8 A) payload load?
10. Connector type on the Standard Edition (the Hot-Swap Edition lists XT60, 12 AWG), output voltage range, fusing.
    Is the output switched by software, and is it cut by the e-stop or at low battery? At which SOC, and with what warning?

## 3. Mechanics and dynamics with our load
11. Is our load (85 kg, CoG ≈ 0.69 m above the floor) within the rated 150 kg? What maximum CoG height do you allow?
    Your page mentions stable motion at 1.8 m total height with an anti-tip coefficient of 1.65: under which load?
12. Recommended maximum acceleration, deceleration, speed and yaw rate with this load; braking distance from 1.0 and
    1.5 m/s (normal stop and e-stop).
13. Deck mounting interface: hole pattern, thread size, permissible loads; a **STEP model** of the chassis.

## 4. Safety
14. Is an **external emergency-stop / protective-stop input** available (dual-channel, safety-rated, or STO on the drives)?
    We want our safety relay (driven by SICK nanoScan3 scanners, PL d) to stop the base.
15. Which components are certified (the page mentions "core components certified to international standards")?
    Is there a Declaration of Conformity / Incorporation (EU), and any ISO 3691-4 or ISO 13849-1 assessment?

## 5. Commercial
16. Price and lead time for **1 unit and 10 units**: Poseidon Standard Edition, charging dock, any SDK licence, shipping to
    Italy (EU). Warranty and spare parts (battery, wheel modules). EU distributor, if any.

Written answers, drawings or STEP files would let us close our design review.

Best regards,
Giovanni Pitton — Giorgio project
