"""All dimensions of the Giorgio mechanical design (mm, kg). Base frame = MuJoCo "amr" body:
origin on the floor at the Tracer centre, x forward, y left, z up. Column lift = 0.

Every purchased-part number carries a confidence tag: SOURCED (datasheet/manual/official CAD),
SECONDARY (reseller/forum), ESTIMATE / ASSUMED (no public source; must be confirmed before ordering).
The full source table is in SOURCES.md.
"""
import math

# ---------------------------------------------------------------- AgileX Tracer 2.0 (manual p.35 drawing, datasheet)
TR_L, TR_W, TR_W_BODY, TR_H = 702.0, 610.0, 580.0, 169.0      # SOURCED (610 incl. side bumpers/knobs, 580 body)
TR_GROUND = 27.0                                               # SOURCED ground clearance
TR_MASS = 55.0                                                 # SOURCED 54-56 kg
TR_PAYLOAD = 100.0                                             # SOURCED manual safety section (datasheet says 150)
TR_TRACK = 517.4                                               # SOURCED "wheelbase" (drive wheel spacing)
TR_RAIL_Y = 115.0                                              # SOURCED rails 230 mm apart
TR_RAIL_W, TR_RAIL_H, TR_RAIL_HALF_L = 40.0, 20.0, 280.0       # ESTIMATE from the drawing scale (rail ~39 mm wide, ~561 long); height ASSUMED
TR_BODY_TOP = TR_H - TR_RAIL_H                                 # ASSUMED: 169 = top of rails
# plan octagon measured on the manual drawing (scale 1.078 mm/px): front chamfer 57 x 117, rear 69 x 127  (ESTIMATE +-3 mm)
TR_OCT = [(351, -173), (351, 173), (294, 290), (-282, 290), (-351, 163), (-351, -163), (-282, -290), (294, -290)]
TR_WHEEL_R = 80.0                                              # ESTIMATE (not published)
TR_COG_Z = 80.0                                                # ESTIMATE (battery/motors low)

# ---------------------------------------------------------------- base adapter plate
AD_T = 8.0                                                      # was 10: column foot now tapped in its own flange
AD_Z0, AD_Z1 = TR_H, TR_H + AD_T                               # 169 .. 177
AD_INSET = 5.0

# ---------------------------------------------------------------- column (telescopic, manual adjust)
COL_X = -60.0                                                  # sim: column at x = -0.06
FL_T, FL_HALF = 12.0, 100.0                                    # foot flange 200 x 200 x 12
TUBE_OUT, TUBE_T = 100.0, 3.0                                  # sleeve: EN AW-6060 square tube 100x100x3 (EN 755-2 standard size; was 5)
SLEEVE_TOP = 555.0
PROF = 80.0                                                    # item Profil 8 80x80 leicht 0.0.265.80: 5.33 kg/m, Ix 134.06 cm4 (SOURCED)
PROF_KG_M = 5.33
PROF_CORE_D = 10.2                                             # ESTIMATE core bore -> tapped M12
PROF_BOT = 195.0
STROKE = 150.0                                                 # proposed (sim: 400, not realisable, see README)
INDEX_PITCH = 25.0
LINER_T = (TUBE_OUT - 2 * TUBE_T - PROF) / 2 - 0.2              # POM-C liners/pads (6.8), 0.2 mm running clearance per side
BRK_T = 20.0                                                   # torso bracket thickness
TORSO_Z = 580.0                                                # sim torso origin (body_link0 underside) at lift 0
BRK_Z0 = TORSO_Z - BRK_T                                       # 560
PROF_TOP = BRK_Z0 + 5.0                                        # profile enters a 5 mm spigot pocket -> 565

# ---------------------------------------------------------------- OpenArm 2.0 body_link0 (official STL, measured)
BL_PLATE = (-155.0, 95.0, -95.0, 95.0, 8.0)                    # x0,x1,y0,y1,t  (STL: 250 x 190 x 8, SOURCED)
BL_GRID = [(x, y) for x in range(-135, 76, 30) for y in range(-75, 76, 30)]   # 48 holes, 30 mm grid (STL) ; docs: M6 taps
BL_MASS = 13.89                                                # URDF body_link0 (SOURCED, the sim uses 8.0)
BL_BOLTS = [(75, 75), (75, -75), (75, 15), (75, -15), (-135, 75), (-135, -75), (-135, 45), (-135, -45)]
ARM_SHOULDER_Z = TORSO_Z + 698.0                               # 1278

