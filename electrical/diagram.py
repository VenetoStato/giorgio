#!/usr/bin/env python3
"""Draw the Giorgio power + safety architecture (SVG + PNG 1920x1080) from netlist.yaml.

Usage:  python diagram.py      (needs matplotlib + PyYAML; e.g. ~/IsaacLab/env_isaaclab/bin/python)
Outputs: power_safety_architecture.svg / .png next to this file.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import yaml

HERE = Path(__file__).resolve().parent
import sys
MIR = "--mir250" in sys.argv
RM = "--rangermini" in sys.argv
RB = "--rbtheron" in sys.argv or RM
NET = yaml.safe_load((HERE / ("netlist_rangermini.yaml" if RM else "netlist_rbtheron.yaml" if RB else "netlist_mir250.yaml" if MIR else "netlist.yaml")).read_text())
OUT = ("power_safety_architecture_rangermini" if RM else "power_safety_architecture_rbtheron" if RB
       else "power_safety_architecture_mir250" if MIR else "power_safety_architecture")
BNAME = "Ranger Mini" if RM else "RB-THERON"
C = {c["id"]: c for c in NET["components"]}
FZ = {f["id"]: C[f["component"]] for f in NET["fuses"]}
B = NET["battery"]
AH = B["cell"]["ah"] * B["parallel"]
E_KWH = B["series"] * B["cell"]["v_nom"] * AH / 1000


def fl(fid):
    return f"{fid}  {FZ[fid]['short']}"


BG, INK, MUTED = "#F7F8FA", "#1F2933", "#5F6B7A"
COL = {"B48": "#D9480F", "A24": "#1C7ED6", "S24": "#2B8A3E", "LV": "#7048E8", "T24": "#7B858F",
       "AC": "#495057", "SAFE": "#E03131", "CAN": "#E8890C"}
FILL = {"B48": "#FFF4E6", "A24": "#E7F5FF", "S24": "#EBFBEE", "LV": "#F3F0FF", "T24": "#F1F3F5",
        "AC": "#F8F9FA", "SAFE": "#FFF5F5"}

plt.rcParams["font.family"] = "DejaVu Sans"
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1920)
ax.set_ylim(1080, 0)
ax.axis("off")
fig.patch.set_facecolor(BG)


def box(x, y, w, h, title, lines=(), dom="B48", title_size=11.5, dashed=False, fill=None, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=9",
                                fc=fill or FILL.get(dom, "white"), ec=COL[dom], lw=lw,
                                ls=(0, (5, 3)) if dashed else "-", zorder=3))
    ax.text(x + 11, y + 18, title, fontsize=title_size, fontweight="bold", color=INK, va="center", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + 11, y + 38 + i * 16.5, ln, fontsize=9.0, color=INK if i == 0 else MUTED, va="center", zorder=4)


def wire(pts, dom="B48", lw=2.6, ls="-", z=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=COL[dom], lw=lw, ls=ls, solid_capstyle="round", solid_joinstyle="round", zorder=z)


def arrow(p0, p1, dom, lw=2.0):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color=COL[dom], lw=lw, mutation_scale=13), zorder=4)


def fuse(x, y, label, dom="B48", above=True):
    ax.add_patch(FancyBboxPatch((x - 15, y - 7), 30, 14, boxstyle="round,pad=0,rounding_size=3", fc="white", ec=COL[dom], lw=1.5, zorder=5))
    ax.plot([x - 10, x + 10], [y, y], color=COL[dom], lw=1.1, zorder=6)
    ax.text(x, y - 13 if above else y + 15, label, fontsize=8.6, color=INK, ha="center", va="bottom" if above else "top", zorder=6)


def contact(x, y, label, dom="B48"):
    ax.plot([x - 16, x - 7], [y, y], color=COL[dom], lw=2.6, zorder=5)
    ax.plot([x - 7, x + 8], [y, y - 10], color=COL[dom], lw=2.6, zorder=5)
    ax.plot([x + 8, x + 16], [y, y], color=COL[dom], lw=2.6, zorder=5)
    ax.plot([x + 8], [y], marker="o", ms=3.5, color=COL[dom], zorder=5)
    ax.text(x, y + 16, label, fontsize=9, ha="center", va="center", color=INK, fontweight="bold", zorder=6)


def txt(x, y, s, size=9.0, color=INK, bold=False, ha="left"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va="center", fontweight="bold" if bold else "normal", zorder=6)


# ================================================================== title
txt(40, 40, "Giorgio  -  power & safety architecture" + (f"  ({BNAME} base, own 48 V pack)" if RB else "  (product: MiR250 base)" if MIR else "  (prototype: Tracer 2.0 base)"), size=24, bold=True)
txt(40, 72, f"15s{B['parallel']}p LiFePO4 48 V {AH:.0f} Ah ({E_KWH:.2f} kWh)   ·   every on-board circuit PELV <= 60 V DC   ·   "
            f"safety functions PL d / Cat 3 (EN ISO 13849-1)   ·   stop category 1 (SS1-t) for arms   ·   rev {NET['meta']['revision'].split(' ')[0]}",
    size=12, color=MUTED)

# ================================================================== station / base (RB-THERON)
if RB:
    if RM:
        box(30, 112, 330, 92, "AgileX charging kit (NAVIS)", ["auto-docking via NAVIS; price/specs UNVERIFIED", "54.9 V x 10.9 A = 598 W assumed (API example)"], dom="AC", fill="white", title_size=11)
    else:
        box(30, 112, 330, 92, "Robotnik charging station (included)", ["contact dock; robotnik_charge (ROS 2, BSD-3)", "switches a charge relay; power UNVERIFIED (600 W ass.)"], dom="AC", fill="white", title_size=11)
    arrow((195, 204), (195, 228), "AC")
    if RM:
        box(30, 228, 330, 150, "AgileX Ranger Mini 3.0 (base)", ["LFP 48 V 24 Ah = 1.15 kWh, 75 kg, 120 kg payload", "accessory out 46-50 V <= 15 A / 720 W",
            "(cut below 10 % SOC); 4WD/4WS, 2 m/s", "own ~40 W (incl. NAVIS) + traction 100-600 W [A]", "no external E-stop / safety input",
            "CAN 500 kbit/s (ranger_ros2) + NAVIS"], dom="T24", title_size=11.5)
    else:
        box(30, 228, 330, 150, "Robotnik RB-THERON (base)", ["48 V 15 Ah = 0.72 kWh, 70 kg, 200 kg payload", "safety PLC + 2 safety LiDARs, i7 PC, CE",
            "outputs 12 V / 24 V / VBATT (ratings UNVERIFIED)", "own load ~70 W + traction 60-350 W [A]", "external safety I/O for payload: NOT documented",
            "ROS 2 over Ethernet (cmd_vel, stop, SoC)"], dom="T24", title_size=11.5)
    wire([(360, 352), (395, 352), (395, 430)], "T24", lw=2.4)
    fuse(395, 372, "", above=True)
    ax.add_patch(FancyBboxPatch((372, 395), 46, 30, boxstyle="round,pad=0,rounding_size=4", fc="white", ec=COL["T24"], lw=1.4, zorder=5))
    txt(395, 410, "Orion", size=7.6, ha="center")
    wire([(395, 425), (395, 520)], "B48", lw=2.4)
    arrow((395, 500), (395, 532), "B48")
    wire([(395, 532), (360, 532)], "B48", lw=2.4)
    for k_, t_ in enumerate([("48 V port" if RM else "VBATT") + " -> F17 -> Orion-Tr 48/48-6 (isolated)", "6 A / 54.0 V -> F18 -> our pack:",
                             "the ONE " + ("AgileX" if RM else "Robotnik") + " dock charges both.", "Jetson: on when docked / balancing,",
                             "off while traction > " + ("150" if RM else "100") + " W."]):
        txt(40, 392 + k_ * 15, t_, size=8.4, color=MUTED)
else:
    # ================================================================== station
    box(30, 112, 330, 312, "Docking station  (230 V mains)", dom="AC", fill="white", title_size=12)
    box(48, 148, 294, 66, "LFP charger  " + C["CHG_DOCK"]["short"], ["CC/CV 54.0 V (3.60 V/cell), 21 A, 1.2 kW", "charge profile + limits from BMS over CAN"], dom="AC")
    box(48, 232, 294, 66, "Station controller + relay", ["contacts energised ONLY after signature +", "Wi-Fi handshake; off < 100 ms on loss"], dom="AC")
    box(48, 316, 294, 90, "Roboteq RoboPad contacts", ["RPCOL90-100 + RPBAS90-100, 75 A, 75 V", "2 poles, 10 mm stroke, +/-5 mm", "robot side dead when undocked"], dom="AC")
    wire([(195, 214), (195, 232)], "AC", lw=2)
    wire([(195, 298), (195, 316)], "AC", lw=2)

    # charge path into pack
    wire([(342, 361), (395, 361), (395, 520)], "B48", lw=2.4)
    arrow((395, 500), (395, 532), "B48")
    fuse(395, 430, "", above=True)
    txt(380, 446, "F9  " + FZ["F9"]["short"] + "  ·  ideal diode: no backfeed to contacts", size=8.4, color=MUTED, ha="right")
    wire([(395, 532), (360, 532)], "B48", lw=2.4)

# ================================================================== battery
box(30, 470, 330, 196, "Battery pack", [f"15s{B['parallel']}p LiFePO4 48 V {AH:.0f} Ah = {E_KWH:.2f} kWh",
    "75 x 32700 6 Ah cells, >= 1.2 C / 2 C, 13 kg", "certified IEC 62619 + UN 38.3, CE / EMC",
    "V range 37.5 - 54.75 V (cut-off - full)", f"bolted Isc ~ {NET['meta']['isc_ka_note']} kA (calc.py)",
    "key switch -> BMS enable"], dom="B48", title_size=12.5)
# main path
wire([(360, 600), (488, 600)], "B48", lw=4.5)
fuse(398, 600, fl("F0"))
contact(452, 600, "Q0")
txt(40, 684, "Q0 = service disconnect (SB120 + lockout), pulled after key-off", size=8.4, color=MUTED)

# busbar
BX = 500
wire([(BX, 150), (BX, 965)], "B48", lw=8)
wire([(488, 600), (BX, 600)], "B48", lw=4.5)
txt(BX - 8, 990, "B48 busbar 37.5 - 54.75 V", size=10, color=COL["B48"], bold=True, ha="left")

# ================================================================== arm branch
Y_ARM = 232
wire([(BX, Y_ARM), (770, Y_ARM)], "B48", lw=3)
fuse(548, Y_ARM, fl("F1"))
contact(612, Y_ARM, "K1")
contact(690, Y_ARM, "K2")
# precharge K3 + R across K2
wire([(668, Y_ARM), (668, Y_ARM + 44), (712, Y_ARM + 44), (712, Y_ARM)], "B48", lw=1.5)
ax.add_patch(Rectangle((678, Y_ARM + 38), 24, 12, fc="white", ec=COL["B48"], lw=1.4, zorder=5))
txt(690, Y_ARM + 62, "K3 + 47 Ω precharge", size=8.4, ha="center")
txt(651, Y_ARM - 52, "K1, K2: Siemens 3RT2036 (S2)", size=8.4, ha="center", color=MUTED)
txt(651, Y_ARM - 37, "mirror contacts -> PNOZ EDM", size=8.4, ha="center", color=MUTED)
wire([(770, 172), (770, 292)], "B48", lw=3)
for y0, side, fid, cid in ((172, "LEFT", "F1L", "F10"), (292, "RIGHT", "F1R", "F11")):
    wire([(770, y0), (800, y0)], "B48", lw=3)
    box(800, y0 - 32, 196, 64, f"DC-DC arm {side.lower()}", ["DDR-480C-24, lying + fan", "24 V 20 A, peak 30 A / 5 s"], dom="A24")
    txt(785, y0 - 42 if side == "LEFT" else y0 + 44, fl(fid), size=8.0, ha="center", color=MUTED)
    wire([(996, y0), (1090, y0)], "A24", lw=3.4)
    fuse(1050, y0, fl(cid), "A24")
    box(1090, y0 - 32, 238, 64, f"OpenArm 2.0 {side.lower()}", ["2x J8009P · 2x J4340P · 4x J4310", "no brakes, no STO · CAN 1 Mbit/s"], dom="A24")
    # ORing + clamp
    ax.add_patch(FancyBboxPatch((1006, y0 + 12), 76, 30, boxstyle="round,pad=0,rounding_size=4", fc="white", ec=COL["A24"], lw=1.2, zorder=5))
    txt(1044, y0 + 21, "ORing +", size=7.2, ha="center")
    txt(1044, y0 + 34, "27.5 V clamp", size=7.2, ha="center")
    wire([(1044, y0), (1044, y0 + 12)], "A24", lw=1.4)

# ================================================================== other branches
rows = [
    (430, "F2", "DC-DC safety 24 V", ["Mean Well DDR-120C-24", "always on, also in E-stop"], "S24", None),
    (552, "F3", "DC-DC 12 V", ["Mean Well DDR-120C-12", "12 V 10 A, 15 A for 3 s"], "LV",
     ("Jetson AGX Orin 64 GB", ["15-60 W · USB: Gemini 336L,", "2x UVC fisheye, PCAN-USB FD x2"])),
    (668, "F4", "DC-DC 5 V", ["Mean Well DDR-60L-5", "5 V 12 A"], "LV",
     ("Face & status UI", ["32x16 LED face, 2x GC9A01 eyes,", "status LEDs, ESP32"])),
] + ([] if (MIR or RB) else [
    (784, "F5", "Tracer charger", ["Victron Orion-Tr 48/24-16", "10 A -> 2-pin charge port"], "T24",
     ("AgileX Tracer 2.0", ["own 24 V 30 Ah LFP + BMS", "stop via CAN only (no safety input)"])),
])
if MIR:
    box(1090, 752, 238, 64, "MiR250 base (product)", ["own Li-ion battery + MiR charger,", "aux E-stop input <- PNOZ (PL d)"], dom="T24")
for y0, fid, title, lines, dom, load in rows:
    wire([(BX, y0), (800, y0)], "B48", lw=2.6)
    fuse(560, y0, fl(fid))
    box(800, y0 - 32, 196, 64, title, lines, dom=dom)
    if load:
        wire([(996, y0), (1090, y0)], dom, lw=3)
        box(1090, y0 - 32, 238, 64, load[0], load[1], dom=dom)
fuse(1043, 552, fl("F30"), "LV")
fuse(1043, 668, fl("F40"), "LV")
if not (MIR or RB):
    fuse(1043, 784, fl("F7"), "T24")

# coffee (default at dock)
Y_COF = 900
wire([(BX, Y_COF), (800, Y_COF)], "B48", lw=2.6)
fuse(560, Y_COF, fl("F6"))
box(800, Y_COF - 32, 196, 64, "DC-DC coffee 24 V", ["Mean Well DDR-480C-24", "remote OFF + K4 by PNOZ"], dom="A24")
wire([(996, Y_COF), (1090, Y_COF)], "A24", lw=3)
fuse(1043, Y_COF, fl("F60"), "A24")
box(1090, Y_COF - 32, 238, 64, "Coffee backpack (barista)", ["24 V DC capsule machine 300 W,", "shuttle MCU · ~3 min, 16 Wh / cup"], dom="A24")
txt(800, Y_COF + 50, "alternatives: brew at the dock with a stock 230 V machine (no load on robot) · 230 V inverter on board rejected (1.4 kW, 2.35 C)",
    size=8.4, color=MUTED)

# S24 distribution towards safety panel
wire([(996, 430), (1030, 430), (1030, 392), (1395, 392)], "S24", lw=2.4)
txt(1040, 380, "S24 -> PNOZ, scanners, E-stops, K1/K2 coils", size=8.8, color=COL["S24"], bold=True)

# CAN (dotted)
wire([(1328, 545), (1342, 545), (1342, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 292), (1328, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 172), (1342, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 172), (1328, 172)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
if not RB:
    wire([(1328, 562), (1342, 562), (1342, 784), (1328, 784)], "CAN", lw=1.8, ls=(0, (1, 2.2)))  # MiR: Ethernet REST on the same route
txt(1336, 470, "CAN", size=8.4, color=COL["CAN"], bold=True, ha="right")

# ================================================================== safety panel
SX, SY, SW = 1395, 112, 495
box(SX, SY, SW, 760, "Safety chain   (PL d, Cat 3)", dom="SAFE", fill="white", title_size=13)
box(SX + 16, SY + 42, 222, 66, "2x E-stop  (2 NC)", ["Eaton M22-PV/K02 (IEC 60947-5-5)", "front + rear, stop category 1"], dom="SAFE")
if MIR:
    box(SX + 257, SY + 42, 222, 66, "MiR250 safety system", ["2x nanoScan3 inside the base", "safe stop output: TBC with MiR"], dom="SAFE")
else:
    box(SX + 257, SY + 42, 222, 66, "2x SICK nanoScan3", ["Type 3, PL d, PFHd 8e-8, OSSDs", "fields: drive / dock / work"], dom="SAFE")
box(SX + 16, SY + 120, 222, 50, "Reset + mode key", ["manual reset, no auto-restart"], dom="SAFE")
box(SX + 257, SY + 120, 222, 50, "K1/K2 mirror contacts", ["EDM feedback before reset"], dom="SAFE")
PN = (SX + 92, SY + 200, 310, 74)
box(*PN, "Pilz PNOZmulti 2", ["PNOZ m B0 (772100) + EF 4DI4DOR", "PL e capable · 24 V from S24"], dom="SAFE")
for xx, yy in ((SX + 127, SY + 108), (SX + 368, SY + 108), (SX + 127, SY + 170), (SX + 368, SY + 170)):
    wire([(xx, yy), (xx, SY + 186), (SX + 247, SY + 186), (SX + 247, SY + 200)], "SAFE", lw=1.5, ls=(0, (3, 2)))

txt(SX + 18, SY + 300, "Stop sequence on any trip", size=10.5, bold=True)
outs = [("t = 0", "SS1 request -> Jetson: controlled stop of both arms via CAN"),
        (("t = 0", "relay output -> MiR250 auxiliary E-stop (PL d)") if MIR else ("t = 0", "Ranger Mini: CAN zero-speed - not safety-rated") if RM else ("t = 0", "RB-THERON: ROS 2 stop; safety-PLC link TBC (not rated)") if RB
         else ("t = 0", "Tracer: CAN zero-speed (500 ms timeout) - not rated")),
        ("t = 0", "coffee: K4 opens + DC-DC off (stop category 0)"),
        ("t = 0.45 s", "DC-DC remote OFF (non-safety, pre-empts arcing)"),
        ("t = 0.5 s", "delayed safe outputs open K1 + K2: arm power removed")]
for i, (t, s) in enumerate(outs):
    yy = SY + 326 + i * 25
    txt(SX + 18, yy, t, size=9, color=COL["SAFE"], bold=True)
    txt(SX + 100, yy, s, size=9)

box(SX + 16, SY + 460, 463, 118, "Stays powered in any stop", [
    "PNOZ, scanners, E-stop circuit, Jetson, cameras, face and status",
    "LEDs, BMS, Wi-Fi." + (" MiR250: stopped by its own safety system." if MIR else " Ranger Mini: held at zero speed via CAN." if RM else " RB-THERON: own PLC; ours via ROS 2." if RB else " Tracer: held at zero speed via CAN only."),
    "Arms: power removed after SS1. No brakes -> park pose on",
    "mechanical rests before the cut; cup placed, not handed over."], dom="S24", fill="white")
box(SX + 16, SY + 592, 463, 150, "Open certification issues", [
    *(["MiR250: safe protective-stop OUTPUT to the PNOZ not documented", "(SF2 FAIL in CHECKS_MIR250.md) -> MiR user guide / quote."] if MIR else
      ["Ranger Mini: no external safety-stop input (SF3 FAIL in", "CHECKS_RANGERMINI.md) -> ask AgileX; dock kit unverified."] if RM else
      ["RB-THERON safety PLC: no documented payload E-stop / safe I/O", "(SF3 FAIL in CHECKS_RBTHERON.md) -> ask Robotnik; P2 4.9 h < 6 h."] if RB else
      ["Tracer 2.0 has no external safety input: base stop path", "unrated (SF3 FAIL) - accepted for the prototype; product: MiR250."]),
    "OpenArm: no STO / brakes / safety-rated monitoring -> no PFL;",
    "arms only move when protective field is clear (SSM by scanners).",
    "Contactor DC-1 rating and gPV fuse IR: verify datasheets.",
    "Speed-dependent field switching needs a safe speed signal."], dom="SAFE", fill="#FFF8F8")

# safety signal routes (dashed red)
wire([(SX, SY + 404), (1368, SY + 404), (1368, 100), (651, 100), (651, Y_ARM - 70)], "SAFE", lw=1.5, ls=(0, (6, 3)))
txt(1000, 92, "K1/K2 coils  <-  PNOZ safe semiconductor outputs (t = 0.5 s)", size=8.8, color=COL["SAFE"], bold=True, ha="center")

# ================================================================== legend + notes
LX, LY = 30, 728
txt(LX, LY, "Legend", size=11, bold=True)
items = [("B48", "-", "48 V battery bus, fused branches"), ("A24", "-", "24 V arm buses (safety-switched)"),
         ("S24", "-", "24 V safety + sensors (always on)"), ("LV", "-", "12 V / 5 V compute and UI"),
         ("T24", "-", "base domain (own battery)" if (MIR or RB) else "Tracer 24 V domain (isolated)"), ("SAFE", "--", "safety signals, dual channel"),
         ("CAN", ":", "CAN bus")]
for i, (k, st, t) in enumerate(items):
    yy = LY + 24 + i * 21
    ls = "-" if st == "-" else ((0, (5, 3)) if st == "--" else (0, (1, 2)))
    ax.plot([LX, LX + 36], [yy, yy], color=COL[k], lw=3, ls=ls)
    txt(LX + 46, yy, t, size=9)
notes = ["Grounding: battery 0 V bonded to chassis at one point (distribution block);",
         ("Base domain isolated from our pack by the Orion-Tr 48/48 (galvanic)." if RB else "Tracer domain isolated by the Orion-Tr; dock charger output isolated (SELV)."),
         "Fuses: breaking capacity >= pack Isc; ampacity, drops, precharge, regen,",
         "autonomy and PFHd are checked by calc.py -> CHECKS.md."]
for i, s in enumerate(notes):
    txt(LX, LY + 184 + i * 17, s, size=8.6, color=MUTED)
txt(1890, 1050, "generated from electrical/" + ("netlist_rangermini.yaml" if RM else "netlist_rbtheron.yaml" if RB else "netlist_mir250.yaml" if MIR else "netlist.yaml") + " by diagram.py  ·  part numbers indicative, see ARCHITECTURE.md",
    size=9, color=MUTED, ha="right")

if MIR:
    wire([(SX, SY + 351), (1380, SY + 351), (1380, 784), (1328, 784)], "SAFE", lw=1.5, ls=(0, (6, 3)))
fig.savefig(HERE / (OUT + ".svg"), facecolor=BG)
fig.savefig(HERE / (OUT + ".png"), dpi=100, facecolor=BG)
print("wrote " + OUT + ".svg/.png")
