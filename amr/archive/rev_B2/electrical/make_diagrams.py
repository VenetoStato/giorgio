#!/usr/bin/env python3
"""Draw single_line.svg/.png and safety_diagram.svg/.png from netlist_amr.yaml (matplotlib only).

Run: cd ~/giorgio_sim/amr/electrical && ../../cad/.env/bin/python make_diagrams.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
import yaml  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NET = yaml.safe_load(open(os.path.join(HERE, "netlist_amr.yaml")))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "svg.fonttype": "none"})

C = dict(b48="#c0392b", t24="#d68910", s24="#1e8449", a24="#7d3c98", sig="#2e86c1", can="#5d6d7e", zero="#17202a")


def box(ax, x, y, w, h, txt, fc="#ffffff", ec="#34495e", fs=6.5, lw=0.9, ls="-", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.25", fc=fc, ec=ec, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal", wrap=True)
    return (x, y, w, h)


def line(ax, pts, col, lw=1.4, ls="-", label=None, lpos=0.5, fs=5.5):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=col, lw=lw, ls=ls, solid_capstyle="round")
    if label:
        i = max(0, min(len(pts) - 2, int(lpos * (len(pts) - 1))))
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.35, label, fontsize=fs, color=col, ha="center", va="bottom",
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))


def zone(ax, x, y, w, h, name, col):
    ax.add_patch(Rectangle((x, y), w, h, fc=col, ec="none", alpha=0.10, zorder=0))
    ax.text(x + 0.4, y + h - 0.4, name, fontsize=7.5, color=col, ha="left", va="top", weight="bold", alpha=0.9)


def save(fig, name):
    for ext, kw in (("svg", {}), ("png", {"dpi": 110})):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), bbox_inches="tight", **kw)
    plt.close(fig)


# ===================================================================================== single line
def single_line():
    fig, ax = plt.subplots(figsize=(17, 11))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 70)
    ax.axis("off")
    zone(ax, 0, 34, 27, 36, "BATTERY + LEFT POWER BAY (upper rail)", "#2471a3")
    zone(ax, 27, 34, 33, 36, "LEFT POWER BAY: branch fuses + T24 (lower rail)", "#2471a3")
    zone(ax, 60, 34, 20, 36, "RIGHT BAY (safety + AUX48)", "#1e8449")
    zone(ax, 80, 18, 30, 52, "", "#7f8c8d")
    ax.text(109.5, 69.6, "CENTRE BAY (fixed, between batteries)\n-> E53 deck grommet -> superstructure", fontsize=6.8, color="#7f8c8d", ha="right", va="top", weight="bold")
    zone(ax, 0, 0, 40, 33, "DOCK PATH (right bay lower rear) + DOCK STATION", "#7d3c98")
    zone(ax, 40, 0, 40, 17, "COMMUNICATION (CAN-T, CAN-E, LYNK, Ethernet)", "#5d6d7e")

    # batteries
    box(ax, 1, 60, 8, 5, "B01F Discover\nDLP-GC2-48V\n51.2 V 30 Ah\nint. fuse", "#fdebd0", fs=6)
    box(ax, 1, 52, 8, 5, "B01R Discover\nDLP-GC2-48V\n51.2 V 30 Ah\nint. fuse", "#fdebd0", fs=6)
    box(ax, 12, 56, 6, 4, "F0 100 A gG\nNH00 (E10)", "#fadbd8")
    line(ax, [(9, 62.5), (10.5, 62.5), (10.5, 58), (12, 58)], C["b48"], label="H01 25", lpos=0)
    line(ax, [(9, 54.5), (10.5, 54.5), (10.5, 58)], C["b48"], label="H02 25", lpos=0)
    box(ax, 19.5, 56, 6.5, 4, "Q0 ED250B key\nservice disc. (E03)", "#fadbd8")
    line(ax, [(18, 58), (19.5, 58)], C["b48"])
    ax.plot([27.5], [58], "o", color=C["b48"])
    ax.text(23, 62.2, "B48_RAW 40-58.4 V (always on with key)", fontsize=6, color=C["b48"], ha="center")
    line(ax, [(26, 58), (27.5, 58)], C["b48"], label="W02 25", lpos=0)
    box(ax, 19.5, 45.5, 8, 6, "K0 Albright SW80B..A (E11)\n+ K0P 47 R (E12); coil: S24 ->\nG01 R1 NO (energised=OK)\n-> K0V >= 48 V -> K0T 0.6 s\n(D0 diode; no safety ctrl)", "#fadbd8", fs=5.6)
    line(ax, [(27.5, 58), (27.5, 52.5), (23.5, 52.5), (23.5, 51)], C["b48"])
    line(ax, [(23.5, 46), (23.5, 44), (29, 44)], C["b48"], label="W03 25  B48_SW", lpos=0.9)
    # 0 V
    box(ax, 1, 40, 10, 6, "E19 0 V block\nsingle 0V-chassis\nbond W15 6 mm2\n(PELV)", "#eaecee", fs=6)
    line(ax, [(5, 52), (5, 46)], C["zero"], ls="--", label="pack -", lpos=0)

    # B48_RAW branch fuses (always on)
    box(ax, 29, 61, 5, 3, "F1 6 A gPV", "#fadbd8")
    box(ax, 29, 56.5, 5, 3, "F2 16 A gPV", "#fadbd8")
    line(ax, [(27.5, 58), (28.3, 58), (28.3, 62.5), (29, 62.5)], C["b48"])
    line(ax, [(28.3, 58), (29, 58)], C["b48"])
    box(ax, 63, 61, 9, 4, "U4 DDR-240C-24\nS24 10 A (E15)", "#d5f5e3")
    line(ax, [(34, 62.5), (63, 62.5)], C["b48"], label="W04 2x1.5", lpos=0.5)
    line(ax, [(72, 63), (74, 63), (74, 67), (61, 67)], C["s24"])
    ax.text(67, 67.5, "S24 always on: PNOZmulti 2, nanoScan3 x2, K0/K1/K2/K4 coils, switch, gateways, fans",
            fontsize=5.8, color=C["s24"], ha="center")
    line(ax, [(34, 58), (61, 58)], C["b48"], label="E2F WF1-3 (left bay) -> WW2 / H03b/e", lpos=0.3)
    box(ax, 61, 55.5, 8, 4.5, "U5 DDR-120C-12\n+ FJ 8 A (E2G)\n(WF1 6 A in the\nleft bay, E2F)", "#fadbd8", fs=5.3)
    line(ax, [(69, 58), (78, 58), (78, 60), (82, 60)], C["b48"], label="H03b/e", lpos=0.5)

    # B48_SW branches
    fus = [("F3 20 A", 50.5), ("F4 20 A", 47), ("F5L 16 A", 40), ("F5R 16 A", 36.5)]
    line(ax, [(29, 44), (29, 52), (30, 52)], C["b48"])
    for name, y in fus:
        box(ax, 31, y - 1.4, 5, 2.8, name + "\ngPV", "#fadbd8", fs=5.8)
        line(ax, [(29.5, 44), (29.5, y), (31, y)], C["b48"])
    box(ax, 38, 49.4, 8, 3, "U1 DDR-480C-24 (E13)", "#fdebd0", fs=6)
    box(ax, 38, 45.9, 8, 3, "U2 DDR-480C-24 (E14)", "#fdebd0", fs=6)
    line(ax, [(36, 50.5), (38, 50.5)], C["b48"])
    line(ax, [(36, 47), (38, 47)], C["b48"])
    ax.text(42, 52.9, "current share P+/P-; remote from K0 NC aux (short = OFF)", fontsize=5.3, ha="center")
    box(ax, 48, 46.5, 6, 5, "U3 DRDN40-24\nORing", "#fdebd0", fs=6)
    line(ax, [(46, 50.9), (48, 50.9)], C["t24"])
    line(ax, [(46, 47.4), (48, 47.4)], C["t24"])
    line(ax, [(54, 49), (57.5, 49), (57.5, 55.2)], C["t24"], label="T24 W11 10", lpos=0)
    box(ax, 48, 53, 7, 4.5, "R1a/R1b maxon\nDSR 50/5 x2\nclamp 27 V\n(E16)", "#fdebd0", fs=5.8)
    line(ax, [(55, 55.2), (57.5, 55.2)], C["t24"])
    box(ax, 50, 39.5, 4.2, 2.6, "F8L 20 A", "#fdebd0", fs=5.8)
    box(ax, 55, 39.5, 4.2, 2.6, "F8R 20 A", "#fdebd0", fs=5.8)
    line(ax, [(57.5, 49), (57.5, 43.5), (52, 43.5), (52, 42.1)], C["t24"])
    line(ax, [(57.5, 43.5), (57, 43.5), (57, 42.1)], C["t24"])
    box(ax, 44, 26, 7, 3.5, "M1L ez-Wheel\nSWD 125 (24 V)", "#fef9e7", fs=5.8)
    box(ax, 53, 26, 7, 3.5, "M1R ez-Wheel\nSWD 125 (24 V)", "#fef9e7", fs=5.8)
    ax.text(52, 24.8, "drive wheels (fixed base, M12-L 1.5 m)", fontsize=5.5, ha="center")
    line(ax, [(52, 39.5), (52, 35), (47.5, 35), (47.5, 29.5)], C["t24"], label="H04", lpos=0.5)
    line(ax, [(57, 39.5), (57, 33), (56.5, 33), (56.5, 29.5)], C["t24"], label="H05", lpos=0.5)
    # arm feed via K1/K2
    box(ax, 63, 37, 9, 5.5, "K1 + K2 Siemens\n3RT2026 (mirror NC)\nsafety contactors\n2 poles/arm in series", "#d5f5e3", fs=5.8)
    line(ax, [(36, 40), (40, 40), (40, 39.3), (63, 39.3)], C["b48"], label="W08", lpos=0.6)
    line(ax, [(36, 36.5), (61, 36.5), (61, 38.2), (63, 38.2)], C["b48"], label="W09", lpos=0.5)
    line(ax, [(72, 40.5), (78, 40.5), (78, 50), (82, 50)], C["b48"], label="H03c A48L", lpos=0.05)
    line(ax, [(72, 38.5), (79, 38.5), (79, 42), (82, 42)], C["b48"], label="H03d A48R", lpos=0.05)

    # waist plate
    line(ax, [(82, 60), (81, 60), (81, 65.8), (89, 65.8)], C["b48"])
    line(ax, [(82, 60), (89, 60)], C["b48"])
    line(ax, [(69, 56.2), (88, 56.2), (88, 62.7), (99, 62.7)], C["a24"], label="W28 12 V", lpos=0.4)
    box(ax, 89, 64.6, 8, 2.5, "U6 DDR-60L-5", "#ebdef0", fs=5.8)
    box(ax, 89, 58.7, 8, 2.5, "U7 DDR-480C-24", "#ebdef0", fs=5.8)
    box(ax, 99, 61.5, 10, 2.5, "Jetson Orin NX (E51)", "#ffffff", fs=5.8)
    box(ax, 99, 64.6, 10, 2.5, "head LEDs / eyes", "#ffffff", fs=5.8)
    box(ax, 99, 55, 10, 5.2, "K4 Finder 22.32 ->\nFCF 16 A -> E53 ->\n24 V capsule machine\n(PNOZ aux out -> KI4)", "#ffffff", fs=5.6)
    line(ax, [(97, 65.8), (99, 65.8)], C["a24"])
    line(ax, [(97, 60), (98, 60), (98, 57.6), (99, 57.6)], C["t24"])
    for y, s in ((50, "L"), (42, "R")):
        box(ax, 82, y - 2.5, 7, 5, f"UA{s} DDR-480C-24\n(OA, CAD E50)", "#ebdef0", fs=5.6)
        box(ax, 90.5, y - 2.5, 6.5, 5, "DRDN40-24\n+ DSR 50/5\n27 V (E52)", "#ebdef0", fs=5.6)
        box(ax, 98.5, y - 2.5, 10.5, 5, f"FA{s} 25 A -> E53 ->\nOpenArm {s} 24 V 6 mm2\nC48: arm DC box on A48", "#ffffff", fs=5.6)
        line(ax, [(89, y), (90.5, y)], C["a24"])
        line(ax, [(97, y), (98.5, y)], C["a24"])
    ax.text(95, 21.5, "C48 variant: UA*/DRDN/DSR removed, A48L/A48R feed the certified\narm DC boxes directly; K3 precharge (400 A inrush) added in the right bay.",
            fontsize=6, ha="center", color="#7d3c98")

    # dock
    box(ax, 1, 22, 11, 8, "DOCK STATION\nNPB-750-48 (11.3 A,\nDIP flooded 56.8 V,\nClass B) + DC contactor\n+ XD3 OV relay 59 V;\nopen unless Hall +\nsignature + handshake", "#e8daef", fs=5.8)
    box(ax, 14, 23.5, 7.5, 5, "X1 Roboteq\nRPCOL90-100\n60 A cont, Hall\n(H06a <= 2 m)", "#e8daef", fs=5.8)
    line(ax, [(12, 26), (14, 26)], C["b48"], label="pads", lpos=0)
    box(ax, 24, 23.5, 7, 5, "U8 DRDN40-48\nideal diode, 1 input\n(pads never\nback-fed)", "#e8daef", fs=5.8)
    line(ax, [(21.5, 26), (24, 26)], C["b48"], label="H06a 10", lpos=0)
    box(ax, 33, 24.5, 5.5, 3, "F7 32 A gPV", "#fadbd8", fs=5.8)
    line(ax, [(31, 26), (33, 26)], C["b48"])
    line(ax, [(38.5, 26), (39.2, 26), (39.2, 33.5), (27.5, 33.5), (27.5, 58)], C["b48"], label="H06b 10 -> B48_RAW", lpos=0.4)
    box(ax, 14, 14, 9, 6.5, "KS relay (E37, PNOZ\naux output): RSIG 10 k\nacross pads only if\nHall + traction STO", "#d5f5e3", fs=5.6)
    line(ax, [(18.5, 20.5), (18.5, 23.5)], C["sig"], ls="--")
    box(ax, 1, 9, 11, 9.5, "Handshake: idle sense 12 V\nvia 2.2 k; robot shows\n10 k (KS); Wi-Fi/Ethernet\nJetson <-> dock: docked,\nBMS charge enable, SoC;\ncollapse -> open < 100 ms", "#ffffff", fs=5.5)

    # comms
    box(ax, 42, 9, 8, 5, "B01F/B01R\nLYNK (J1939)\nremote ON/OFF", "#eaecee", fs=5.8)
    box(ax, 52, 9, 8, 5, "G01 LYNK II\nR1 NO = OK -> K0\nR3 -> PNOZ info", "#eaecee", fs=5.8)
    box(ax, 62, 9, 9, 5, "CAN1 PEAK PCAN-\nEthernet GW DR\nCAN-T + CAN-E", "#eaecee", fs=5.8)
    box(ax, 73, 9, 6.5, 5, "NET1 switch\n8p (E25)", "#eaecee", fs=5.8)
    line(ax, [(50, 11.5), (52, 11.5)], C["can"], label="W20", lpos=0)
    line(ax, [(60, 11.5), (62, 11.5)], C["can"], label="CAN-E", lpos=0)
    line(ax, [(71, 11.5), (73, 11.5)], C["can"])
    line(ax, [(66.5, 9), (66.5, 4), (48, 4)], C["can"], label="CAN-T W18 -> SWD L, SWD R (M12)", lpos=0.5)
    ax.text(22, 6.2, "no RoboPad CAN (passive part): dock handshake over Wi-Fi / Ethernet", fontsize=5.3, color=C["can"])
    line(ax, [(79.5, 11.5), (85, 11.5), (85, 18)], C["can"], label="H10b Ethernet -> Jetson", lpos=0.3)
    ax.text(55, 1.0, "Bus colours: red B48 / AUX48 / A48 (40-58.4 V), orange T24 / COF24, green S24, purple A24 / C12 / L5, grey comms. "
            "Cable IDs = cable_schedule.csv; CAD harness IDs H01..H10.", fontsize=6, ha="center")
    ax.set_title("Giorgio AMR - power single-line diagram (rev B2, 2026-10-05, no waist joint) - netlist_amr.yaml", fontsize=11, weight="bold")
    save(fig, "single_line")


# ===================================================================================== safety diagram
def safety():
    io = NET["safety_io"]
    scm = NET["safety_controller"]["modules"]
    mods = list(io.keys())
    rows = 0
    for m in mods:
        rows += max(len([1 for v in io[m]["inputs"].values() if not v["sig"].startswith("spare")]),
                    len(io[m].get("outputs", {})) + len(io[m].get("std_outputs", {})), 2) + 0.4
    H = rows + 14
    fig, ax = plt.subplots(figsize=(17, H * 0.33))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, H)
    ax.axis("off")
    xm, wm = 60, 16
    y = H - 3
    box(ax, xm, y, wm, 2.2, "SC1 PNOZ m ES ETH (Modbus TCP -> Jetson, non-safe)", "#d5f5e3", fs=6, bold=True)
    yi = y - 0.6
    for m in mods:
        ins = [(k, v) for k, v in io[m]["inputs"].items() if not v["sig"].startswith("spare")]
        rly = scm[m].get("rly", 0) > 0
        outs = [(k, v, "#b9770e" if rly else C["b48"]) for k, v in io[m].get("outputs", {}).items() if not v["sig"].startswith("spare")]
        outs += [(k, v, "#7f8c8d") for k, v in io[m].get("std_outputs", {}).items() if not v["sig"].startswith("spare")]
        n = max(len(ins), len(outs), 2)
        top, bot = yi, yi - n
        c48 = io[m].get("variant") == "C48"
        box(ax, xm, bot + 0.15, wm, n - 0.3, f"{m}\n" + scm[m]['mpn'].replace(" (", "\n(") + ("\n(variant C48 only)" if c48 else ""),
            "#f5eef8" if c48 else "#e8f8f5", ls="--" if c48 else "-", fs=7, bold=True)
        for j, (k, v) in enumerate(ins):
            yy = top - (j + 0.5) * n / len(ins)
            col = C["sig"] if v.get("sf") else "#95a5a6"
            ax.text(xm - 35.5, yy, f"{v['src']}", fontsize=5.5, ha="right", va="center", color="#555")
            ax.text(xm - 35, yy, v["sig"][:70] + (f"  [{v['test']}]" if v.get("test") else ""), fontsize=5.8, ha="left", va="center")
            line(ax, [(xm - 0.8, yy), (xm, yy)], col, lw=1.0)
            ax.text(xm + 0.3, yy, k, fontsize=5.5, va="center", color=col)
            ax.text(xm - 35, yy - 0.42, ",".join(v.get("sf", [])), fontsize=4.6, ha="left", va="center", color="#7d3c98")
        for j, (k, v, col) in enumerate(outs):
            yy = top - (j + 0.5) * n / len(outs)
            ax.text(xm + wm - 0.3, yy, k, fontsize=5.5, va="center", ha="right", color=col)
            line(ax, [(xm + wm, yy), (xm + wm + 1.2, yy)], col, lw=1.0)
            ax.text(xm + wm + 1.5, yy, v["sig"][:62], fontsize=5.8, ha="left", va="center")
            ax.text(xm + wm + 1.5, yy - 0.42, f"-> {v['dst']}   " + ",".join(v.get("sf", [])), fontsize=4.6, ha="left", va="center", color="#7d3c98")
        yi = bot - 0.4
    fs_ = NET["field_sets"]
    t = ["Field sets (nanoScan3 static control inputs CI1-CI3, 1-of-3 evaluation, same code on both scanners):"]
    for k in ("FS1_FAST", "FS2_SLOW", "FS3_DOCK"):
        v = fs_[k]
        t.append(f"  {k}: {v['code']} | {v['speed']} | {v['prot_field'][:95]} | when: {v['condition'][:60]}")
    t.append("  rule: " + fs_["switching_rule"][:230])
    sp = NET["swd_permanent"]
    t.append(f"SWD permanent (no controller channel): SMS {sp['SMS']}; SLSa {sp['SLSa'][:80]}")
    t.append("Stops: E-stop -> traction SS1-t (t=0 SLS[1] requested + SWD quick-stop ramp 1.5 m/s2, STO+SBC at 1.2 s via SR1 relays), OA arms: K1/K2 open at 0.5 s "
             "(arms fall onto rests: no brakes), coffee KI4/K4 off. Protective stop (OSSD1) = as E-stop, auto-resume in AUTO once clear; OSSD2 -> arms only. "
             "Manual reset SB1 after E-stop. Orange = positive-guided relay contacts (2.2 k bleed each, no test pulses); grey = auxiliary (non-safe) outputs; T0/T1 = test pulses.")
    for i, s in enumerate(t):
        ax.text(1, 7.4 - i * 0.8, s, fontsize=5.8, ha="left", va="center")
    ax.text(1, H - 1.0, "INPUTS (test pulses T0/T1 on NC contacts)", fontsize=8, weight="bold", color=C["sig"])
    ax.text(xm + wm + 1.5, H - 1.0, "OUTPUTS (red = safe SC 24 V; orange = safe relay; grey = auxiliary)", fontsize=8, weight="bold", color=C["b48"])
    ax.set_title("Giorgio AMR - safety controller wiring overview (Pilz PNOZmulti 2, rev B2) - from netlist_amr.yaml safety_io",
                 fontsize=11, weight="bold")
    save(fig, "safety_diagram")


if __name__ == "__main__":
    single_line()
    safety()
    print("written:", [f for f in sorted(os.listdir(HERE)) if f.endswith((".svg", ".png"))])