# ---------------------------------------------------------------- sensors
SCAN_Z = 180.0                                                 # sim scan plane (kept: ISO 3691-4 lying test piece needs a low plane)
NS3_W, NS3_D, NS3_H = 100.6, 102.5, 80.2                       # SOURCED housing; +15 mm system plug at the rear (117.5 total)
NS3_PLANE = 50.5                                               # SOURCED scan plane above housing base
NS3_HOOD_D = 86.0
NS3_MASS = 0.67
NS3_HOLE_Z, NS3_HOLE_PITCH, NS3_HOLE_FROM_REAR = 19.0, 44.0, 26.3   # SOURCED (2x M5x7.5 per side); reading of the chain = ASSUMED
NS3_AXIS_FROM_REAR = 26.3 + 24.0                               # mirror axis from the rear housing face (ASSUMED reading)
NS3_PLUG = 15.0
GEM = dict(L=124.0, H=29.7, D=27.7, mass=0.135, m4_pitch=95.0)  # SOURCED Orbbec Gemini 330 datasheet V1.6
GEM_POS = (108.0, 0.0, TORSO_Z + 665.0)
GEM_TILT = 50.0
X4 = dict(W=46.0, D=37.6, H=123.6, mass=0.203)                  # SOURCED Insta360 X4

# ---------------------------------------------------------------- power / electronics envelopes
BATT = dict(L=270.0, W=400.0, H=75.0, mass=13.0, cap="15s 30 Ah LFP, 48 V nominal, 1.44 kWh")   # ESTIMATE custom flat pack (was 15s 40 Ah 1.92 kWh 17 kg)
DCDC = dict(L=129.2, W=125.2, H=85.5, mass=1.375)              # SOURCED Mean Well DDR-480C-24 (mounted lying)
PNOZ = dict(L=45.0, W=120.0, H=101.4, mass=0.235)              # SOURCED Pilz PNOZ m B0 772100 (upright on DIN rail)
JETSON = dict(L=110.0, W=110.0, H=71.65, mass=1.58)            # SECONDARY dims / SOURCED mass
CHARGER = dict(L=150.0, W=100.0, H=60.0, mass=1.2)             # ESTIMATE 48->24 V 10 A LFP charger for the Tracer battery
CONTACTOR = dict(L=45.0, W=70.0, H=80.0, mass=0.35)            # ESTIMATE DC contactor 48 V 100 A class
ROBOPAD = dict(W=90.0, H=56.0, D=42.0, mass=0.3, pitch=(74.0, 56.0))   # SOURCED Roboteq RPCOL90-100 (mass ESTIMATE)

# ---------------------------------------------------------------- coffee backpack
COF_SH = 690.0                                                 # shelf top (lead 2026-10-03: +80 mm so the right arm reaches the shuttle; sim updated)
COF_X = -225.0                                                 # sim machine/spout x
COF_Y_IN, COF_Y_OUT = -100.0, -240.0                           # sim shuttle: under spout / out
COF_STACK = (-105.0, -270.0)
COF_STACK_Z = 120.0
INISSIA = dict(W=119.0, D=320.0, H=229.0, mass=2.4)             # SOURCED De'Longhi EN80 119 x 320 x 229
INI_X0, INI_Y0 = COF_X - 60.0, -130.0                          # machine envelope: x -285..-166, y -130..190 (front = spout side, -y)
INI_RECESS = (COF_SH + 15.0, COF_SH + 125.0, -130.0, -53.0)                     # ESTIMATE cup recess under the spout (z0, z1, y0, y1)
SHUTTLE_PLATE_Z = COF_SH + 30.0                                        # proposed (sim 0.70 m): cup <= 85 mm under the real spout
P16 = dict(closed=197.0, stroke=150.0, w=20.0, h=26.0, mass=0.125)  # SOURCED Actuonix P16-150 (section ESTIMATE)
MGN12 = dict(rail_w=12.0, rail_h=8.0, car_w=27.0, car_l=45.4, H=13.0)   # HIWIN MGN12H (catalogue values, SECONDARY)

# ---------------------------------------------------------------- chest kitting tray (sim BUF_Z, BUFFER_SLOTS)
BUF_Z = 950.0
BUF_X = 190.0
BUF_YS = [110.0, 185.0, 260.0]
POCKET, WALL, POCKET_H, CHAMF = 60.0, 9.0, 60.0, 16.0

# ---------------------------------------------------------------- loads
GRAV = 9.81
ARM_PAYLOAD_PEAK = 6.0                                         # SOURCED OpenArm 2.0 peak payload incl. end effector
ARM_PAYLOAD_NOM = 4.1
PRODUCT_PAYLOAD_ARM = 3.0                                      # product rating per arm (object only; gripper is in the arm mass), software-limited
TRAY_PAYLOAD = 6 * 0.35                                        # 6 flasks in the chest tray
MASS_LIMIT, MASS_TARGET = 100.0, 90.0                          # Tracer manual p.3 (binding) / 10 % margin
J_PEAK = {"J1": 40.0, "J2": 40.0}                              # DM-J8009P peak torques used in the sim (SOURCED sim/Enactic)
BRAKE_G, BUMP_G = 0.5, 2.0


def deg(x):
    return math.radians(x)
