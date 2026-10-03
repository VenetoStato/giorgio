#!/usr/bin/env python3
"""Draw the Giorgio 24 V base-powered architecture (Ranger Air) - SVG + PNG 1920x1080 from netlist_rangerair.yaml.

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
MIR = False
NET = yaml.safe_load((HERE / "netlist_rangerair.yaml").read_text())
OUT = "power_safety_architecture_rangerair"
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
txt(40, 40, "Giorgio  -  power & safety architecture  (Ranger Air, base-powered 24 V)", size=24, bold=True)
txt(40, 72, "no own pack, no own dock: superstructure fed from the Ranger Air accessory output (24-29.6 V, <= 25 A / 600 W)   ·   PELV   ·   "
            "safety PL d / Cat 3   ·   arms SS1-t   ·   rev E2.1", size=12, color=MUTED)

# ================================================================== base
box(30, 112, 330, 230, "AgileX OEM charging dock", ["automatic recharging (manufacturer feature)", "specs UNVERIFIED: power, contact type,",
    "payload powered while docked?", "-> AGILEX_REQUEST.md"], dom="AC", fill="white", title_size=12)
box(30, 380, 330, 290, "AgileX Ranger Air (base)", ["internal LFP 24 V 30 Ah = 0.77 kWh", "own BMS, traction, onboard E-stop",
    "accessory output 24-29.6 V", "<= 25 A / 600 W (peak UNVERIFIED)", "rear port: power + CAN", "no external safety-stop input documented",
    "payload 80 kg -> superstructure <= 64-68 kg"], dom="T24", title_size=12.5)
arrow((195, 342), (195, 380), "AC")
txt(205, 360, "charges the base battery", size=8.6, color=MUTED)

BX = 500
wire([(360, 600), (488, 600)], "B48", lw=4.5)
fuse(398, 600, fl("F0"))
contact(452, 600, "Q0")
txt(40, 690, "Q0 = SB50 service disconnect (open only with the base output off)", size=8.4, color=MUTED)
wire([(BX, 150), (BX, 965)], "B48", lw=8)
wire([(488, 600), (BX, 600)], "B48", lw=4.5)
txt(BX - 8, 990, "B24 busbar 24 - 29.6 V (base port)", size=10, color=COL["B48"], bold=True)
txt(515, 625, "power manager: 3x INA228 (arm L, arm R, total) keeps the port <= 600 W", size=8.4, color=COL["B48"], bold=True)

# ================================================================== arms (direct 24 V)
Y_ARM = 232
wire([(BX, Y_ARM), (770, Y_ARM)], "B48", lw=3)
fuse(548, Y_ARM, fl("F1"))
contact(612, Y_ARM, "K1")
contact(690, Y_ARM, "K2")
wire([(668, Y_ARM), (668, Y_ARM + 44), (712, Y_ARM + 44), (712, Y_ARM)], "B48", lw=1.5)
ax.add_patch(Rectangle((678, Y_ARM + 38), 24, 12, fc="white", ec=COL["B48"], lw=1.4, zorder=5))
txt(690, Y_ARM + 62, "K3 + 10 Ω precharge", size=8.4, ha="center")
box(520, 318, 262, 58, "Peak buffer 8s 6 Ah LFP, 1.9 kg", ["154 Wh · 30 A / 5 s · F12 · ideal diode", "3 A charger from B24 (leftover)"], dom="A24", title_size=10)
wire([(585, 318), (585, Y_ARM)], "A24", lw=2.4)
txt(548, Y_ARM + 22, "17.5 A limiter", size=8.2, ha="center", color=COL["B48"], bold=True)
txt(651, Y_ARM - 52, "K1, K2: 3RT2036 (S2), after buffer node", size=8.4, ha="center", color=MUTED)
txt(651, Y_ARM - 37, "mirror contacts -> PNOZ EDM", size=8.4, ha="center", color=MUTED)
wire([(770, 172), (770, 292)], "B48", lw=3)
for y0, side, fid in ((172, "left", "F10"), (292, "right", "F11")):
    wire([(770, y0), (800, y0)], "B48", lw=3)
    box(800, y0 - 32, 196, 64, f"Regen clamp {side}", ["30.8 V shunt + 2.2 Ω", "(Damiao OVP 32 V)"], dom="A24")
    wire([(996, y0), (1090, y0)], "A24", lw=3.4)
    fuse(1043, y0, fl(fid), "A24")
    box(1090, y0 - 32, 238, 64, f"OpenArm 2.0 {side}", ["210 W sust. / 550 W 5 s (buffer)", "no brakes, no STO · CAN 1 Mbit/s"], dom="A24")

rows = [
    (430, "F2", "DC-DC safety 24 V", ["Mean Well DDR-60G-24", "regulated (PNOZ <= 26.4 V)"], "S24", None),
    (552, "F3", "DC-DC 12 V", ["Mean Well DDR-120B-12", "Jetson capped at 50 W mode"], "LV",
     ("Jetson AGX Orin 64 GB", ["USB: Gemini 336L, 2x UVC fisheye,", "PCAN-USB FD x2"])),
    (668, "F4", "DC-DC 5 V", ["Mean Well DDR-60G-5", "5 V 10.8 A"], "LV",
     ("Face & status UI", ["32x16 LED face (50 %), 2x GC9A01,", "status LEDs, ESP32"])),
]
for y0, fid, title, lines, dom, load in rows:
    wire([(BX, y0), (800, y0)], "B48", lw=2.6)
    fuse(560, y0, fl(fid))
    box(800, y0 - 32, 196, 64, title, lines, dom=dom)
    if load:
        wire([(996, y0), (1090, y0)], dom, lw=3)
        box(1090, y0 - 32, 238, 64, load[0], load[1], dom=dom)
fuse(1043, 552, fl("F30"), "LV")
fuse(1043, 668, fl("F40"), "LV")

Y_COF = 800
wire([(BX, Y_COF), (1090, Y_COF)], "B48", lw=2.6)
fuse(560, Y_COF, fl("F6"))
contact(700, Y_COF, "K4")
box(1090, Y_COF - 32, 238, 64, "Coffee (barista)", ["24 V capsule machine ~300 W", "arms parked, bus <= 27.6 V"], dom="A24")
txt(560, Y_COF + 50, "interlock (power manager): brewing XOR arm motion; brew only at bus <= 27.6 V (heater 456 W at 29.6 V)",
    size=8.4, color=MUTED)

wire([(996, 430), (1030, 430), (1030, 392), (1395, 392)], "S24", lw=2.4)
txt(1040, 380, "S24 -> PNOZ, scanners, E-stops, K1/K2/K4 coils", size=8.8, color=COL["S24"], bold=True)
wire([(1328, 545), (1342, 545), (1342, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 292), (1328, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 172), (1342, 292)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1342, 172), (1328, 172)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
wire([(1090, 600), (1060, 600), (1060, 905), (360, 905), (360, 640)], "CAN", lw=1.8, ls=(0, (1, 2.2)))
txt(700, 918, "CAN to Ranger Air (500 kbit/s, isolated PCAN): motion, zero-speed stop, battery SoC", size=8.6, color=COL["CAN"], bold=True)

# ================================================================== safety panel
SX, SY, SW = 1395, 112, 495
box(SX, SY, SW, 760, "Safety chain   (PL d, Cat 3)", dom="SAFE", fill="white", title_size=13)
box(SX + 16, SY + 42, 222, 66, "2x E-stop  (2 NC)", ["Eaton M22-PV/K02 (IEC 60947-5-5)", "front + rear, stop category 1"], dom="SAFE")
box(SX + 257, SY + 42, 222, 66, "2x SICK nanoScan3", ["Type 3, PL d, PFHd 8e-8, OSSDs", "fields: drive / work"], dom="SAFE")
box(SX + 16, SY + 120, 222, 50, "Reset + mode key", ["manual reset, no auto-restart"], dom="SAFE")
box(SX + 257, SY + 120, 222, 50, "K1/K2 mirror contacts", ["EDM feedback before reset"], dom="SAFE")
box(SX + 92, SY + 200, 310, 74, "Pilz PNOZmulti 2", ["PNOZ m B0 (772100) + EF 4DI4DOR", "+ ES ETH · 24 V regulated (S24)"], dom="SAFE")
for xx, yy in ((SX + 127, SY + 108), (SX + 368, SY + 108), (SX + 127, SY + 170), (SX + 368, SY + 170)):
    wire([(xx, yy), (xx, SY + 186), (SX + 247, SY + 186), (SX + 247, SY + 200)], "SAFE", lw=1.5, ls=(0, (3, 2)))
txt(SX + 18, SY + 300, "Stop sequence on any trip", size=10.5, bold=True)
outs = [("t = 0", "SS1 request -> Jetson: controlled stop of both arms"),
        ("t = 0", "Ranger Air: CAN zero-speed - not safety-rated"),
        ("t = 0", "coffee: K4 opens (stop category 0)"),
        ("t = 0.5 s", "delayed safe outputs open K1 + K2: arm power removed")]
for i, (t, s_) in enumerate(outs):
    yy = SY + 326 + i * 25
    txt(SX + 18, yy, t, size=9, color=COL["SAFE"], bold=True)
    txt(SX + 100, yy, s_, size=9)
box(SX + 16, SY + 440, 463, 118, "Stays powered in any stop", [
    "PNOZ, scanners, E-stop circuit, Jetson, cameras, face/status LEDs.",
    "All of it depends on the base port: if the base cuts its output",
    "(low battery / base E-stop) the whole superstructure goes dark",
    "and the arms drop -> park pose before low-SoC cut-off."], dom="S24", fill="white")
box(SX + 16, SY + 572, 463, 170, "Open issues (this architecture)", [
    "Base stop not rated: no external safety input documented (SF3).",
    "Autonomy 0.65 kWh base + 0.12 kWh buffer: P1 3.0 h, P2 2.8 h,",
    "P3 7.9 h (targets 4 / 6 / 8 h) -> dock visits between tasks.",
    "Port 600 W treated as hard limit: arms 210 W sust., 550 W 5 s.",
    "Dock specs and 'payload powered while docked' unverified.",
    "OpenArm: no STO / brakes -> SS1-t + park pose, no handover."], dom="SAFE", fill="#FFF8F8")
wire([(SX, SY + 401), (1368, SY + 401), (1368, 100), (651, 100), (651, Y_ARM - 70)], "SAFE", lw=1.5, ls=(0, (6, 3)))
txt(1000, 92, "K1/K2 coils  <-  PNOZ safe semiconductor outputs (t = 0.5 s)", size=8.8, color=COL["SAFE"], bold=True, ha="center")
wire([(SX, SY + 376), (1380, SY + 376), (1380, Y_COF - 40), (700, Y_COF - 40), (700, Y_COF - 12)], "SAFE", lw=1.5, ls=(0, (6, 3)))

LX, LY = 30, 728
txt(LX, LY, "Legend", size=11, bold=True)
items = [("B48", "-", "24 V base bus (fused branches)"), ("A24", "-", "24 V arm buses (safety-switched)"),
         ("S24", "-", "24 V regulated safety + sensors"), ("LV", "-", "12 V / 5 V compute and UI"),
         ("T24", "-", "base (AgileX, own battery)"), ("SAFE", "--", "safety signals, dual channel"), ("CAN", ":", "CAN bus")]
for i, (k, st, t) in enumerate(items):
    yy = LY + 24 + i * 21
    ls = "-" if st == "-" else ((0, (5, 3)) if st == "--" else (0, (1, 2)))
    ax.plot([LX, LX + 36], [yy, yy], color=COL[k], lw=3, ls=ls)
    txt(LX + 46, yy, t, size=9)
txt(LX, LY + 184, "Checked by calc.py -> CHECKS_RANGERAIR.md", size=8.6, color=MUTED)
txt(1890, 1050, "generated from electrical/netlist_rangerair.yaml by diagram_24v.py  ·  part numbers indicative, see ARCHITECTURE.md §15",
    size=9, color=MUTED, ha="right")
fig.savefig(HERE / (OUT + ".svg"), facecolor=BG)
fig.savefig(HERE / (OUT + ".png"), dpi=100, facecolor=BG)
print("wrote " + OUT + ".svg/.png")
