"""Giorgio AMR (own base), design rev B (no waist joint), electrical inputs rev B2 (VERIFICATION.md): engineering check calculations -> amr/CALC.md
(system python3 has no numpy here: run with ../cad/.env/bin/python amr_calc.py)

Reads (never writes) amr_params.py, out/parts.json, out/integration.json, out/stl/*.stl and ../cad/out/stl/*.stl (plan radii,
bounding boxes). python3 + numpy only (STL files are parsed here, no trimesh needed).
Run:  cd ~/giorgio_sim/amr && ../cad/.env/bin/python amr_calc.py   (any python3 with numpy)

Rev B (owner decision 2026-10-05): NO waist yaw joint. The deck (10 mm 6082, z 343..353) is the fixed superstructure flange;
the superstructure is fixed at yaw 0, so the torso can no longer turn the arms toward the load: the worst arm poses are
checked forward, to each side and to the rear. Rotation = the whole robot rotating in place on the drive wheels.

Every input is registered with a tag:
  SOURCED   = manufacturer datasheet / page (URL)
  SECONDARY = distributor / catalogue / CONTEXT.md decision value taken from a manufacturer source
  CAD       = computed from out/parts.json / out/integration.json / STL files (CAD masses, ESTIMATE where the part envelope is an estimate)
  ESTIMATE  = our engineering estimate
  ASSUMED   = assumption to be confirmed (supplier question or test)
Frame: origin on the floor at the base centre, x forward, y left, z up; mm / kg / N / s unless stated.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import amr_params as P  # noqa: E402

G = 9.81
PARTS = json.load(open(HERE / "out" / "parts.json"))
INTEG = json.load(open(HERE / "out" / "integration.json"))
SUP_STL = HERE.parent / "cad" / "out" / "stl"
BASE_STL = HERE / "out" / "stl"


# =============================================================================== STL helpers (numpy only)
def read_stl(path):
    """vertices (n, 3) of a binary or ASCII STL."""
    b = Path(path).read_bytes()
    n = int.from_bytes(b[80:84], "little") if len(b) >= 84 else 0
    if len(b) == 84 + 50 * n and n > 0:
        a = np.frombuffer(b, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
        return a["v"].reshape(-1, 3).astype(float)
    t = b.decode(errors="ignore").split()
    return np.array([[float(t[i + 1]), float(t[i + 2]), float(t[i + 3])] for i, w in enumerate(t) if w == "vertex"])


def load_sup_meshes():
    out = {}
    for n, m, c in INTEG["items"]:
        f = SUP_STL / f"{n}.stl"
        if f.exists():
            out[n] = read_stl(f)
    return out


def load_base_meshes():
    out = {}
    for p in PARTS:
        if p["group"] == "base" and p.get("category") != "harness":
            f = BASE_STL / p["file"]
            if f.exists():
                out[p["name"]] = read_stl(f)
    return out


SUP_V = load_sup_meshes()
BASE_V = load_base_meshes()

# =============================================================================== input registry
INPUTS = []      # (name, value, unit, tag, source)


def inp(name, value, unit, tag, source=""):
    INPUTS.append((name, value, unit, tag, source))
    return value


SRC_NS3 = P.SOURCES["nanoscan3"]
SRC_SWD = P.SOURCES["swd125"]
SRC_DDR = P.SOURCES["ddr480"]
SRC_RP = P.SOURCES["robopad"]
SRC_BATT = "https://discoverbattery.com/products/search/dlp-gc2-48v"
SRC_DMAN = "Discover 805-0027 Rev N Table 3-1/3-4/3-9 (docs/fonti), VERIFICATION D8/D9/D10"
SRC_PILZ = "Pilz PNOZmulti 2 Technical Catalogue 1006421-EN-01 p.26-28 (docs/fonti), VERIFICATION P8"
SRC_NPB750 = "Mean Well NPB-750-SPEC (docs/fonti), VERIFICATION M13"
SRC_RP13 = "Roboteq RoboPad datasheet v1.3 p.15 (docs/fonti), VERIFICATION R1"
SRC_SWDM = "ez-Wheel SWD user manual v2.0.2 (docs/fonti)"
CTX = "amr/CONTEXT.md"
ARCH = "electrical/ARCHITECTURE.md §3"

# geometry / supports
WY = inp("drive wheel contact |y|", P.WHEEL_Y, "mm", "ESTIMATE", "amr_params.WHEEL_Y (design)")
WR = inp("drive wheel radius", P.WHEEL_D / 2, "mm", "SOURCED", SRC_SWD + " (D125)")
CX, CY = P.CASTER_XY
inp("castor swivel axis (x, y)", f"(±{CX:g}, ±{CY:g})", "mm", "ESTIMATE", "amr_params.CASTER_XY (design)")
TRAIL = inp("castor trail, worst case inward", 35.0, "mm", "ASSUMED", "D100 swivel castor class; confirm on the chosen castor drawing")
SCAN_Z = inp("scan plane height", P.SCAN_Z, "mm", "SOURCED", "amr_params.SCAN_Z (tower roof + 50.5 mm SOURCED plane)")
inp("superstructure yaw", 0.0, "deg", "CAD", "rev B: no waist joint, superstructure bolted to the deck (out/integration.json)")

# payload / poses (validated poses of cad/validate.py + rev B side/rear poses)
M_HAND = inp("payload per hand (product rating)", 3.0, "kg", "SECONDARY", "cad/params.py PRODUCT_PAYLOAD_ARM")
M_TRAY = inp("tray payload (6 flasks)", 2.1, "kg", "SECONDARY", "cad/params.py TRAY_PAYLOAD")
P_TRAY = np.array([190.0, 0.0, 990.0])
inp("tray payload CoG", "(190, 0, 990)", "mm", "SECONDARY", "cad/params.py BUF_X, BUF_Z + 40")
SH_Y = inp("shoulder |y| (OpenArm link2 CoG)", 162.5, "mm", "CAD", "integration.json openarm_*_link2")
REACH = inp("hand horizontal reach from the shoulder, worst pose", 550.0, "mm", "SECONDARY", "cad/validate.py worst pose (0.55 m)")
ARM_SHIFT = inp("arm links shift toward the reach direction, worst pose", 150.0, "mm", "SECONDARY", "cad/validate.py worst pose (+150 mm x)")
P_HAND_WORK = np.array([300.0, 150.0, 1030.0])
inp("hand payload, nominal work pose", "(300, ±150, 1030)", "mm", "SECONDARY", "cad/validate.py work pose")
inp("hand payload, worst forward pose", "(550, ±250, 1100)", "mm", "SECONDARY", "cad/validate.py worst pose")
inp("hand payload, worst side pose (both arms to one side)", f"near arm (0, ±{SH_Y + REACH:.0f}, 1100), far arm across the chest (250, ±300, 1100)",
    "mm", "ESTIMATE", "rev B: same 0.55 m reach to the side; the far arm crosses in front of the torso")
inp("hand payload, worst rear pose", "(-550, ±250, 1100)", "mm", "ESTIMATE",
    "rev B: mirror of the validated forward pose; real rear reach may be limited by joint limits / coffee module (conservative)")
FINGER = inp("gripper/fingers beyond the payload point", 50.0, "mm", "ESTIMATE", "")
M_HARN_F = inp("harness + small parts, base (harness parts are 0 kg in parts.json)", 3.0, "kg @ z 200", "ASSUMED", "48 V/24 V cables, lugs, glands")
M_HARN_S = inp("harness on the superstructure (arm buses, Ethernet, safety loop)", 0.5, "kg @ z 450", "ASSUMED", "")

# drive
SWD_TN = inp("SWD 125 4:1 nominal torque (wheel)", P.SWD["T_nom"], "Nm", "SOURCED", SRC_SWD)
SWD_TP = inp("SWD 125 4:1 peak torque (wheel)", P.SWD["T_peak"], "Nm", "SOURCED", SRC_SWD)
SWD_RPM = inp("SWD 125 4:1 nominal speed", P.SWD["rpm_nom"], "rpm", "SOURCED", SRC_SWD)
SWD_LOAD = inp("SWD static load rating per wheel", P.SWD["load_kg"], "kg", "SOURCED", SRC_SWD)
SWD_P = inp("SWD S1 power", P.SWD["P_nom"], "W", "SOURCED", SRC_SWD)
MU = inp("tyre/floor friction PU on concrete", 0.5, "-", "ASSUMED", "dry, clean, sealed concrete")
CRR_D = inp("rolling resistance drive wheels", 0.015, "-", "ASSUMED", "PU 80 ShA on concrete")
CRR_C = inp("rolling resistance castors (incl. swivel scrub)", 0.025, "-", "ASSUMED", "D100 PU castor")
ETA_DRV = inp("traction efficiency motor+gear+drive", 0.75, "-", "ASSUMED", "")
ETA_DC = inp("DC-DC efficiency DDR-480C-24", 0.92, "-", "SOURCED", "DDR-480-SPEC p.2 'EFFICIENCY (Typ.) 92%' (VERIFICATION M3)")
A_SS1 = inp("SS1-t stop ramp (normal & E-stop), SWD quick-stop ramp 604Ah (non-safe)", 1.5, "m/s²", "ASSUMED", "design value; the SWD has no safety-rated SS1 (VERIFICATION E4)")
T_STO = inp("SS1-t: PNOZ STO delay after the stop request (traction)", 1.2, "s", "ESTIMATE",
            "design choice rev B2: >= ramp from 1.5 m/s + t_logic + t_drive (1.094 s) + margin; VERIFICATION E4 asks >= 1.1 s")
T_SLS = inp("SWD SLS[1] time to velocity monitoring t_SLS (6691h)", 1.0, "s", "ESTIMATE",
            SRC_SWDM + " p.109-110 (configurable U16 ms; value is our design choice)")
A_CMD = inp("commanded accel/decel limit (target)", 1.5, "m/s²", "ASSUMED", "brief / old Ranger Mini limit")
SLOPE6, SLOPE8 = 0.06, 0.08
inp("ramps", "6 % (design), 8 % (check)", "-", "ASSUMED", "brief")

# castor springs
TRAVEL = inp("castor spring travel (total)", 15.0, "mm", "ASSUMED", "suspension castor D100 class; confirm on drawing")
FLOOR_DZ = inp("floor unevenness under one castor (35 % rule)", 5.0, "mm", "ASSUMED", "industrial floor; thresholds up to 20 mm (amr_params) checked as info")
PITCH_MAX = inp("max body pitch at commanded accel (scan-plane tilt)", 1.0, "deg", "ASSUMED", "1° -> 52 mm plane drop at 3 m")

# energy
E_BATT = inp("battery energy (2 packs)", 2 * P.BATT["kWh"], "kWh", "SOURCED", SRC_BATT)
USABLE = inp("usable fraction (energy above the 48 V application cut-off)", 0.88, "-", "ESTIMATE", "rev B1 0.9 ASSUMED; the 48 V LVCO (VERIFICATION D10) leaves the last few % of an LFP pack unused")
V_NOM = inp("bus nominal", P.BATT["V"], "V", "SOURCED", SRC_BATT)
V_MIN = inp("bus minimum under peak load (worst for peak current)", 44.0, "V", "ASSUMED", "LFP 16s near the cut-off under peak; bus range 40-58.4 V")
V_LVCO = inp("application low-voltage cut-off K0V (sustained / average currents use this)", 48.0, "V", "SOURCED", SRC_DMAN + ": 'Low Voltage Disconnect Recommended 48.0 V'")
I_PACK_C = inp("pack Max Continuous Discharge Current (5 back-to-back full cycles, thermal)", 15.0, "A", "SOURCED", SRC_DMAN)
I_PACK_1H = inp("pack Max Discharge Current (1 hour)", 58.0, "A", "SOURCED", SRC_DMAN)
I_PACK_P = inp("pack Peak Discharge Current (10 s)", 90.0, "A RMS", "SOURCED", SRC_DMAN)
I_BMS_TRIP = inp("pack BMS over-discharge trip", "> 58 A for 10 s", "-", "SOURCED", SRC_DMAN + " Table 3-4")
inp("pair ratings (linear scaling, no share factor)", "30 A continuous / 116 A 1 h / 180 A 10 s", "-", "SOURCED", SRC_DMAN + " Table 3-9 (VERIFICATION D11)")
DDR_I, DDR_IP = inp("DDR-480C-24 rated current", 20.0, "A", "SOURCED", SRC_DDR), inp("DDR-480C-24 peak current (5 s)", 30.0, "A", "SOURCED", SRC_DDR)
OA_TYP, OA_CONT, OA_PK = (inp("OpenArm per arm typ", 70.0, "W", "SECONDARY", ARCH), inp("OpenArm per arm cont", 360.0, "W", "SECONDARY", ARCH),
                          inp("OpenArm per arm peak (5 s)", 720.0, "W", "SECONDARY", ARCH))
KA_TYP = inp("Kassow Edge per arm typ (active)", 350.0, "W", "ASSUMED", "not found in a datasheet; ask Kassow")
KA_IDLE = inp("Kassow Edge per arm idle (brakes on, controller on)", 40.0, "W", "ASSUMED", "")
KA_PK = inp("Kassow Edge per arm peak", 1000.0, "W", "ASSUMED", "")
JET = inp("Jetson Orin NX average", 25.0, "W", "SECONDARY", ARCH + " (10-40 W)")
JET_MAX = inp("Jetson Orin NX max", 40.0, "W", "SECONDARY", ARCH)
SCN = inp("2 x nanoScan3 Pro I/O at max output load", 2 * 15.9, "W", "SOURCED", "SICK nanoScan3 I/O OI 8024596 p.130: 'With maximum output load Typ. 15.9 W' (VERIFICATION S9)")
SAFE = inp("Pilz PNOZ m B0 + 2x EF 4DI4DOR + ES ETH + bleed resistors + relays", 16.0, "W", "ESTIMATE", "EF/ES ~1 W each SOURCED (VERIFICATION P13); B0 + relay coils + 7 x 0.26 W bleed ESTIMATE")
NETCAM = inp("Ethernet switch + cameras (Gemini 336L, Insta360)", 12.0, "W", "ASSUMED", "")
SWD_STBY = inp("2 x SWD standby electronics", 10.0, "W", "ASSUMED", "")
DC_NL = inp("DC-DC no-load losses (all converters)", 10.0, "W", "ASSUMED", "")
COFFEE = inp("coffee module (barista, when brewing)", 300.0, "W", "SECONDARY", ARCH)
COFFEE_PK = inp("coffee module peak via its DDR-480C-24", 720.0, "W", "SOURCED", SRC_DDR + " (30 A 5 s x 24 V, converter-limited)")
ARM_CABLE_L = inp("arm 24 V feed length, centre-bay DC-DC -> shoulder (one way)", 1.3, "m", "ESTIMATE", "centre bay z ~100 -> deck grommet -> column -> shoulder z 1278")
ARM_CABLE_A = inp("arm 24 V feed cross-section", 4.0, "mm²", "ASSUMED", "to fix in amr/electrical/")

# charging
I_CHG = inp("NPB-750-48 CC current (rev B2 charger, EMC Class B)", 11.3, "A", "SOURCED", SRC_NPB750)
I_CHG_ALT = inp("NPB-1700-48 CC current (option, EMC Class A radiated -> dock EMC test)", 25.0, "A", "SOURCED", "Mean Well NPB-1700-SPEC p.2 (VERIFICATION M11/M13)")
V_CHG = inp("charging voltage (mid CC)", 54.0, "V", "ASSUMED", "LFP 16s CC phase")
P_DOCK = inp("robot consumption while docked", 150.0, "W", "ASSUMED", "brief")
RP_I = inp("RoboPad continuous rating", 60.0, "A", "SOURCED", SRC_RP13 + ": 'Continuous Current 60 A' (75 A only 80 s on / 60 s off)")
I_CHG_PACK = inp("pack Max Continuous Charge Current", 15.0, "A", "SOURCED", SRC_DMAN)
T_CHG_MAX = inp("acceptable 20 -> 90 % charge time (overnight, single shift 8-10 h/day)", 8.0, "h", "ASSUMED", "ce/RISK_ASSESSMENT limits: 8-10 h/day operation")

# safety
T_SCAN = inp("nanoScan3 response time", 0.070, "s", "SOURCED", SRC_NS3 + " (70 ms; multiple sampling > default adds time -> recompute in Safety Designer)")
Z_SUP = inp("nanoScan3 protective field supplement", 65.0, "mm", "SOURCED", SRC_NS3)
NS_RANGE = inp("nanoScan3 protective field range", 3000.0, "mm", "SOURCED", SRC_NS3)
Z_REFL = inp("reflector supplement", 0.0, "mm", "ASSUMED", "no retro-reflectors within the field plane; add per SICK OI if present (dock AprilTag reflector is at z 380-500, above the plane)")
T_LOG = inp("PNOZmulti 2 logic, worst case through the EF 4DI4DOR relays", 0.054, "s", "SOURCED", SRC_PILZ + " (B0 33 ms, EF 41 ms, relay path 54 ms)")
T_DRV = inp("SWD reaction to the start of the ramp / STO", 0.040, "s", "ASSUMED", "not published (VERIFICATION E9): 2 x the rev B1 20 ms; measure SFRT in TP-01 and keep >= 2x margin")
BRK_F = inp("braking-distance factor (wear, floor)", 1.1, "-", "ASSUMED", "ISO 3691-4 asks to account for worst conditions")
K_HUM = inp("human approach speed K (ISO 13855)", 1600.0, "mm/s", "SOURCED", "EN ISO 13855 (horizontal approach)")
T_ARM_STOP = inp("arm stopping time (OpenArm: contactor drop-out + coast; certified arm: its stop time)", 0.20, "s", "ASSUMED",
                 "measure per EN ISO 13855 before use; OpenArm has no brakes")

# carry mode
GRIP_F = inp("OpenArm gripper grip force", 50.0, "N", "ASSUMED", "not published; measure")
MU_GRIP = inp("grip pad friction on cup", 0.4, "-", "ASSUMED", "rubber pad on ceramic/paper")
MU_TRAY = inp("cup/flask on tray friction", 0.3, "-", "ASSUMED", "")

# structure
E_AL = inp("E 6082-T6", 70e3, "MPa", "SOURCED", "EN 485-2 / EN 755-2 typical")
RP_AL = inp("Rp0.2 6082-T6 plate 10 mm", 240.0, "MPa", "SOURCED", "EN 485-2 (6 < t <= 12.5 mm, min 240 MPa)")
RP_ST = inp("ReH S355MC", 355.0, "MPa", "SOURCED", "EN 10149-2")
DECK_SPAN = inp("deck span between spines (c/c)", 2 * P.SPINE_Y, "mm", "CAD", "amr_params.SPINE_Y (spines at ±137, x ±262; end posts at (±360, ±155))")
COL_X = inp("column foot centre x (160 x 160 x 20, 8 x M6 on a ±62 mm grid)", -60.0, "mm", "SECONDARY", "cad/params.py COL_X, cad/model.py column()")
FOOT_B = 62.0
B_ROW = inp("deck effective strip width per foot bolt row (3 rows at 62 mm pitch)", 100.0, "mm", "ESTIMATE",
            "one-way slab, concentrated load spread ~ 0.5 x span shared by 3 rows")
M6_PRELOAD = inp("M6 8.8 preload in tapped 6082 (deck)", 7000.0, "N", "ASSUMED", "~ 10 Nm, μ 0.14; thread engagement ≥ 1.5 d (≥ 9 mm in the 10 mm deck) or helicoil")
COFFEE_UPR = [(-228.0, -118.0), (-228.0, 175.0)]
inp("coffee uprights on the deck", "(-228, -118), (-228, 175)", "mm", "CAD", "integration.json P22_coffee_upright_0/1")

# =============================================================================== results registry
RES = []        # (section, check, value, limit, status)


def res(sec, check, value, limit, status):
    RES.append((sec, check, value, limit, status))
    return status


def st(ok, warn=False):
    return "PASS" if ok else ("WARN" if warn else "FAIL")


MD = []


def md(s=""):
    MD.append(s)


def table(head, rows):
    md("| " + " | ".join(head) + " |")
    md("|" + "|".join("---" for _ in head) + "|")
    for r in rows:
        md("| " + " | ".join(str(x) for x in r) + " |")
    md()


def f(x, n=2):
    return f"{x:.{n}f}"


# =============================================================================== 1. mass & CoG
def bbox_of(v):
    return [float(v[:, 0].min()), float(v[:, 0].max()), float(v[:, 1].min()), float(v[:, 1].max()), float(v[:, 2].min()), float(v[:, 2].max())]


base = [(p["name"], p["mass_kg"] * p.get("qty", 1), np.array(p["com_mm"]), p["bbox_mm"]) for p in PARTS if p["group"] in ("base", "waist")]
base.append(("harness base (ASSUMED)", M_HARN_F, np.array([0.0, 0.0, 200.0]), None))
sup = [(n, m, np.array(c), bbox_of(SUP_V[n]) if n in SUP_V else None) for n, m, c in INTEG["items"]]
sup += [(p["name"], p["mass_kg"] * p.get("qty", 1), np.array(p["com_mm"]), p["bbox_mm"]) for p in PARTS if p["group"] == "waist_rot"]   # empty in rev B
sup.append(("harness superstructure (ASSUMED)", M_HARN_S, np.array([0.0, 0.0, 450.0]), None))
COFFEE_PREFIX = ("E11", "E12", "E13", "P21", "P22", "P23", "P24", "P25", "P26", "P30", "P31", "S07", "S08", "S09", "S10", "SH06")


def mc(rows):
    m = sum(r[1] for r in rows)
    return m, sum(r[1] * r[2] for r in rows) / m


m_base, c_base = mc(base)
m_sup0, c_sup0 = mc(sup)

FAR = np.array([250.0, 300.0, 1100.0])
POSES = {
    "empty": ("arms home, no payload", None, None),
    "work": ("arms home, 2x3 kg at (300, ±150, 1030), tray 2.1 kg", None, None),
    "fwd": ("arms +150 mm fwd, 2x3 kg at (550, ±250, 1100), tray 2.1 kg", np.array([ARM_SHIFT, 0, 0]),
            [np.array([550.0, 250.0, 1100.0]), np.array([550.0, -250.0, 1100.0])]),
    "side_L": (f"both arms to the left (+150 mm y), 3 kg at (0, {SH_Y + REACH:.0f}, 1100) + 3 kg at (250, 300, 1100), tray 2.1 kg",
               np.array([0, ARM_SHIFT, 0]), [np.array([0.0, SH_Y + REACH, 1100.0]), FAR]),
    "side_R": ("mirror of side_L (to the right)", np.array([0, -ARM_SHIFT, 0]),
               [np.array([0.0, -(SH_Y + REACH), 1100.0]), FAR * [1, -1, 1]]),
    "rear": ("arms -150 mm rear, 2x3 kg at (-550, ±250, 1100), tray 2.1 kg", np.array([-ARM_SHIFT, 0, 0]),
             [np.array([-550.0, 250.0, 1100.0]), np.array([-550.0, -250.0, 1100.0])]),
}
WORST = ("fwd", "side_L", "side_R", "rear")


def sup_rows(pose):
    """superstructure rows (yaw 0, fixed) for a pose."""
    _, shift, hands = POSES[pose]
    rows = []
    for n, m, c, b in sup:
        c = c.copy()
        if shift is not None and n.startswith("openarm_"):
            c = c + shift
            b = None if b is None else [b[0] + shift[0], b[1] + shift[0], b[2] + shift[1], b[3] + shift[1], b[4], b[5]]
        rows.append((n, m, c, b))
    if pose == "work":
        hands = [P_HAND_WORK, P_HAND_WORK * [1, -1, 1]]
    if hands is not None:
        rows += [("hand payload L", M_HAND, hands[0], None), ("hand payload R", M_HAND, hands[1], None),
                 ("tray payload", M_TRAY, P_TRAY, None)]
    return rows


SUP = {k: mc(sup_rows(k)) for k in POSES}


def total_cog(pose):
    ms, cs = SUP[pose]
    m = m_base + ms
    return m, (m_base * c_base + ms * cs) / m


def hand_points(pose):
    _, _, hands = POSES[pose]
    if pose == "work":
        return [P_HAND_WORK, P_HAND_WORK * [1, -1, 1]]
    return hands or []


ARM_REACH = inp("arm hazard radius from the base centre (max over poses, hand + fingers)",
                max(math.hypot(h[0], h[1]) + FINGER for k in POSES for h in hand_points(k)), "mm", "ESTIMATE", "side pose governs")


# =============================================================================== plan geometry (swept radii, overhang)
def plan_radius(vs):
    best = (0.0, None, None)
    for n, v in vs.items():
        r = np.hypot(v[:, 0], v[:, 1])
        i = int(r.argmax())
        if r[i] > best[0]:
            best = (float(r[i]), n, v[i])
    return best


R_BASE, R_BASE_PART, R_BASE_PT = plan_radius(BASE_V)
R_SUP, R_SUP_PART, R_SUP_PT = plan_radius(SUP_V) if SUP_V else (INTEG["rotating_swept_radius_mm"], "integration.json", None)
inp("base swept radius (max plan radius of all base STL vertices)", round(R_BASE, 1), "mm", "CAD", f"out/stl ({R_BASE_PART})")
inp("superstructure swept radius (arms home)", round(R_SUP, 1), "mm", "CAD", f"cad/out/stl ({R_SUP_PART}); integration.json {INTEG['rotating_swept_radius_mm']}")
R_SWEPT = max(R_BASE, R_SUP)
K05 = next(p for p in PARTS if p["name"] == "K05_rubber_edge")["bbox_mm"]
BX, BY = K05[1], K05[3]


def outside_outline(x, y):
    """distance of plan point(s) outside the chamfered base outline (K05 rubber edge), 0 if inside."""
    ax, ay = np.abs(x), np.abs(y)
    dx = np.maximum(ax - BX, 0.0)
    dy = np.maximum(ay - BY, 0.0)
    # chamfer line: ax + ay <= BX + BY - CHAMF ; distance = excess / sqrt 2
    dc = np.maximum((ax + ay - (BX + BY - P.CHAMF)) / math.sqrt(2), 0.0)
    return np.maximum(np.maximum(dx, dy), dc)


def overhang():
    best = (0.0, None, None)
    for n, v in SUP_V.items():
        d = outside_outline(v[:, 0], v[:, 1])
        i = int(d.argmax())
        if d[i] > best[0]:
            best = (float(d[i]), n, v[i])
    return best


OVH, OVH_PART, OVH_PT = overhang()


# =============================================================================== 2. tipping
def hull(pts):
    pts = sorted(map(tuple, pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


def ray_dist(poly, p, u):
    """distance from p (inside) along unit u to the polygon boundary; negative if p is outside."""
    best = 1e9
    n = len(poly)
    inside = True
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        e = b - a
        if e[0] * (p[1] - a[1]) - e[1] * (p[0] - a[0]) < 0:
            inside = False
        den = u[0] * (-e[1]) - u[1] * (-e[0])
        if abs(den) < 1e-12:
            continue
        r = a - p
        t = (r[0] * (-e[1]) - r[1] * (-e[0])) / den
        s = (u[0] * r[1] - u[1] * r[0]) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9:
            best = min(best, t)
    return best if inside else -1.0


def support(mode):
    """6 contacts. mode: x / y / radial = direction of the 35 mm inward castor trail."""
    pts = [(0.0, WY), (0.0, -WY)]
    for sx in (1, -1):
        for sy in (1, -1):
            x, y = sx * CX, sy * CY
            if mode == "x":
                x -= sx * TRAIL
            elif mode == "y":
                y -= sy * TRAIL
            elif mode == "radial":
                r = math.hypot(x, y)
                x, y = x * (1 - TRAIL / r), y * (1 - TRAIL / r)
            pts.append((x, y))
    return hull(np.array(pts))


SUPPORTS = {k: support(k) for k in ("none", "x", "y", "radial")}
PHI = np.arange(0, 360, 1.0)


def a_tip(pose, phi_deg, sup_modes=("x", "y", "radial")):
    """tip acceleration [m/s²] toward direction phi (inertial load toward phi): worst over castor trail cases."""
    m, c = total_cog(pose)
    u = np.array([math.cos(math.radians(phi_deg)), math.sin(math.radians(phi_deg))])
    d = min(ray_dist(SUPPORTS[s], c[:2], u) for s in sup_modes)
    return G * d / c[2]


TIP = {pose: np.array([a_tip(pose, ph) for ph in PHI]) for pose in POSES}


def dir_min(arr, centre, half=10.0):
    idx = [int(round((centre + d) % 360)) for d in np.arange(-half, half + 1)]
    return float(arr[idx].min())


# =============================================================================== 3. load split, sprung castors
def pitch_solve(m, c, a_long, Fi, k, slope_deg=0.0):
    """rigid drive axle at x=0; body pitch theta (rad, + nose down) on 4 sprung castors at x=±CX.
    a_long: decel (+) produces nose-down moment. returns theta, F_front(each), F_rear(each), N_drive_total."""
    th_lim = (TRAVEL / 1000) / (CX / 1000)
    gN = G * math.cos(math.radians(slope_deg))
    M_app = m * gN * c[0] / 1000 + m * (a_long + G * math.sin(math.radians(slope_deg))) * c[2] / 1000
    def forces(th):
        d = (CX / 1000) * th                       # front compression increase (m)
        def F(dd):
            if dd > (TRAVEL / 1000) * 0.5:         # bottoming: hard stop, very stiff (installed at mid travel)
                return max(0.0, Fi + k * (TRAVEL / 1000) * 0.5 + 50 * k * (dd - TRAVEL / 2000))
            return max(0.0, Fi + k * dd)
        return F(d), F(-d)
    def mom(th):
        ff, fr = forces(th)
        return 2 * (CX / 1000) * (ff - fr) - M_app
    lo, hi = -0.5, 0.5
    for _ in range(200):
        mid = (lo + hi) / 2
        if mom(mid) > 0:
            hi = mid
        else:
            lo = mid
    th = (lo + hi) / 2
    ff, fr = forces(th)
    return th, ff, fr, m * gN - 2 * (ff + fr), th_lim


# =============================================================================== build report
def main():
    md("# Giorgio AMR (own base) - engineering checks, design rev B (no waist joint)")
    md()
    md("Generated by `amr/amr_calc.py` from `amr_params.py`, `out/parts.json`, `out/integration.json` and the STL files "
       "(`out/stl`, `../cad/out/stl`). Quasi-static hand calculations for design review; they do not replace the supplier "
       "confirmations listed at the end, the SISTEMA/Safety Designer calculations or the type tests. Every input is tagged "
       "(table at the end). Frame: floor, base centre, x forward, y left, z up.")
    md()
    md("**Rev B (owner decision 2026-10-05): no waist yaw joint.** The 10 mm 6082 deck (z 343..353) is the fixed superstructure "
       "flange at the old adapter height; the superstructure is fixed at yaw 0. Consequences for the checks: (a) tipping is "
       "evaluated at yaw 0 only, but because the torso can no longer turn the arms toward the load, the worst arm poses are "
       "checked **forward, to the left, to the right and to the rear**; (b) all yaw motion is the whole robot rotating in place, so "
       "the rotate-in-place field and yaw-rate limit use the swept radius of the whole robot (base + superstructure overhang); "
       "(c) the waist actuator, crossed-roller bearing, coupling and waist field checks of rev A are removed; (d) the Jetson and the "
       "arm DC-DCs sit in the base centre bay. Section numbers changed from rev A (old §5 waist removed).")
    md()

    # ------------------------------------------------------------------ 1
    md("## 1. Mass and CoG")
    md()
    mi, ci = INTEG["base_fixed_kg"], INTEG["base_fixed_com_mm"]
    rows = [["base (parts.json group base) + harness 3 kg ASSUMED", f(m_base, 1), np.round(c_base, 0).tolist(), f"integration.json w/o harness: {mi} kg {ci}"]]
    rows.append(["superstructure (fixed, yaw 0) + harness 0.5 kg ASSUMED", f(m_sup0, 1), np.round(c_sup0, 0).tolist(),
                 f"integration.json: {INTEG['superstructure_kept_kg']} kg {INTEG['superstructure_com_mm']}"])
    arms_m = sum(m for n, m, c, b in sup if n.startswith("openarm_"))
    rows.append(["  of which OpenArm links (both arms)", f(arms_m, 2), "", "integration.json (cad mass_properties arms)"])
    for k, (d, _, _) in POSES.items():
        ms, cs = SUP[k]
        rows.append([f"superstructure, pose **{k}**: {d}", f(ms, 1), np.round(cs, 0).tolist(), ""])
    table(["item", "mass kg", "CoG mm", "note"], rows)
    rows = []
    for k in POSES:
        m, c = total_cog(k)
        rows.append([k, f(m, 1), f"{c[0]:.0f}", f"{c[1]:.0f}", f"{c[2]:.0f}", f"{math.hypot(c[0], c[1]):.0f}"])
    md("Whole robot per pose:")
    md()
    table(["pose", "total kg", "CoG x mm", "CoG y mm", "CoG z mm", "CoG r_xy mm"], rows)
    m_worst = total_cog("fwd")[0]
    res("1 Mass", "total mass, fully loaded", f"{m_worst:.1f} kg (empty {total_cog('empty')[0]:.1f})", "2 x 250 kg wheel rating", "PASS")

    # ------------------------------------------------------------------ 2
    md("## 2. Tipping (quasi-static, superstructure fixed at yaw 0)")
    md()
    md(f"Support polygon: drive wheels (0, ±{WY:g}) + castor contacts at (±{CX:g}, ±{CY:g}) with the castor contact displaced "
       f"{TRAIL:g} mm inward (ASSUMED trail) in x, in y or radially - worst of the three for every direction. "
       "a_tip(φ) = g·d_edge(φ)/h, d_edge = distance from the CoG ground projection to the polygon edge along φ (exact for a "
       "quasi-static inertial load; φ = direction the robot tips = direction of the inertial load: decel while driving forward = "
       "φ 0°, accel forward = φ 180°, lateral = 90°/270°). Sprung castors are treated as rigid supports at the tip limit "
       "(springs bottom out on their hard stop - see §3 for the drive-wheel unloading that happens earlier). Each direction is the "
       "minimum over ±10°. Without the waist the arms cannot be turned toward the load, so every arm pose (forward, side, rear) "
       "is combined with every direction of acceleration.")
    md()
    rows = []
    lim = {}
    for k in POSES:
        A = TIP[k]
        fwd, back = dir_min(A, 0), dir_min(A, 180)
        left, right = dir_min(A, 90), dir_min(A, 270)
        allm = float(A.min())
        ip = int(np.argmin(A))
        lim[k] = dict(decel=fwd / 2, accel=back / 2, lat=min(left, right) / 2, any=allm / 2)
        rows.append([k, f(fwd), f(back), f(left), f(right), f"{allm:.2f} (φ {PHI[ip]:.0f}°)", f(fwd / 2), f(back / 2), f(min(left, right) / 2)])
    table(["pose", "a_tip fwd (decel)", "a_tip back (accel)", "a_tip left", "a_tip right", "a_tip any direction",
           "allowed decel (SF 2)", "allowed accel (SF 2)", "allowed lateral (SF 2)"], rows)
    env = {key: min(lim[k][key] for k in WORST) for key in ("decel", "accel", "lat", "any")}
    gov = {key: min(WORST, key=lambda k: lim[k][key]) for key in ("decel", "accel", "lat", "any")}
    lim["worst"] = env
    lim["worst_gov"] = gov
    md("Envelope of the worst arm poses (fwd, side_L, side_R, rear) with SF 2: "
       + ", ".join(f"{key} ≤ {env[key]:.2f} m/s² ({gov[key]})" for key in ("decel", "accel", "lat", "any")) + ".")
    md()
    md("Polygon without trail (info): " + ", ".join(f"({x:.0f}, {y:.0f})" for x, y in SUPPORTS["none"]))
    md()
    lat_raw = min(min(dir_min(TIP[k], 90), dir_min(TIP[k], 270)) for k in WORST)
    res("2 Tipping", "worst lateral a_tip, all worst poses (vs old Ranger Mini 3.65 m/s²)", f"{lat_raw:.2f} m/s² ({gov['lat']})",
        "> 3.65 m/s² (improvement)", st(lat_raw > 3.65, True))
    res("2 Tipping", "commanded accel/decel 1.5 m/s² ≤ a_tip/2 (all worst poses)", f"accel ≤ {env['accel']:.2f} ({gov['accel']}), decel ≤ {env['decel']:.2f} ({gov['decel']})",
        f"≥ {A_CMD}", st(min(env["accel"], env["decel"]) >= A_CMD))
    res("2 Tipping", "lateral (centripetal) 1.5 m/s² ≤ a_tip/2 (all worst poses)", f"≤ {env['lat']:.2f} m/s² ({gov['lat']})", f"≥ {A_CMD}", st(env["lat"] >= A_CMD, True))
    md("Emergency-stop deceleration: see §2b (after §3, it needs the castor preload).")
    md()
    return lim


def sec3(lim):
    md("## 3. Load split with sprung castors")
    md()
    md("Model: two rigid drive wheels on one axle line (x = 0) fix the body height; the body can only pitch about that line. "
       "Each castor force F = F_inst + k·(x·θ), F_inst = installed spring force (preload at installed height). Consequences: "
       "(a) the castor load total is set by the springs, not by the CoG, so the **drive-wheel share is lowest for the lightest "
       "robot (empty)**; (b) longitudinal pitching moments go to the castors (drive load unchanged while all 4 castors touch); "
       "(c) roll cannot happen without lifting a drive wheel, so **lateral moments go entirely to the drive wheels**.")
    md()
    m_e, c_e = total_cog("empty")
    m_w, _ = total_cog("fwd")
    Fi_max = (1 - 2 * 0.35) * m_e * G / 4                     # all 4 castors at F_inst: drive >= 35 % each (empty)
    Fi_tgt = (1 - 2 * 0.40) * m_e * G / 4                     # target 40 % each (amr_params SUSP)
    k_max = (4 * Fi_max - 4 * Fi_tgt) / (FLOOR_DZ / 1000)
    def worst_pitch(k):
        w = 0.0
        for pose in POSES:
            m, c = total_cog(pose)
            for a in (A_CMD, -A_CMD):
                th = pitch_solve(m, c, a, Fi_tgt, k)[0]
                w = max(w, abs(math.degrees(th)))
        return w
    lo, hi = 1e3, 1e7
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if worst_pitch(mid) > PITCH_MAX:
            lo = mid
        else:
            hi = mid
    k_min = hi
    k_rec = min(k_min * 1.2, k_max) if k_min <= k_max else k_max
    md(f"- Empty robot {m_e:.1f} kg, fully loaded {m_w:.1f} kg.")
    md(f"- Drive wheels ≥ 35 % each on flat floor (empty robot) ⇒ F_inst ≤ {Fi_max:.0f} N per castor; target 40 % each "
       f"(amr_params SUSP) ⇒ **F_inst = {Fi_tgt:.0f} N per castor** (castors {100 * 4 * Fi_tgt / (m_e * G):.0f} % of the empty weight).")
    md(f"- Floor unevenness {FLOOR_DZ:g} mm (ASSUMED) under the castors must not push the drive share below 35 %: k ≤ {k_max / 1000:.1f} N/mm.")
    md(f"- Body pitch ≤ {PITCH_MAX:g}° (ASSUMED, scan-plane tilt) at ±{A_CMD} m/s², all poses: k ≥ {k_min / 1000:.1f} N/mm.")
    ok_k = k_min <= k_max
    md(f"- **Spring window {'OK' if ok_k else 'EMPTY'}: k = {k_min / 1000:.1f} .. {k_max / 1000:.1f} N/mm; chosen k = {k_rec / 1000:.1f} N/mm**, "
       f"spring travel {TRAVEL:g} mm ASSUMED, installed at mid travel, hard stop at the end."
       + ("" if ok_k else f" With the window empty the 35 % rule is kept (k = k_max) and the pitch at ±{A_CMD} m/s² is "
          f"{worst_pitch(k_rec):.2f}° (> {PITCH_MAX:g}° target): accept ~{worst_pitch(k_rec):.1f}° (scan plane drops "
          f"{3000 * math.tan(math.radians(worst_pitch(k_rec))):.0f} mm at 3 m - check the field against floor detection) or "
          "require a flatter floor (≤ 4 mm) / reduce F_inst."))
    md()
    res("3 Load split", "castor spring window (35 % drive share vs ≤1° pitch)", f"k {k_min / 1000:.1f}..{k_max / 1000:.1f} N/mm, F_inst {Fi_tgt:.0f} N",
        "window not empty", st(ok_k, True))
    rows = []
    maxFc = 0
    for pose in POSES:
        for a, lab in ((0.0, "static"), (A_CMD, f"decel {A_CMD}"), (-A_CMD, f"accel {A_CMD}"), (-A_CMD, f"accel {A_CMD} + 6 % up")):
            sl = math.degrees(math.atan(SLOPE6)) if "6 %" in lab else 0.0
            m, c = total_cog(pose)
            th, ff, fr, Nd, _ = pitch_solve(m, c, a, Fi_tgt, k_rec, -sl)   # uphill: slope pitches nose up (as accel)
            share = Nd / 2 / (m * G)
            Freq = m * (abs(a) + G * math.sin(math.radians(sl))) + CRR_D * Nd + CRR_C * (m * G - Nd)
            trac = MU * Nd
            rows.append([pose, lab, f"{abs(math.degrees(th)):.2f}", f"{share * 100:.1f}", f"{max(ff, fr):.0f}", f"{Freq:.0f}", f"{trac:.0f}", st(trac >= Freq)])
            maxFc = max(maxFc, ff, fr)
    table(["pose", "case", "pitch °", "drive share per wheel %", "max castor load N", "traction needed N", "μ·N_drive N", "traction"], rows)
    trac_ok = all(r[-1] == "PASS" for r in rows)
    res("3 Load split", "traction μ 0.5 for 1.5 m/s² + 6 % slope (all poses)", "see table", "μ·N_drive ≥ needed", st(trac_ok))
    s0 = min(float(x[3]) for x in rows if x[1] == "static")
    res("3 Load split", "drive share per wheel, flat static (min over poses)", f"{s0:.1f} %", "≥ 35 %", st(s0 >= 35))
    md("**Lateral (roll): inner drive wheel unloading.** N_inner = N_drive/2 − (m·g·|y_cog| + m·a·h)/(2·232 mm). "
       "Inner wheel lift = loss of traction/braking on one side (control loss before the geometric tip limit). The side poses "
       "move the CoG sideways: the lift acceleration is lower toward the side the arms reach to.")
    md()
    rows = []
    a_lift_min, gov = 1e9, ""
    for pose in POSES:
        m, c = total_cog(pose)
        Nd = m * G - 4 * Fi_tgt
        al = (Nd / 2 * 2 * WY / 1000 - m * G * abs(c[1]) / 1000) / (m * c[2] / 1000)
        if al < a_lift_min:
            a_lift_min, gov = al, pose
        rows.append([pose, f"{c[1]:.0f}", f(al), f(al / 2)])
    table(["pose", "CoG y mm", "a_lat at inner drive-wheel lift m/s²", "with SF 2"], rows)
    lim["worst"]["lat_lift"] = a_lift_min / 2
    res("3 Load split", "lateral accel at inner wheel lift /2 ≥ 1.5 (all poses)", f"{a_lift_min / 2:.2f} m/s² ({gov})", "≥ 1.5", st(a_lift_min / 2 >= 1.5, True))
    m, c = total_cog("empty")
    Nd_thr = m * G - 4 * Fi_tgt - k_rec * 0.020
    md(f"Info: one castor on a 20 mm threshold (amr_params limit), empty robot: drive share drops to {100 * Nd_thr / 2 / (m * G):.1f} % per wheel "
       f"(transient; acceptable if speed is limited on thresholds).")
    md()
    Nmax = 0
    for pose in POSES:
        m, c = total_cog(pose)
        Nd = m * G - 4 * Fi_tgt
        Nmax = max(Nmax, Nd / 2 + (m * G * abs(c[1]) + m * A_CMD * c[2]) / 1000 / (2 * WY / 1000))
    res("3 Load split", "max drive wheel load (worst pose + lateral 1.5) vs 250 kg", f"{Nmax / G:.0f} kg", f"≤ {SWD_LOAD:.0f} kg", st(Nmax / G <= SWD_LOAD))
    m, _ = total_cog("fwd")
    Fc_tip = m * G / 2
    md(f"**Castor load rating.** At max commanded accel the most loaded castor carries {maxFc:.0f} N; at the tip limit (springs on the "
       f"hard stop) one castor pair carries up to the whole weight ⇒ {Fc_tip:.0f} N per castor. **Required castor rating ≥ "
       f"{math.ceil(Fc_tip / G / 10) * 10:.0f} kg per castor** (rated dynamic load, 4 km/h), spring end force ≥ {maxFc * 1.5:.0f} N "
       "with a solid hard stop.")
    md()
    F_end = Fi_tgt + k_rec * TRAVEL / 2000
    md(f"Spring force at the end of travel (mid-travel install): {F_end:.0f} N vs {maxFc:.0f} N max at commanded accel + 6 % slope: "
       + ("no bottoming." if F_end >= maxFc else "the most loaded castor reaches its hard stop in the worst case (acceptable: hard stop = rigid support, tip limit unchanged)."))
    md()
    res("3 Load split", "castor rating required", f"≥ {math.ceil(Fc_tip / G / 10) * 10:.0f} kg each", "spec for purchase", "PASS")
    lim["k_rec"], lim["Fi"], lim["k_max"] = k_rec, Fi_tgt, k_max
    return lim


def sec2b(lim):
    """cat 0 braking."""
    a_cat0 = max(MU * (total_cog(k)[0] * G - 4 * lim["Fi"]) / total_cog(k)[0] for k in POSES)
    tipd = lim["worst"]["decel"] * 2
    md("## 2b. Emergency stop deceleration")
    md()
    md("**Rev B2 stop concept: SS1-t** (the SWD has no safety-rated SS1; its default SBC on STO is the internal motor-phase short, not a "
       f"friction brake - SWD manual v2.0.2 p.24/p.106, VERIFICATION E3/E4). On a stop request the PNOZ (t = 0) requests SLS[1] 0.3 m/s and the "
       f"SWD ramps at {A_SS1} m/s² (non-safe quick-stop ramp); the PNOZ removes STO at t = {T_STO:g} s, after the ramp has ended at every "
       f"speed (§7, SS1-t timing). If the ramp fails, the SWD SLS monitoring (t_SLS {T_SLS:g} s, PL d) or the PNOZ timer ({T_STO:g} s, PL e) "
       "end it with STO + phase-short braking. Cat 0 (STO with motion) therefore happens only on power loss or a ramp fault. Cat-0 decel "
       "(phase-short brake, then parking brake) is limited by tyre grip of the drive wheels only (castors free): a_cat0 ≤ μ·N_drive/m "
       f"(highest for the heaviest robot). Tip limit = forward direction, worst arm pose ({lim['worst_gov']['decel']}). "
       "Braking while driving backward loads the rear: compare with the 'back' column of §2 (rear pose).")
    md()
    tipb = min(dir_min(TIP[k], 180) for k in WORST)
    table(["stop", "decel m/s²", "a_tip fwd worst", "SF fwd", "a_tip back worst (reversing)", "SF back", "status"],
          [["SS1 ramp (configured)", f(A_SS1), f(tipd), f(tipd / A_SS1), f(tipb), f(tipb / A_SS1), st(min(tipd, tipb) / A_SS1 >= 2)],
           ["cat 0 (STO + brake), grip-limited μ·N_drive/m (heaviest)", f(a_cat0), f(tipd), f(tipd / a_cat0), f(tipb), f(tipb / a_cat0),
            st(min(tipd, tipb) / a_cat0 >= 2, min(tipd, tipb) / a_cat0 >= 1.2)]])
    sf_ss1 = min(tipd, tipb) / A_SS1
    sf_c0 = min(tipd, tipb) / a_cat0
    res("2 Tipping", "SS1 1.5 m/s² vs a_tip fwd/back (SF 2)", f"{sf_ss1:.2f}", "≥ 2", st(sf_ss1 >= 2))
    res("2 Tipping", "cat-0 brake (grip-limited) vs a_tip fwd/back", f"{a_cat0:.2f} m/s², SF {sf_c0:.2f}", "SF ≥ 2 (≥1.2 WARN)",
        st(sf_c0 >= 2, sf_c0 >= 1.2))
    m_l, _ = total_cog("fwd")
    T_hold = m_l * G * math.sin(math.atan(SLOPE6)) / 2 * WR / 1000
    md("The SWD parking-brake torque and the phase-short braking decel are **not published** (VERIFICATION E3, RESIDUAL): the design does not "
       "use them. The fields (§7) are sized on the SS1-t ramp, which ends before STO. Two **type tests** replace the missing data (ISO 3691-4 "
       "brake test, `ce/TEST_PLAN.md`): TP-03a cat-0 stopping distance at each speed band (power cut and STO with the ramp disabled), and "
       f"TP-03b holding on a 6 % slope, loaded robot ({m_l:.0f} kg): {T_hold:.2f} Nm per wheel = {T_hold / 4:.2f} Nm at each motor (4:1), "
       "no creep > 10 mm in 10 min with power off. If the measured cat-0 decel is below the grip limit, the cat-0 tip margin is better than shown.")
    md()
    lim["T_hold"] = T_hold
    lim["a_cat0"] = a_cat0
    return lim


def Iz(rows):
    I = 0.0
    for n, mm, cc, b in rows:
        I += mm * ((cc[0] / 1000) ** 2 + (cc[1] / 1000) ** 2)
        if b is not None:
            I += mm * (((b[1] - b[0]) / 1000) ** 2 + ((b[3] - b[2]) / 1000) ** 2) / 12
    return I


def sec4(lim):
    md("## 4. Drive sizing (SWD 125, 4:1) and rotate in place")
    md()
    r = WR / 1000
    v_max = SWD_RPM * 2 * math.pi / 60 * r
    rows = []
    stat = []
    for pose in ("empty", "fwd"):
        m, c = total_cog(pose)
        Nd = m * G - 4 * lim["Fi"]
        for a in (0.0, 0.5, 1.0):
            for s in (0.0, SLOPE6, SLOPE8):
                al = math.atan(s)
                F = m * a + m * G * math.sin(al) + (CRR_D * Nd + CRR_C * (m * G - Nd)) * math.cos(al)
                T = F / 2 * r
                lab = "PASS" if T <= SWD_TN else ("WARN" if T <= SWD_TP else "FAIL")
                if a == 0:
                    lab = "PASS" if T <= SWD_TN else "FAIL"          # steady state must be within S1
                rows.append([pose if pose == "empty" else "loaded", a, f"{s * 100:.0f} %", f"{F:.0f}", f(T), lab])
                stat.append(lab)
    table(["mass case", "a m/s²", "slope", "total tractive force N", "torque per wheel Nm", f"vs {SWD_TN} nom / {SWD_TP} peak"], rows)
    md("WARN = above nominal but below peak: allowed only for short accelerations (peak-torque duration from the SWD manual).")
    md()
    res("4 Drive", "per-wheel torque, all cases (a ≤ 1.0, slope ≤ 8 %)", "see table", f"≤ {SWD_TP} Nm peak, steady ≤ {SWD_TN}",
        "FAIL" if "FAIL" in stat else ("WARN" if "WARN" in stat else "PASS"))
    m, _ = total_cog("fwd")
    Nd = m * G - 4 * lim["Fi"]
    T_peak_a = (2 * SWD_TP / r - m * G * SLOPE6 - CRR_D * Nd - CRR_C * (m * G - Nd)) / m
    md(f"Max accel at peak torque on 6 % (loaded): {T_peak_a:.2f} m/s². Flat: {(2 * SWD_TP / r - CRR_D * Nd - CRR_C * (m * G - Nd)) / m:.2f} m/s².")
    md()
    rows = []
    for v in (1.0, 1.5):
        for s in (0.0, SLOPE6):
            F = m * G * math.sin(math.atan(s)) + CRR_D * Nd + CRR_C * (m * G - Nd)
            Pw = F * v / 2
            rows.append([v, f"{s * 100:.0f} %", f"{Pw:.0f}", f"{Pw / ETA_DRV:.0f}", st(Pw <= SWD_P)])
    table(["v m/s", "slope", "mech. power per wheel W", "elec. per wheel W", f"vs S1 {SWD_P:.0f} W"], rows)
    res("4 Drive", "S1 power cruising 1.5 m/s on 6 %", rows[-1][2] + " W/wheel", f"≤ {SWD_P:.0f} W", rows[-1][-1])
    md(f"Mechanical max speed: {SWD_RPM:.0f} rpm × π × {WR * 2:.0f} mm = **{v_max:.2f} m/s**. Speed limit (SLS) set by the scanner field (§7): "
       "1.5 m/s max, 0.3 m/s in the docking/narrow zones, 0.5 m/s in carry mode (§8).")
    md()
    # ---- swept radius
    md("**Swept radius when the base rotates in place** (rotation centre = base centre = drive axle midpoint). Computed from every "
       "STL vertex in plan (base: `out/stl`; superstructure: `../cad/out/stl`, arms in the home/parked pose):")
    md()
    sup_r = []
    for n, v in SUP_V.items():
        rr = np.hypot(v[:, 0], v[:, 1])
        i = int(rr.argmax())
        sup_r.append((float(rr[i]), n, v[i]))
    sup_r.sort(key=lambda x: -x[0])
    rows = [["base (max over all base parts)", R_BASE_PART, f"({R_BASE_PT[0]:.0f}, {R_BASE_PT[1]:.0f}, {R_BASE_PT[2]:.0f})", f"{R_BASE:.0f}"]]
    rows += [["superstructure", n, f"({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f})", f"{rr:.0f}"] for rr, n, p in sup_r[:6]]
    tray = [x for x in sup_r if x[1].startswith("P20")]
    if tray:
        rows.append(["superstructure (tray edge, cups/flasks)", tray[0][1], f"({tray[0][2][0]:.0f}, {tray[0][2][1]:.0f}, {tray[0][2][2]:.0f})", f"{tray[0][0]:.0f}"])
    rows.append(["**whole robot, arms parked**", R_SUP_PART if R_SUP >= R_BASE else R_BASE_PART, "", f"**{R_SWEPT:.0f}**"])
    rows.append(["info: arms extended (hand + fingers, side pose)", "OpenArm", "", f"{ARM_REACH:.0f}"])
    table(["group", "part", "farthest point (x, y, z) mm", "plan radius mm"], rows)
    md(f"Superstructure overhang beyond the base outline (rubber edge {BX * 2:.0f} × {BY * 2:.0f} mm, {P.CHAMF:g} mm chamfers), "
       f"arms parked: **{OVH:.0f} mm** ({OVH_PART}" + (f" at ({OVH_PT[0]:.0f}, {OVH_PT[1]:.0f}, z {OVH_PT[2]:.0f}))" if OVH_PT is not None else ")")
       + ". Above the scan plane, so the scanners do not see it: the protective fields must be drawn from the overhang (§7).")
    md()
    res("4 Drive", "superstructure overhang beyond the base outline (arms parked)", f"{OVH:.0f} mm ({OVH_PART})", "0 mm (else add to the fields)",
        st(OVH <= 0.5, True))
    # ---- yaw rate limits
    a_lat = min(lim["worst"]["lat"], lim["worst"]["lat_lift"])
    a_item = MU_TRAY * G / 2
    a_y = min(a_lat, a_item)
    w_sw = math.sqrt(a_y / (R_SWEPT / 1000))
    w_base = math.sqrt(a_y / (R_BASE / 1000))
    w_reach = math.sqrt(a_y / (ARM_REACH / 1000))
    w_wheel = v_max / (WY / 1000)
    I_base = Iz(base)
    I_sup = Iz(sup_rows("work"))
    I_tot = I_base + I_sup
    alpha_wheel = 2 * (SWD_TP / r - CRR_D * Nd) * (WY / 1000) / I_tot
    md(f"**Rotate in place / yaw-rate limits.** Allowed centripetal/tangential accel at the periphery: min(lateral tip/2 = {lim['worst']['lat']:.2f}, "
       f"inner-wheel lift/2 = {lim['worst']['lat_lift']:.2f}, tray-item slip μ_tray·g/2 = {a_item:.2f}) = **{a_y:.2f} m/s²** "
       "(conservative: applied at the farthest point of the robot).")
    md()
    table(["limit", "radius mm", "ω max rad/s", "ω max °/s"],
          [["base corners only (info)", f"{R_BASE:.0f}", f(w_base), f"{math.degrees(w_base):.0f}"],
           ["**whole robot swept radius (arms parked)**", f"{R_SWEPT:.0f}", f(w_sw), f"**{math.degrees(w_sw):.0f}**"],
           ["arms extended (not allowed while rotating; carry mode only)", f"{ARM_REACH:.0f}", f(w_reach), f"{math.degrees(w_reach):.0f}"],
           ["wheel speed limit (380 rpm) in place", f"{WY:.0f}", f(w_wheel), f"{math.degrees(w_wheel):.0f}"]])
    md(f"Yaw inertia about the base centre (work pose): base {I_base:.1f} kg·m² + superstructure {I_sup:.1f} kg·m² "
       f"(point masses + bounding-box self inertia from the STL files, CAD) = {I_tot:.1f} kg·m². Yaw accel available at peak "
       f"wheel torque: {alpha_wheel:.1f} rad/s²; the tangential accel limit gives α ≤ {a_y / (R_SWEPT / 1000):.1f} rad/s² at {R_SWEPT:.0f} mm.")
    md()
    w_cfg = min(w_sw, w_wheel)
    res("4 Drive", "rotate-in-place yaw-rate limit (whole robot swept radius)", f"{math.degrees(w_cfg):.0f} °/s at r {R_SWEPT:.0f} mm", "configure as safe limit", "PASS")
    lim.update(w_cfg=w_cfg, w_reach=w_reach, a_y=a_y, v_max=v_max)
    return lim


def sec5(lim):
    md("## 5. Energy, battery current, DC-DC")
    md()
    m, _ = total_cog("fwd")
    Nd = m * G - 4 * lim["Fi"]
    F_roll = CRR_D * Nd + CRR_C * (m * G - Nd)
    v = 1.0
    seg = 10.0
    P_drive = (F_roll * v + 0.5 * m * v ** 2 / (seg / v)) / ETA_DRV / ETA_DC          # while driving; regen dumped in the shunt
    inp("logistics drive cycle", "1.0 m/s, stop every 10 m, regen dumped", "-", "ASSUMED", "")
    base_w = JET + SCN + SAFE + NETCAM + SWD_STBY + DC_NL
    profiles = {"logistics": dict(drive=0.6, arms=0.3, coffee=0.0),
                "barista": dict(drive=0.1, arms=0.9, coffee=0.5),
                "idle-heavy": dict(drive=0.05, arms=0.1, coffee=0.05)}
    inp("duty profiles (fractions of the hour)", "; ".join(f"{k}: drive {d['drive']}, arms {d['arms']}, coffee {d['coffee']}"
                                                          for k, d in profiles.items()), "-", "ASSUMED", "rev B: waist removed")
    rows = []
    for var, (atyp, aidle) in (("OpenArm (R&D)", (OA_TYP, 0.0)), ("Kassow Edge (CE)", (KA_TYP, KA_IDLE))):
        for k, d in profiles.items():
            arms_dcdc = var.startswith("OpenArm")
            Pa = 2 * (d["arms"] * atyp + (1 - d["arms"]) * aidle) / (ETA_DC if arms_dcdc else 1.0)
            Pd = d["drive"] * P_drive
            Pc = d["coffee"] * COFFEE / ETA_DC
            Ptot = base_w + Pa + Pd + Pc
            hrs = E_BATT * USABLE * 1000 / Ptot
            rows.append([var, k, f"{base_w:.0f}", f"{Pd:.0f}", f"{Pa:.0f}", f"{Pc:.0f}", f"**{Ptot:.0f}**", f"**{hrs:.1f}**"])
            lim.setdefault("P_prof", {})[(var, k)] = Ptot
            lim.setdefault("runtime", {})[(var, k)] = hrs
    md(f"Base loads always on (compute, scanners, safety, network, SWD standby, DC-DC no-load): {base_w:.0f} W (rev A also had "
       f"15 W waist holding + 40 W waist motion: removed). Traction while driving at {v} m/s (loaded, rolling + accel every {seg:g} m): "
       f"{P_drive:.0f} W at the bus.")
    md()
    table(["variant", "profile", "base W", "traction W", "arms W", "coffee W", "total W", f"runtime h ({E_BATT:.2f} kWh × {USABLE})"], rows)
    worst_rt = min(float(r[-1].strip("*")) for r in rows)
    res("5 Energy", "runtime, worst variant/profile", f"{worst_rt:.1f} h", "≥ 4 h (shift half)", st(worst_rt >= 4, worst_rt >= 2.5))
    # ---- battery duty check (rev B2: Discover ratings, VERIFICATION D9)
    md(f"**Battery duty (rev B2).** Discover ratings per pack: {I_PACK_C:.0f} A continuous for repeated full cycles (thermal, 5 back-to-back "
       f"cycles), {I_PACK_1H:.0f} A for 1 h, {I_PACK_P:.0f} A RMS peak for 10 s; the BMS trips above 58 A for 10 s. The pair scales linearly "
       f"(30 A / 116 A / 180 A, Table 3-9). Average and RMS currents are taken at the {V_LVCO:g} V cut-off (conservative); each intermittent "
       "load is treated as on/off with its duty fraction (independent loads: E[P²] = (ΣE[P])² + Σ P²·f·(1−f)).")
    md()
    rows = []
    duty = {}
    for var, (atyp, aidle) in (("OpenArm (R&D)", (OA_TYP, 0.0)), ("Kassow Edge (CE)", (KA_TYP, KA_IDLE))):
        for k, d in profiles.items():
            arms_dcdc = var.startswith("OpenArm")
            eta_a = ETA_DC if arms_dcdc else 1.0
            loads = [(2 * (atyp - aidle) / eta_a, d["arms"]), (P_drive, d["drive"]), (COFFEE / ETA_DC, d["coffee"])]
            base_c = base_w + 2 * aidle / eta_a
            mean = base_c + sum(Pw * fr for Pw, fr in loads)
            var_ = sum(Pw * Pw * fr * (1 - fr) for Pw, fr in loads)
            rms = math.sqrt(mean * mean + var_)
            i_avg, i_rms = mean / V_LVCO, rms / V_LVCO
            rows.append([var, k, f"{mean:.0f}", f"{i_avg:.1f}", f"{i_rms:.1f}", f"{i_avg / 2:.1f}", st(i_rms <= 2 * I_PACK_C)])
            duty[(var, k)] = (mean, i_avg, i_rms)
    table(["variant", "profile", "average W", f"I avg A @{V_LVCO:g} V (pair)", "I RMS A (pair)", "I avg per pack A", f"RMS ≤ 2 × {I_PACK_C:.0f} A"], rows)
    worst = max(duty.items(), key=lambda kv: kv[1][2])
    res("5 Energy", "battery duty: worst profile RMS current vs pair continuous rating",
        f"{worst[1][2]:.1f} A ({worst[0][0].split()[0]} {worst[0][1]})", f"≤ {2 * I_PACK_C:.0f} A", st(worst[1][2] <= 2 * I_PACK_C))
    sust = (2 * OA_CONT / ETA_DC + 2 * SWD_P / ETA_DRV / ETA_DC + COFFEE / ETA_DC + base_w) / V_LVCO
    sust_c48 = (2 * KA_TYP + 2 * SWD_P / ETA_DRV / ETA_DC + COFFEE / ETA_DC + base_w) / V_LVCO
    t_full = E_BATT * USABLE * 1000 / (sust * V_LVCO)
    md(f"**Worst sustained case** (envelope, not a duty profile): 2 × OpenArm at their continuous rating ({OA_CONT:.0f} W each) + both SWD at "
       f"S1 ({SWD_P:.0f} W each) + coffee brewing + base = **{sust:.1f} A** at {V_LVCO:g} V (C48 with Kassow typical: {sust_c48:.1f} A). This exceeds "
       f"the 30 A repeated-cycle rating of the pair, but it is only {100 * sust / (2 * I_PACK_1H):.0f} % of the 1-hour rating ({2 * I_PACK_1H:.0f} A) and "
       f"below one pack's {I_PACK_1H:.0f} A. Held without a break it would empty the usable energy in {t_full:.1f} h: one full cycle slightly above "
       "the thermal rating, which the BMS answers with an over-temperature trip (availability, not a hazard). It cannot persist in service: coffee "
       "brews in ~1 min cycles, the arms reach their continuous rating only in bursts and the drives reach S1 only on ramps. "
       "**Decision: no 3rd pack, no hardware limit.** Rule for the Jetson energy manager: keep the 1-hour rolling average of the pack current "
       f"(read over LYNK) ≤ 30 A for the pair; above it, cap arm power and speed first. The duty profiles need at most {worst[1][2]:.1f} A RMS.")
    md()
    res("5 Energy", "worst sustained (2 × OpenArm cont + 2 × SWD S1 + coffee) vs pair 1-hour rating", f"{sust:.0f} A",
        f"≤ {2 * I_PACK_1H:.0f} A (1 h); > 30 A only as a transient (energy manager)", st(sust <= 2 * I_PACK_1H))
    P_trac_pk = 2 * DDR_IP * 24.0 / ETA_DC
    rows = []
    for var, arm_pk, via in (("OpenArm", OA_PK, True), ("Kassow", KA_PK, False)):
        Pa = 2 * arm_pk / (ETA_DC if via else 1)
        Pc = COFFEE_PK / ETA_DC
        Pt = P_trac_pk + Pa + Pc + base_w
        I = Pt / V_MIN
        rows.append([var, f"{P_trac_pk:.0f}", f"{Pa:.0f}", f"{Pc:.0f}", f"{base_w:.0f}", f"{Pt:.0f}", f"{I:.0f}",
                     f"{I / 2:.0f}", st(I / 2 < I_PACK_1H, I / 2 <= I_PACK_P)])
        lim.setdefault("I_pk", {})[var] = I
    table(["arms", "traction pk (2 DDR at 30 A)", "arms pk", "coffee pk", "base", "total W", f"I at {V_MIN:g} V A (pair)",
           "per pack A", f"< {I_PACK_1H:.0f} A (no BMS trip) / ≤ {I_PACK_P:.0f} A 10 s"], rows)
    md(f"All peaks coinciding is the worst case. The DC-DC / OpenArm peaks last ≤ 5 s, shorter than the 10 s of both the {I_PACK_P:.0f} A peak rating "
       "and the BMS over-discharge timer, and the coincident peak stays below 58 A per pack, so the BMS never sees an over-current condition.")
    md()
    for r in rows:
        res("5 Energy", f"peak battery current ({r[0]}), per pack", r[7] + " A", f"< {I_PACK_1H:.0f} A (BMS trip 10 s), ≤ {I_PACK_P:.0f} A 10 s", r[-1])
    lim["duty"] = duty
    # DC-DC
    rows = []
    for v_ in (1.5, lim["v_max"]):
        w = v_ / r if (r := WR / 1000) else 0
        P_w = SWD_TP * w / ETA_DRV
        I24 = 2 * P_w / 24.0
        rows.append([f"traction: 2 wheels at peak torque {SWD_TP} Nm, {v_:.2f} m/s", f"{I24:.0f} A", f"2 × {DDR_I:.0f} = {2 * DDR_I:.0f} A cont / {2 * DDR_IP:.0f} A 5 s",
                     st(I24 <= 2 * DDR_I, I24 <= 2 * DDR_IP)])
    rows.append(["arm (OpenArm): 360 W cont on 1 DDR (centre bay)", f"{OA_CONT / 24:.0f} A", f"{DDR_I:.0f} A", st(OA_CONT / 24 <= DDR_I)])
    rows.append(["arm (OpenArm): 720 W 5 s on 1 DDR (centre bay)", f"{OA_PK / 24:.0f} A", f"{DDR_IP:.0f} A (5 s)", st(OA_PK / 24 < 0.9 * DDR_IP, OA_PK / 24 <= DDR_IP)])
    table(["DC-DC check", "demand", "capacity", "status"], rows)
    for rr in rows:
        res("5 Energy", "DC-DC " + rr[0], rr[1], rr[2], rr[3])
    md("Traction: the regulated 24 V DDR (current-limited) cannot absorb regen; the two 27 V maxon DSR 50/5 clamps are MANDATORY (SWD FW >= 1.1.4 disables the phase-short brake if the supply cannot accept current, VERIFICATION E1; 27 V < DDR OVP 28.8 V < SWD alert 32 V) and are sized for the "
       f"braking energy: ½·m·v² at 1.5 m/s = {0.5 * m * 1.5 ** 2:.0f} J per stop, peak power ≈ m·a·v = {m * A_SS1 * 1.5:.0f} W "
       "(minus losses) for ~1 s. Arms: one DDR per arm has no margin at 720 W (100 % of the 5 s rating) - WARN; use a 2nd DDR in "
       "parallel per arm (DDR-480 supports parallel with ORing) or limit arm peak power in the driver.")
    md()
    # rev B: arm buses leave the base at 24 V through the deck grommet
    rho = 0.0175
    R_loop = rho * 2 * ARM_CABLE_L / ARM_CABLE_A
    dv_c, dv_p = R_loop * OA_CONT / 24, R_loop * OA_PK / 24
    md(f"**Arm 24 V feeds (rev B).** The arm DC-DCs (E50, 2 × DDR-480C-24) and the ORing modules (E52) are in the base centre bay, so "
       f"each arm bus crosses the deck grommet (E53, CABLE_PASS) at 24 V instead of 48 V: loop {2 * ARM_CABLE_L:.1f} m of "
       f"{ARM_CABLE_A:g} mm² Cu (ASSUMED) = {R_loop * 1000:.1f} mΩ ⇒ drop {dv_c:.2f} V at 360 W, {dv_p:.2f} V at 720 W "
       f"({100 * dv_p / 24:.1f} % of 24 V). Use remote sense or set the DDR output to compensate. Note: the amr_params CABLE_PASS "
       "comment still says '48 V arm buses' - with the DC-DCs in the base the arm buses are 24 V.")
    md()
    res("5 Energy", "arm 24 V feed drop at 720 W peak", f"{dv_p:.2f} V ({100 * dv_p / 24:.1f} %)", "≤ 3 % (0.72 V)", st(dv_p <= 0.72, dv_p <= 1.2))
    q_bay = 2 * OA_CONT * (1 / ETA_DC - 1) + JET_MAX
    md(f"Centre-bay heat (info): 2 arm DC-DCs at 360 W cont ({2 * OA_CONT * (1 / ETA_DC - 1):.0f} W loss) + Jetson max {JET_MAX:.0f} W = "
       f"**{q_bay:.0f} W** in the closed bay between the batteries (156 × 254 mm, below the deck). The side-bay fans (E40) do not "
       "obviously ventilate the centre bay: provide an air path (spine cut-outs or a dedicated fan) and verify by a heat-run test.")
    md()
    I_pk = max(lim["I_pk"].values())
    FUSE = inp("main fuse F0 Siemens 3NA3830 (NH000 gG)", 100.0, "A", "SOURCED", "Siemens 3NA3830 data sheet: 100 A gG, 250 V DC, 25 kA DC (VERIFICATION SI5)")
    SW80 = inp("Albright SW80B Ith (interrupted) / thermal", 100.0, "A", "SOURCED", "Albright SW80 data sheet: Ith 100 A / 125 A (VERIFICATION AL1)")
    table(["item", "value", "check", "status"],
          [["main fuse 100 A gG vs sustained", f"{sust:.0f} A", "fuse ≥ 1.25 × sustained", st(FUSE >= 1.25 * sust)],
           ["main fuse vs worst peak (5 s)", f"{I_pk:.0f} A", "a gG link carries < 1.5 × In for ≫ 5 s", st(I_pk <= 1.5 * FUSE)],
           ["SW80B vs sustained", f"{sust:.0f} A", f"≤ {SW80:.0f} A (SOURCED)", st(sust <= SW80)],
           ["SW80B vs peak (5 s)", f"{I_pk:.0f} A", "≤ 125 A thermal (SOURCED); K0 never breaks load in normal use", st(I_pk <= 125)]])
    res("5 Energy", "main fuse 100 A vs sustained/peak", f"{sust:.0f} / {I_pk:.0f} A", "1.25×sust ≤ 100, peak ≤ 150", st(FUSE >= 1.25 * sust and I_pk <= 1.5 * FUSE))
    res("5 Energy", "SW80B contactor rating vs sustained / peak", f"{sust:.0f} / {I_pk:.0f} A", "≤ 100 A / 125 A (SOURCED)", st(sust <= SW80 and I_pk <= 125))
    lim["sust"] = sust
    lim["q_bay"] = q_bay
    return lim


def sec6(lim):
    md("## 6. Charging")
    md()
    ah = P.BATT["Ah"] * 2
    out = {}
    for name, I in (("NPB-750-48 (chosen, Class B)", I_CHG), ("NPB-1700-48 (option)", I_CHG_ALT)):
        I_net = I - P_DOCK / V_CHG
        out[name] = (I, I_net, 0.7 * ah / I_net)
    (I7, n7, t7), (I17, n17, t17) = out.values()
    rows = [["charger output (CC, mid-CC voltage)", f"{I7 * V_CHG:.0f} W ({I7:g} A at {V_CHG:g} V)", f"{I17 * V_CHG:.0f} W ({I17:g} A)"],
            ["robot docked consumption (ASSUMED)", f"{P_DOCK:.0f} W = {P_DOCK / V_CHG:.1f} A", "same"],
            ["net charge current", f"{n7:.1f} A ({n7 / 2:.1f} A per pack)", f"{n17:.1f} A ({n17 / 2:.1f} A per pack)"],
            ["20 → 90 % (CC, LFP)", f"**{t7:.2f} h** ({t7 * 60:.0f} min)", f"{t17:.2f} h ({t17 * 60:.0f} min)"]]
    for (var, k), Pw in lim["P_prof"].items():
        if var.startswith("OpenArm") or k == "barista":
            r7 = Pw / (n7 * V_CHG) * 60
            r17 = Pw / (n17 * V_CHG) * 60
            rows.append([f"opportunity charging, {var} {k} ({Pw:.0f} W): min charge per hour of work", f"{r7:.0f}", f"{r17:.0f}"])
    rows.append([f"RoboPad {RP_I:.0f} A continuous vs CC", f"margin {RP_I / I7:.1f}×", f"margin {RP_I / I17:.1f}×"])
    table(["item", "NPB-750-48 (chosen)", "NPB-1700-48 (option)"], rows)
    md(f"**Charger decision (rev B2): NPB-750-48.** RoboPad requires a charger compliant with EN 61000-6-3 (datasheet v1.3 p.14); the NPB-750 "
       "is EMC Class B conducted and radiated (SOURCED), the NPB-1700 is Class A radiated and would need a dock-level EMC test. Both carry the "
       "IEC 60335-2-29 approval and the DIP 'flooded' preset 56.8 / 53.6 V that equals the Discover bulk / float voltages, so no reprogramming. "
       f"The price is the charge time: {t7:.1f} h instead of {t17:.1f} h for 20 → 90 %. Acceptable for the single-shift use of the limits "
       f"(8-10 h/day, charge overnight ≤ {T_CHG_MAX:g} h) and for the OpenArm profiles. Not acceptable for the C48 barista configuration "
       f"({lim['P_prof'][('Kassow Edge (CE)', 'barista')]:.0f} W > {n7 * V_CHG:.0f} W net charge power: it could never recover by opportunity "
       "charging): that configuration keeps the NPB-1700-48 option with a dock EMC test (TP-19b). The dock adds a 59 V over-voltage relay "
       "(RoboPad 60 V fault limit; the NPB OVP trips only at 82-100 V).")
    md()
    res("6 Charging", "20→90 % time (NPB-750-48)", f"{t7:.2f} h", f"≤ {T_CHG_MAX:g} h (overnight)", st(t7 <= T_CHG_MAX))
    res("6 Charging", "RoboPad continuous rating vs charger CC (both options)", f"{I7:g} / {I17:g} A", f"≤ {RP_I:.0f} A", st(max(I7, I17) <= RP_I))
    res("6 Charging", "charge current per pack (both options)", f"{n7 / 2:.1f} / {n17 / 2:.1f} A", f"≤ {I_CHG_PACK:.0f} A continuous (SOURCED)",
        st(max(n7, n17) / 2 <= I_CHG_PACK))
    lim["t_chg"] = t7
    lim["t_chg_alt"] = t17
    return lim


def sec7(lim):
    md("## 7. Protective field lengths (nanoScan3)")
    md()
    T = T_SCAN + T_LOG + T_DRV
    rs = math.hypot(290, 208)
    off = BX - 290.0
    md(f"S = v·(t_scan {T_SCAN * 1000:.0f} ms SOURCED + t_logic {T_LOG * 1000:.0f} ms SOURCED (PNOZ through the EF 4DI4DOR relays) + t_drive "
       f"{T_DRV * 1000:.0f} ms ASSUMED, measure) + {BRK_F}·v²/(2·{A_SS1}) + Z ({Z_SUP:.0f} mm supplement SOURCED + {Z_REFL:.0f} mm reflector: valid "
       f"only while no retroreflector is within 6 m of the scan plane, else ZR = 350 mm, SICK OI p.27). Field length from the "
       f"scanner = S + {off:.0f} mm (scanner origin to front bumper). Brake decel = SS1-t ramp {A_SS1} m/s²: valid because STO arrives after the "
       "ramp at every band (timing table below); replace by the measured stopping distance of the ISO 3691-4 brake test. Lateral fields are measured from the "
       f"outermost point of the robot: base outline + superstructure overhang {OVH:.0f} mm (§4).")
    md()
    rows = []
    for v in (0.3, 0.8, 1.2, 1.5):
        s_r = v * T * 1000
        s_b = BRK_F * v * v / (2 * A_SS1) * 1000
        S = s_r + s_b + Z_SUP + Z_REFL
        L_ = S + off
        rows.append([v, f"{s_r:.0f}", f"{s_b:.0f}", f"{S:.0f}", f"{L_:.0f}", st(L_ <= NS_RANGE)])
        res("7 Safety", f"protective field at {v} m/s", f"{L_:.0f} mm", f"≤ {NS_RANGE:.0f} mm", rows[-1][-1])
    table(["v m/s", "reaction mm", "braking mm", "S mm", "field from scanner mm", "≤ 3000 mm"], rows)
    md("Warning field: 2 × protective + 0.5 m recommended (slow-down to the next speed band). Rev B2 vs B1: t_logic 10 → 54 ms and "
       f"t_drive 20 → 40 ms add {(0.054 + 0.040 - 0.030) * 1500:.0f} mm at 1.5 m/s.")
    md()
    md(f"**SS1-t timing (rev B2 choice: STO delay {T_STO:g} s, not mid-ramp STO).** The PNOZ timer starts when the OSSD switches off; the ramp "
       f"starts after t_logic + t_drive = {(T_LOG + T_DRV) * 1000:.0f} ms. Why not a short delay with fields sized for STO mid-ramp: the "
       "tail would be a cat-0 phase-short stop whose decel is not published (fields could not be computed), its tip margin is lower "
       "(§2b) and every protective stop above 0.75 m/s would end in a cat-0 jolt. The cost of the long delay is the ramp-failure case, "
       f"which the SWD SLS monitoring bounds at t_SLS = {T_SLS:g} s (PL d) before the PNOZ STO at {T_STO:g} s (PL e).")
    md()
    trows = []
    for v in (0.3, 0.8, 1.2, 1.5):
        t_end = T_LOG + T_DRV + v / A_SS1
        t_03 = T_LOG + T_DRV + max(0.0, v - 0.3) / A_SS1
        a_c0 = lim["a_cat0"]
        d_fail = v * (T_SCAN + T_LOG + T_SLS) + v * v / (2 * a_c0)
        trows.append([v, f"{t_end:.3f}", f"{t_03:.3f}", st(t_end <= T_STO and t_03 <= T_SLS), f"{d_fail * 1000:.0f}"])
        res("7 Safety", f"SS1-t timing at {v} m/s (ramp end ≤ t_STO, ≤ 0.3 m/s before t_SLS)", f"{t_end:.3f} / {t_03:.3f} s",
            f"≤ {T_STO:g} / {T_SLS:g} s", st(t_end <= T_STO and t_03 <= T_SLS))
    table(["v m/s", "ramp ends at s", "≤ 0.3 m/s at s", f"ramp end ≤ {T_STO:g} s and ≤ 0.3 m/s by {T_SLS:g} s",
           f"info: ramp-failure distance mm (no decel until SLS-STO at {T_SLS:g} s, then grip-limited cat 0)"], trows)
    md("The ramp-failure distance is a single fault in a non-safety-rated part (SS1-t per IEC 61800-5-2 does not monitor the ramp); it is "
       "recorded as a residual risk in `ce/RISK_ASSESSMENT.md` and measured in TP-01b (ramp disabled by fault injection).")
    md()
    # rotation in place: circle about the rotation centre covering the whole robot
    w = lim["w_cfg"]
    alpha = A_SS1 / (WY / 1000)
    r = R_SWEPT / 1000
    s_stop = r * (w * T + w * w / (2 * alpha) * BRK_F) * 1000
    R_rot = R_SWEPT + s_stop + Z_SUP + Z_REFL
    d_rot = math.hypot(R_rot, rs)
    md(f"**Rotation in place** at the configured limit ω = {math.degrees(w):.0f}°/s, stop α = {A_SS1}/0.232 = {alpha:.1f} rad/s². "
       f"The field must cover the swept circle of the **whole robot** (r = {R_SWEPT:.0f} mm, {R_SUP_PART if R_SUP >= R_BASE else R_BASE_PART}; "
       f"base alone {R_BASE:.0f} mm) plus the peripheral travel during the stop ({s_stop:.0f} mm) plus Z: **circle R = {R_rot:.0f} mm about the "
       f"base centre** = {R_rot - BX:.0f} mm beyond the front/rear bumper and {R_rot - BY:.0f} mm beyond the sides. Farthest point from a "
       f"corner scanner (r_s = {rs:.0f} mm) ≈ √(R² + r_s²) = {d_rot:.0f} mm.")
    md()
    res("7 Safety", "rotate-in-place field (whole-robot swept circle)", f"R {R_rot:.0f} mm about centre; {d_rot:.0f} mm from scanner", f"≤ {NS_RANGE:.0f}", st(d_rot <= NS_RANGE))
    # arms moving, base standstill
    C = max(850.0, 1200 - 0.4 * SCAN_Z)
    Tw = T_SCAN + T_LOG + T_ARM_STOP
    S_w = K_HUM * Tw + C
    R = ARM_REACH + S_w
    d_req = math.hypot(R, rs)
    md(f"**Arm field (base at standstill, arms moving; EN ISO 13855, horizontal):** S = K·T + C, K = 1600 mm/s, T = {T_SCAN * 1000:.0f} + "
       f"{T_LOG * 1000:.0f} + {T_ARM_STOP * 1000:.0f} ms (arm stop, ASSUMED) = {Tw * 1000:.0f} ms, C = 1200 − 0.4·H = {C:.0f} mm "
       f"(H = {SCAN_Z:.0f} mm). Without the waist the arms reach to any side of the fixed torso, so the hazard is a circle about "
       f"the base centre with the largest hand radius ({ARM_REACH:.0f} mm, side pose): R = {ARM_REACH:.0f} + {S_w:.0f} = **{R:.0f} mm**; "
       f"farthest point from a corner scanner ≈ **{d_req:.0f} mm** vs 3000 mm. A pose-dependent field (front-only when the arms work "
       "forward) can be selected through the PNOZ if the arm controller provides a safe zone signal - for OpenArm it cannot "
       "(no safety-rated position), so the full circle applies. The OpenArm falls on a cat-0 stop (no brakes): not covered here.")
    md()
    res("7 Safety", "arm field radius from scanner (base standstill)", f"{d_req:.0f} mm", f"≤ {NS_RANGE:.0f}", st(d_req <= NS_RANGE, d_req <= NS_RANGE * 1.05))
    md("Field-set table to configure (nanoScan3 monitoring cases, selected by the PNOZ through the SR2 relay contacts; speed bands enforced by the SWD SLS / SMS):")
    md()
    table(["case", "speed band", "protective field (from scanner, travel direction)", "lateral (from the body side)", "other"],
          [["dock / narrow", "≤ 0.3 m/s", f"{rows[0][4]} mm", f"≥ {100 + OVH:.0f} mm", "docking: FS3 static rear cut-out shaped to the dock (no muting), only with SLS 0.3 m/s"],
           ["slow", "≤ 0.8 m/s", f"{rows[1][4]} mm", f"≥ {150 + OVH:.0f} mm", ""],
           ["normal", "≤ 1.2 m/s", f"{rows[2][4]} mm", f"≥ {200 + OVH:.0f} mm", ""],
           ["fast (open area)", "≤ 1.5 m/s", f"{rows[3][4]} mm", f"≥ {250 + OVH:.0f} mm", "SLS 1.5 m/s in the SWD"],
           ["rotate in place", f"ω ≤ {math.degrees(w):.0f} °/s, arms parked", f"circle R {R_rot:.0f} mm about the base centre", f"{R_rot - BY:.0f} mm", "arms must be parked (no rotation with arms extended)"],
           ["arms moving", "base standstill (SMS)", f"circle R {R:.0f} mm about the base centre", "-", ""]])
    lim["R_rot"], lim["R_arm"] = R_rot, R
    return lim


def sec8(lim):
    md("## 8. Carry mode (arms hold an object while driving)")
    md()
    m_cup = M_HAND
    lim_tip_work = lim["work"]["any"]
    lim_tip_worst = lim["worst"]["any"]
    Fh = 2 * MU_GRIP * GRIP_F
    a_slip = math.sqrt(max(0.0, (Fh / (2 * m_cup)) ** 2 - G ** 2))
    F_req = 2 * m_cup * math.hypot(G, 0.5) / (2 * MU_GRIP)
    rows = [["tipping SF 2, carry pose = work pose (any direction)", f"{lim_tip_work:.2f} m/s²"],
            [f"tipping SF 2, arms extended, worst of fwd/side/rear ({lim['worst_gov']['any']})", f"{lim_tip_worst:.2f} m/s²"],
            [f"grip slip, 3 kg cup, 2 pads μ {MU_GRIP} × {GRIP_F:.0f} N (ASSUMED), SF 2", f"{a_slip:.2f} m/s² (0 = cannot hold 3 kg with SF 2 even at rest)"],
            ["grip force needed for 3 kg at 0.5 m/s², SF 2", f"{F_req:.0f} N"]]
    table(["limit", "value"], rows)
    md(f"**Recommended carry mode:** v ≤ 0.5 m/s (SLS), accel/decel ≤ 0.5 m/s², lateral ≤ 0.5 m/s², rotate in place ≤ 30°/s, "
       "arms close to the body (work pose, not extended to the sides: there is no waist to bring them back over the base), "
       "cups ≤ 1 kg unless a form-fit holder (cup sits in a cradle/fingers below the rim) replaces friction grip. "
       f"Tipping SF in carry mode at 0.5 m/s², arms extended worst pose: {lim['worst']['any'] * 2 / 0.5:.1f} ≥ 2.")
    md()
    md("- **OpenArm (R&D):** no brakes, no STO. Any cat-0 stop (E-stop, protective field, power loss) cuts arm power: the arms fall "
       "and the object is dropped (and the falling arm is itself a hazard). Carry mode with OpenArm is acceptable only in R&D, "
       "fenced/attended, not in public. Keep the CONTEXT rule: objects carried in the tray while driving.")
    md("- **Certified arms (Kassow/UR):** brakes + safe stop 1/2 + safe standstill monitoring. Carry mode becomes **certifiable only "
       "with certified standstill monitoring of the arm joints (SOS / safe standstill, PL d) while the base moves**, with the base "
       "stop category SS1 and the arm in SOS, and a risk assessment of the dropped object (EN ISO 10218-2 application, EN ISO 3691-4).")
    md()
    res("8 Carry", "3 kg cup with ASSUMED 50 N gripper, SF 2", f"a_slip {a_slip:.2f} m/s²; needs {F_req:.0f} N", "hold with SF 2",
        st(a_slip >= 0.5))
    res("8 Carry", "tipping SF ≥ 2 at 0.5 m/s² carry limit (arms extended, any side)", f"a_tip/2 = {lim_tip_worst:.2f}", "≥ 0.5", st(lim_tip_worst >= 0.5))
    return lim


def ss_beam(L, loads, n=401):
    """simply supported beam 0..L, point loads [(s, F)] (F + downward). returns max |M| (N·mm) and max |deflection| / (E I) factor."""
    xs = np.linspace(0, L, n)
    M = np.zeros(n)
    d = np.zeros(n)      # deflection × E·I
    for s, F in loads:
        a, b = s, L - s
        M += np.where(xs <= a, F * b * xs / L, F * a * (L - xs) / L)
        d += np.where(xs <= a, F * b * xs * (L ** 2 - b ** 2 - xs ** 2) / (6 * L),
                      F * a * (L - xs) * (L ** 2 - a ** 2 - (L - xs) ** 2) / (6 * L))
    return float(np.abs(M).max()), float(np.abs(d).max())


def ss_mid(L, loads):
    """deflection × E·I at mid-span of a simply supported beam."""
    x = L / 2
    d = 0.0
    for s_, F in loads:
        a, b = s_, L - s_
        d += F * b * x * (L ** 2 - b ** 2 - x ** 2) / (6 * L) if x <= a else F * a * (L - x) * (L ** 2 - a ** 2 - (L - x) ** 2) / (6 * L)
    return d


def foot_loads(pose, gz, ax, ay):
    """column group (everything except the coffee module) -> foot reactions at (COL_X, 0, deck top).
    gz: vertical g multiplier; (ax, ay): inertial accel (m/s²) applied to the masses (e.g. +x = braking while driving forward).
    returns Fz (N, + down), Mx, My (N·mm) about the foot centre, and the coffee-group rows."""
    rows = sup_rows(pose)
    col = [r for r in rows if not r[0].startswith(COFFEE_PREFIX)]
    cof = [r for r in rows if r[0].startswith(COFFEE_PREFIX)]
    o = np.array([COL_X, 0.0, P.DECK_Z1])
    Fz, M = 0.0, np.zeros(3)
    for n, m, c, b in col:
        Fv = np.array([m * ax, m * ay, -m * G * gz])
        M += np.cross(c - o, Fv)
        Fz += m * G * gz
    return Fz, M[0], M[1], cof


def bolt_reactions(Fz, Mx, My):
    """8 M6 on the ±62 grid. R_i (+ = foot pushes the deck down, - = bolt tension)."""
    pts = [(sx * FOOT_B, sy * FOOT_B) for sx in (-1, 0, 1) for sy in (-1, 0, 1) if (sx, sy) != (0, 0)]
    sxx = sum(x * x for x, y in pts)
    syy = sum(y * y for x, y in pts)
    # superstructure equilibrium with deck reactions Q_i (up): ΣQ = Fz, Σx·Q = My, Σy·Q = -Mx  (r × Q·ẑ = (y·Q, -x·Q, 0))
    return [(x, y, Fz / 8 + My * x / sxx - Mx * y / syy) for x, y in pts]


def sec9(lim):
    md("## 9. Structure: deck plate, column foot, floor pan, castor tower roof")
    md()
    t = P.DECK_T
    Lc = DECK_SPAN
    W_row = B_ROW * t ** 2 / 6
    I_row = B_ROW * t ** 3 / 12
    m_sup_w = SUP["fwd"][0]
    md(f"Deck: EN AW-6082-T6 {t:g} mm at z {P.DECK_Z0:g}..{P.DECK_Z1:g}, carried by the two spines (y ±{P.SPINE_Y:g}, c/c {Lc:.0f} mm, "
       f"x ±{P.SPINE_X:g}) and by the four end posts at (±{P.POSTS[0][0]:g}, ±{P.POSTS[0][1]:g}). The superstructure ({m_sup_w:.1f} kg "
       f"incl. {2 * M_HAND + M_TRAY:.1f} kg payload) stands on the deck through the column foot P29 (160 × 160 × 20 at x {COL_X:g}, "
       "8 × M6 on a ±62 mm grid, now tapped in the deck) and the two coffee uprights P22. Model: each foot bolt row (x = "
       f"{COL_X - FOOT_B:g} / {COL_X:g} / {COL_X + FOOT_B:g}) loads a deck strip b = {B_ROW:g} mm (ESTIMATE) simply supported on the "
       f"spines (span {Lc:.0f} mm, conservative: deck continuity and the 20 mm foot flange ignored). Bolt-row loads from a rigid "
       "flange: R_i = F_z/8 + M_y·x_i/Σx² − M_x·y_i/Σy² (M about the foot centre at deck level). The coffee module (E11-E13, P21-P26, P30/P31, S07-S10, SH06) is carried by "
       "the uprights. Load cases: 1 g static, 2 g vertical bump, 1 g + SS1 braking, 2 g bump + cat-0 braking (horizontal accel "
       "applied in the 4 directions), all poses.")
    md()
    cases = [("1 g static", 1.0, 0.0), ("2 g bump", 2.0, 0.0), (f"1 g + SS1 {A_SS1} m/s²", 1.0, A_SS1), (f"2 g + cat-0 {lim['a_cat0']:.2f} m/s²", 2.0, lim["a_cat0"])]
    rows = []
    worst = dict(sig=0, d=0, T=0, M=0, tilt=0, tilt_ss1=0)
    worst_lab = {}
    sig_1g_ss1 = 0.0
    for lab, gz, a in cases:
        best = None
        for pose in POSES:
            for ax, ay in ((a, 0), (-a, 0), (0, a), (0, -a)) if a > 0 else ((0, 0),):
                Fz, Mx, My, cof = foot_loads(pose, gz, ax, ay)
                R = bolt_reactions(Fz, Mx, My)
                sig_r, d_r = 0.0, 0.0
                dmid = {}
                for xr in (-FOOT_B, 0.0, FOOT_B):
                    loads = [(Lc / 2 + y, Ri) for x, y, Ri in R if abs(x - xr) < 1e-6]
                    Mmax, dEI = ss_beam(Lc, loads)
                    sig_r = max(sig_r, Mmax / W_row)
                    d_r = max(d_r, dEI / (E_AL * I_row))
                    dmid[xr] = ss_mid(Lc, loads) / (E_AL * I_row)
                tilt = abs(dmid[FOOT_B] - dmid[-FOOT_B]) / (2 * FOOT_B)
                if lab.startswith("1 g + SS1"):
                    worst["tilt_ss1"] = max(worst.get("tilt_ss1", 0.0), tilt)
                worst["tilt"] = max(worst.get("tilt", 0.0), tilt)
                Tb = max(0.0, -min(Ri for _, _, Ri in R))
                Mres = math.hypot(Mx, My) / 1000
                cand = (sig_r, d_r, Tb, Mres, pose, ax, ay, Fz, Mx / 1000, My / 1000)
                if best is None or cand[0] > best[0]:
                    best = cand
                worst["T"] = max(worst["T"], Tb)
                if Mres > worst["M"]:
                    worst["M"] = Mres
                    worst_lab["M"] = f"{lab}, {pose}, a = ({ax:.1f}, {ay:.1f})"
                if lab.startswith("1 g + SS1"):
                    sig_1g_ss1 = max(sig_1g_ss1, sig_r)
        sig_r, d_r, Tb, Mres, pose, ax, ay, Fz, Mxk, Myk = best
        worst["sig"] = max(worst["sig"], sig_r)
        if gz == 2.0:
            worst["d"] = max(worst["d"], d_r)
        rows.append([lab, f"{pose} (a {ax:.1f}, {ay:.1f})", f"{Fz:.0f}", f"{Mxk:.0f}", f"{Myk:.0f}", f"{Tb:.0f}", f"{sig_r:.0f}", f"{d_r:.2f}"])
    table(["load case", "governing pose / inertial accel m/s²", "F_z N", "M_x Nm", "M_y Nm", "max M6 tension N", "deck σ MPa", "deck δ mm"], rows)
    md(f"Largest column-foot moment: **{worst['M']:.0f} Nm** ({worst_lab.get('M', '')}).")
    md()
    h_sh = 1278.0 - P.DECK_Z1
    t_need = t * (worst["d"] / (Lc / 500)) ** (1 / 3)
    md(f"Column tilt from the deck flexibility (front/rear bolt-row deflection difference / 124 mm): {worst['tilt_ss1'] * 1000:.2f} mrad at "
       f"1 g + SS1 ⇒ {worst['tilt_ss1'] * h_sh:.2f} mm at the shoulders (z 1278); {worst['tilt'] * 1000:.2f} mrad / {worst['tilt'] * h_sh:.2f} mm "
       f"in the 2 g + cat-0 case (upper bound: independent strips, no plate two-way action, no deck continuity over the spines; "
       f"info: affects arm accuracy and the head camera while braking - confirm with a plate FE model). Deck thickness for δ ≤ L/500 "
       f"with this strip model: ≥ {t_need:.1f} mm, or keep 10 mm and add a transverse rib under the foot (e.g. 6 × 40 mm 6082 flat "
       "between the spines under the front and rear bolt rows, or a 10 mm doubler 180 × 274 mm under the foot).")
    md()
    res("9 Structure", "deck stress under the column foot (2 g + braking, all poses)", f"{worst['sig']:.0f} MPa", f"≤ Rp0.2/1.5 = {RP_AL / 1.5:.0f} MPa",
        st(worst["sig"] <= RP_AL / 1.5, worst["sig"] <= RP_AL))
    res("9 Structure", "deck deflection under the column foot (2 g cases)", f"{worst['d']:.2f} mm", f"≤ L/500 = {Lc / 500:.2f} mm",
        st(worst["d"] <= Lc / 500, worst["d"] <= Lc / 250))
    res("9 Structure", "column foot M6 tension (8 × M6, 2 g + braking)", f"{worst['T']:.0f} N", f"≤ preload {M6_PRELOAD:.0f} N / 1.5 (no gapping)",
        st(worst["T"] <= M6_PRELOAD / 1.5, worst["T"] <= M6_PRELOAD))
    res("9 Structure", "column-foot moment (arms at worst reach, 2 g + braking)", f"{worst['M']:.0f} Nm", "info (input to the deck/bolt checks)", "PASS")
    md(f"Fatigue note: in normal operation (1 g + SS1 braking) the deck stress under the foot is ≤ {sig_1g_ss1:.0f} MPa; EN 1999-1-3 "
       "detail category for unwelded plate with drilled holes allows ~ 40-50 MPa at 2·10⁶ cycles (ESTIMATE); keep the tapped holes "
       "clean (or use helicoils) and avoid the deck grommet cut-out (E53, x 37..87) next to the foot rows.")
    md()
    # coffee uprights
    _, _, _, cof = foot_loads("fwd", 2.0, 0.0, 0.0)
    m_cof = sum(r[1] for r in cof)
    c_cof = sum(r[1] * r[2] for r in cof) / m_cof
    (x0, y0), (x1, y1) = COFFEE_UPR
    F1 = 2 * m_cof * G * (c_cof[1] - y0) / (y1 - y0)
    F0 = 2 * m_cof * G - F1
    M_in, dEI = ss_beam(Lc, [(Lc / 2 + y0, F0)])
    sig_in = M_in / W_row
    cant = y1 - P.SPINE_Y
    sig_ca = F1 * cant / W_row
    md(f"Coffee uprights (module {m_cof:.1f} kg, CoG y {c_cof[1]:.0f} mm, 2 g): upright at y {y0:g} → {F0:.0f} N on the span "
       f"(σ {sig_in:.1f} MPa); upright at y {y1:g} sits {cant:.0f} mm outboard of the left spine (deck cantilever) → {F1:.0f} N, "
       f"σ {sig_ca:.1f} MPa. Both negligible.")
    md()
    res("9 Structure", "deck under the coffee uprights (2 g)", f"{max(sig_in, sig_ca):.1f} MPa", f"≤ {RP_AL / 1.5:.0f} MPa", st(max(sig_in, sig_ca) <= RP_AL / 1.5))
    # floor pan / towers (unchanged load path)
    m, _ = total_cog("fwd")
    Fc_tip = m * G / 2
    arm = math.hypot(CX - P.SPINE_X, CY - P.SPINE_Y)
    bp = 100.0
    sig_p = Fc_tip * arm / (bp * P.PAN_T ** 2 / 6)
    rows = [["castor load at the tip limit (hard stop)", f"{Fc_tip:.0f} N", "", ""],
            ["lever from castor axis to spine end (cantilever)", f"{arm:.0f} mm", "", ""],
            ["pan 5 mm S355MC bending, b = 100 mm (ESTIMATE)", f"{sig_p:.0f} MPa", f"≤ ReH/1.5 = {RP_ST / 1.5:.0f}", st(sig_p <= RP_ST / 1.5, sig_p <= RP_ST)]]
    q = 2 * P.BATT["mass"] * G
    Lb = 2 * P.SPINE_Y
    sig_b = q * Lb / 8 / (P.BATT["Lx"] * P.PAN_T ** 2 / 6)
    rows.append([f"pan under battery {P.BATT['mass']:.0f} kg × 2 g, span {Lb:.0f} mm (UDL)", f"{sig_b:.0f} MPa", f"≤ {RP_ST / 1.5:.0f}", st(sig_b <= RP_ST / 1.5)])
    M_roof = Fc_tip / 4 * (52.5 - 40.0) * math.sqrt(2)
    sig_r = M_roof / (60.0 * 6.0 ** 2 / 6)
    H = 0.3 * Fc_tip
    inp("castor horizontal impact load (threshold)", "0.3 × castor load", "-", "ASSUMED", "")
    M_leg = H / 4 * (P.CASTER_H - P.PAN_Z1 + 6.0)
    sig_l = M_leg / (15.0 ** 3 / 6)
    rows += [["tower roof 6 mm S355MC: bolt-to-leg bending (60 mm strip)", f"{sig_r:.0f} MPa", f"≤ {RP_ST / 1.5:.0f}", st(sig_r <= RP_ST / 1.5)],
             ["tower legs 15×15: horizontal 0.3·F (ASSUMED) as cantilevers", f"{sig_l:.0f} MPa", f"≤ {RP_ST / 1.5:.0f}", st(sig_l <= RP_ST / 1.5, sig_l <= RP_ST)]]
    table(["floor pan / tower check", "value", "limit", "status"], rows)
    for r in rows[2:]:
        res("9 Structure", r[0], r[1], r[2], r[3])
    md("The castor load path (tower → pan → spine) loads the 5 mm pan as a short cantilever beyond the spine end (x 262 → 280). "
       "If it is marked WARN/FAIL above, extend the spines to x = ±300 (under the tower) or add a 6 mm gusset tower-to-spine.")
    md()
    lim["deck"] = worst
    return lim


def limits_and_changes(lim):
    md("## Limits to configure (drives / PNOZmulti 2 / nanoScan3)")
    md()
    L = lim["worst"]
    table(["parameter", "value", "where"],
          [["accel limit (normal)", f"{min(A_CMD, L['accel']):.1f} m/s²", "Nav2 + SWD profile"],
           ["decel limit / SS1-t ramp", f"{min(A_SS1, L['decel']):.1f} m/s²", "SWD quick-stop ramp 604Ah (non-safe)"],
           ["SS1-t STO delay (traction)", f"{T_STO:g} s", "PNOZmulti 2 timer element (SR1 O0/O1 → STO_1/STO_2)"],
           ["SLS[1] time to velocity monitoring t_SLS", f"{T_SLS * 1000:.0f} ms", "SWD 6691h (both drives), error reaction STO (6698h)"],
           ["lateral (centripetal) accel v·ω", f"{min(A_CMD, L['lat'], L['lat_lift']):.1f} m/s²", "Nav2 controller (not a safety function)"],
           ["SLS speed bands", "0.3 / 0.8 / 1.2 / 1.5 m/s", "SWD SLS / SMS, field-set switching (§7)"],
           ["rotate-in-place yaw rate (derived maximum; lower for comfort in public)", f"{math.degrees(lim['w_cfg']):.0f} °/s", "Nav2 (SLS per wheel bounds it in FS2)"],
           ["rotate in place only with the arms parked", f"swept circle R {R_SWEPT:.0f} mm, field R {lim['R_rot']:.0f} mm", "arm controller interlock + PNOZ field set FS2"],
           ["carry mode", "v ≤ 0.5 m/s, a ≤ 0.5 m/s², ω ≤ 30 °/s, arms close to the body", "mode in the PNOZ program (certified arms only)"],
           ["castor springs", f"F_inst {lim['Fi']:.0f} N, k ≈ {lim['k_rec'] / 1000:.0f} N/mm, travel ≥ {TRAVEL:g} mm with hard stop", "castor purchase spec"]])


def finish():
    md("## Overall results")
    md()
    table(["section", "check", "value", "limit", "status"], RES)
    n = {s: sum(1 for r in RES if r[-1] == s) for s in ("PASS", "WARN", "FAIL")}
    md(f"**{n['PASS']} PASS, {n['WARN']} WARN, {n['FAIL']} FAIL.**")
    md()


CHANGES = []


def changes(lim):
    md("## Required design changes / open items")
    md()
    md("Not applied to `amr_cad.py` / `amr_params.py` (calc stream only): to be decided and implemented in the CAD stream.")
    md()
    for r in RES:
        if r[0] == "8 Carry" and r[-1] == "FAIL":
            CHANGES.append("Carry mode: the ASSUMED 50 N OpenArm gripper cannot hold a 3 kg cup by friction with SF 2 "
                           "(needs ~75 N): form-fit cup cradle or carry objects in the tray (current R&D rule); measure the grip force.")
        if r[0] == "4 Drive" and "overhang" in r[1] and r[-1] != "PASS":
            CHANGES.append(f"Superstructure overhang: {r[2]} beyond the base outline above the scan plane (coffee shelf/shuttle on the "
                           "right side). Either trim P21/P24/S08 so that the coffee module stays inside y ≥ -280 mm, or keep it and add the "
                           "overhang to every lateral protective field (done in §7) and to the rotate-in-place circle.")
        if r[0] == "5 Energy" and "720 W" in r[1] and r[-1] != "PASS":
            CHANGES.append("Arm DC-DC: 720 W 5 s = 100 % of one DDR-480C-24 peak: 2 DDR in parallel per arm (or limit arm peak power). "
                           "With rev B both arm DC-DCs are in the centre bay: a second pair needs bay space (156 × 254 mm).")
        if r[0] == "5 Energy" and "traction" in r[1] and r[-1] != "PASS":
            CHANGES.append("Traction DC-DC: 2 × DDR-480C-24 cover peak torque up to 1.5 m/s but not at the 2.49 m/s mechanical max: keep SLS ≤ 1.5 m/s (already the plan) or add a 3rd DDR.")
        if r[0] == "5 Energy" and "SW80" in r[1] and r[-1] != "PASS":
            CHANGES.append("Main contactor: SW80B rating exceeded (else SW180/SW200).")
        if r[0] == "5 Energy" and ("peak battery" in r[1] or "battery duty" in r[1] or "worst sustained" in r[1]) and r[-1] != "PASS":
            CHANGES.append(f"Battery ({r[1]}): {r[2]} vs {r[3]}: stagger arm and traction peaks / cap arm power in the energy manager, or add a 3rd pack.")
        if r[0] == "5 Energy" and "24 V feed" in r[1] and r[-1] != "PASS":
            CHANGES.append(f"Arm 24 V feeds: {r[2]} drop: larger cross-section or remote sense on the arm DC-DCs.")
        if r[0] == "2 Tipping" and "cat-0" in r[1] and r[-1] != "PASS":
            CHANGES.append("Cat-0 stop decel (grip-limited) is close to the tip limit in the worst arm pose: SS1-t (STO delay 1.2 s, ramp ends "
                           "before STO) is used for every stop except power loss / ramp fault; cat-0 stopping distance and 6 % slope holding "
                           "are type tests (TP-03a/b); arms not extended while driving.")
        if r[0] == "2 Tipping" and "lateral" in r[1] and r[-1] != "PASS":
            CHANGES.append(f"Lateral tipping with the arms to one side: {r[2]}: no driving with arms extended sideways; or widen the track.")
        if r[0] == "9 Structure" and r[-1] != "PASS":
            CHANGES.append(f"Structure: {r[1]} -> {r[2]} vs {r[3]}: stiffen the deck under the column foot (transverse 6 × 40 mm rib between "
                           "the spines under the front/rear bolt rows, or a 10 mm doubler under the foot, or a ≥ 15 mm deck; see §9).")
        if r[0] == "3 Load split" and r[-1] != "PASS":
            CHANGES.append(f"Castor springs / roll: {r[1]} = {r[2]} -> see §3.")
        if r[0] == "4 Drive" and r[-1] == "FAIL":
            CHANGES.append(f"Drive: {r[1]} -> {r[2]}.")
        if r[0] == "7 Safety" and r[-1] != "PASS":
            CHANGES.append(f"Safety field: {r[1]} = {r[2]} exceeds the nanoScan3 range: lower the speed band or the arm reach/speed.")
    CHANGES.append(f"Centre-bay ventilation: ~{lim['q_bay']:.0f} W (2 arm DC-DCs + Jetson) in the closed bay between the batteries; the E40 fans "
                   "serve the side bays. Add an air path through the spines or a dedicated fan; heat-run test.")
    CHANGES.append("amr_params.CABLE_PASS comment says '48 V arm buses': with the arm DC-DCs in the centre bay the buses through the "
                   "grommet are 24 V (2 × up to 30 A): fix the comment and size the grommet for 2 × 4 mm² pairs + Ethernet + safety loop.")
    CHANGES.append("Column foot: the 8 × M6 are now tapped in the 10 mm 6082 deck (was the 8 mm adapter): thread engagement ≥ 9 mm "
                   "or helicoils; drawing note.")
    CHANGES.append("Operating rule (no waist): rotate in place only with the arms parked; no driving with the arms extended "
                   "sideways or to the rear (side/rear poses govern the lateral and acceleration tip limits, §2).")
    CHANGES.append(f"amr_params.SUSP quotes the rev A spring limit (k ≤ 30.7 N/mm); rev B (lighter, empty robot {total_cog('empty')[0]:.1f} kg) gives "
                   f"F_inst {lim['Fi']:.0f} N per castor (40 % drive share each, empty) and k ≤ {lim['k_max'] / 1000:.1f} N/mm (35 % with {FLOOR_DZ:g} mm floor "
                   "unevenness): update the comment and the castor purchase spec.")
    seen = set()
    out = []
    for c in CHANGES:
        if c not in seen:
            seen.add(c)
            out.append(c)
    CHANGES[:] = out
    for i, c in enumerate(out, 1):
        md(f"{i}. {c}")
    md()
    md("No supplier confirmation is needed any more for the base (`VERIFICATION.md`, 93 items: 73 CLOSED, 8 REPLACE applied in rev B2, "
       "12 RESIDUAL). The remaining unknowns are measured in type tests: SWD reaction time t_drive (TP-01), cat-0 stopping distance and "
       "6 % slope holding (TP-03a/b), regen without a chopper (TP-03/TP-14), BMS behaviour (TP-14). Outside the base: Kassow DC power "
       "(arm variant C48), OpenArm stopping time and gripper force (measure).")
    md()


def inputs_table():
    md("## Inputs and sources")
    md()
    table(["input", "value", "unit", "tag", "source"], [[n, v if isinstance(v, str) else f"{v:g}", u, t, s] for n, v, u, t, s in INPUTS])


if __name__ == "__main__":
    lim = main()
    lim = sec3(lim)
    lim = sec2b(lim)
    lim = sec4(lim)
    lim = sec5(lim)
    lim = sec6(lim)
    lim = sec7(lim)
    lim = sec8(lim)
    lim = sec9(lim)
    limits_and_changes(lim)
    finish()
    changes(lim)
    inputs_table()
    (HERE / "CALC.md").write_text("\n".join(MD) + "\n")
    n = {s: sum(1 for r in RES if r[-1] == s) for s in ("PASS", "WARN", "FAIL")}
    print(f"CALC.md written: {n['PASS']} PASS, {n['WARN']} WARN, {n['FAIL']} FAIL")
    m_e, m_w = total_cog("empty")[0], total_cog("fwd")[0]
    print(f"  mass: base {m_base:.1f} kg, superstructure {m_sup0:.1f} kg, robot {m_e:.1f} kg empty / {m_w:.1f} kg loaded")
    W = lim["worst"]
    print(f"  tip limits (SF 2, worst poses): decel {W['decel']:.2f} ({lim['worst_gov']['decel']}), accel {W['accel']:.2f} "
          f"({lim['worst_gov']['accel']}), lateral {W['lat']:.2f} ({lim['worst_gov']['lat']}), wheel lift {W['lat_lift']:.2f} m/s²")
    print(f"  swept radius: base {R_BASE:.0f} mm, superstructure {R_SUP:.0f} mm ({R_SUP_PART}), whole robot {R_SWEPT:.0f} mm; "
          f"overhang {OVH:.0f} mm; rotate-in-place ≤ {math.degrees(lim['w_cfg']):.0f} °/s")
    print(f"  fields: rotate-in-place circle R {lim['R_rot']:.0f} mm; arm field R {lim['R_arm']:.0f} mm")
    rt = lim["runtime"]
    print("  runtime: " + ", ".join(f"{v.split()[0]} {k} {h:.1f} h" for (v, k), h in rt.items()))
    print(f"  charge 20->90 %: {lim['t_chg']:.2f} h; deck σ {lim['deck']['sig']:.0f} MPa, δ {lim['deck']['d']:.2f} mm, foot M {lim['deck']['M']:.0f} Nm")
    for r in RES:
        if r[-1] != "PASS":
            print(f"  {r[-1]:4s} [{r[0]}] {r[1]}: {r[2]} (limit {r[3]})")
    print("Required changes:")
    for c in CHANGES:
        print("  -", c)
