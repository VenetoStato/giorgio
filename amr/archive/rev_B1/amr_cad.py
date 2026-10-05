"""Giorgio AMR (own base), rev B - parametric CadQuery model: chassis, 2 safety wheel drives, 4 sprung castors,
2 batteries, centre electronics bay, DIN bays, safety scanners, dock contacts, covers, cable harness routes and the
charging dock. Rev B has no waist joint: the 10 mm top deck is the superstructure flange (top at z = 353 mm).

    cad/.env/bin/python amr/amr_cad.py            # build, export STEP/STL/DXF, parts.json, mass properties

Frame as cad/: mm, origin on the floor at the base centre, x forward, y left, z up, waist yaw = 0.
Purchased parts are datasheet envelopes (tag ESTIMATE where the manufacturer CAD is not public): replace them with
the vendor STEP before release (list in DESIGN.md).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cad"))
import geom as G  # noqa: E402
from geom import box, cyl  # noqa: E402
from amr_params import *  # noqa: E402,F401,F403

OUT = HERE / "out"
RHO = {"S355MC": 7850, "EN AW-6082-T6": 2700, "EN AW-5754-H22": 2670, "POM-C": 1410, "PA12 (MJF)": 1010,
       "EPDM": 1200, "steel 42CrMo4": 7850, "purchased": 0, "harness": 0}
COL = {"S355MC": (0.30, 0.31, 0.33), "EN AW-6082-T6": (0.74, 0.75, 0.77), "EN AW-5754-H22": (0.80, 0.81, 0.83),
       "POM-C": (0.95, 0.95, 0.93), "PA12 (MJF)": (0.93, 0.93, 0.91), "EPDM": (0.07, 0.07, 0.08), "steel 42CrMo4": (0.5, 0.5, 0.52)}
PARTS: dict = {}


def add(name, shape, material, process, group="base", category="custom", color=None, explode=(0, 0, 0), mass=None,
        src="", flat=None, qty=1, notes=""):
    """flat = (z_cut, thickness) for laser/waterjet parts -> a DXF profile is exported"""
    m = mass if mass is not None else shape.Volume() * 1e-9 * RHO[material]
    PARTS[name] = dict(shape=shape, material=material, process=process, group=group, category=category,
                       color=color or COL.get(material, (0.2, 0.2, 0.22)), explode=explode, mass=m, src=src, flat=flat,
                       qty=qty, notes=notes)
    return shape


def poly(pts, t, z0):
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(t).val()


def outline(inset=0.0, chamf=CHAMF):
    x0, x1, y0, y1 = X0 + inset, X1 - inset, Y0 + inset, Y1 - inset
    c = chamf - inset * (math.sqrt(2) - 1)
    return [(x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c), (x0 + c, y0), (x1 - c, y0)]


def place(shape, R=np.eye(3), t=(0, 0, 0)):
    return G.transform_shape(shape, R, t)


def tube(points, r):
    """harness as a swept circle along a polyline (rounded corners)"""
    pts = [cq.Vector(*p) for p in points]
    path = cq.Wire.makePolygon(pts, close=False)
    try:
        path = cq.Wire.assembleEdges(path.Edges()).fillet(min(25.0, r * 4)) if len(pts) > 2 else path
    except Exception:
        pass
    d = (pts[1] - pts[0]).normalized()
    circ = cq.Wire.makeCircle(r, pts[0], d)
    return cq.Solid.sweep(circ, [], path, transitionMode="round")


# ====================================================================== structure
def chassis():
    pan = poly(outline(6.0), PAN_T, PAN_Z0)
    # wheel wells (wheel + 12 mm clearance) and caster holes
    for sy in (-1, 1):
        pan = pan.cut(box(-WHEEL_D / 2 - 14, WHEEL_D / 2 + 14, sy * (WHEEL_Y - WHEEL_W / 2 - 10), sy * (WHEEL_Y + WHEEL_W / 2 + 12),
                          PAN_Z0 - 1, PAN_Z1 + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pan = pan.cut(cyl(CASTER_D / 2 + 22, PAN_T + 2, (sx * CASTER_XY[0], sy * CASTER_XY[1], PAN_Z0 - 1)))
    for sx in (-1, 1):                                    # cable pass-throughs / drain
        pan = pan.cut(G.rounded_rect(0, sx * 60, 80, 30, PAN_T + 2, PAN_Z0 - 1, 10))
    add("A01_floor_pan", pan, "S355MC", "laser cut 5 mm S355MC, deburr, zinc-flake or powder coat; PEM studs M6",
        explode=(0, 0, -160), flat=(PAN_Z0, PAN_T), notes="low and heavy on purpose: ballast for tipping")

    deck = poly(outline(4.0), DECK_T, DECK_Z0)
    cx_, cy_, lx_, ly_ = CABLE_PASS
    deck = deck.cut(G.rounded_rect(cx_, cy_, lx_, ly_, DECK_T + 2, DECK_Z0 - 1, 12))      # grommet: base -> superstructure cables
    # rev B: no open windows in the deck (it is the visible top surface; ISO 13857 finger access)
    add("A02_top_deck", deck, "EN AW-6082-T6", "waterjet 15 mm 6082-T6 + CNC: column-foot M6 pattern (thread engagement >= 9 mm) and coffee-upright holes (as old P01), spine slots; powder coat RAL 9016 textured",
        explode=(0, 0, 260), flat=(DECK_Z0, DECK_T), notes="IS the superstructure flange (old P01 + Ranger deck in one part); bolted to both spines and 4 end posts")

    for sy in (-1, 1):
        y0 = sy * SPINE_Y - (SPINE_T if sy > 0 else 0)
        sp = box(-SPINE_X, SPINE_X, y0, y0 + SPINE_T, PAN_Z1, DECK_Z0)
        sp = sp.cut(box(-60, 60, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 + 20, PAN_Z1 + 110))        # drive connector / service window
        for x in (-200, -140, 140, 200):
            sp = sp.cut(G.rounded_rect(x, y0 + SPINE_T / 2, 34, SPINE_T + 2, 120, PAN_Z1 + 40, 0).rotate((x, y0 + SPINE_T / 2, 0), (x, y0 + SPINE_T / 2, 1), 0)
                        if False else box(x - 17, x + 17, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 + 160, PAN_Z1 + 240))   # harness windows
        add(f"A03_spine_{'L' if sy > 0 else 'R'}", sp, "EN AW-6082-T6",
            "waterjet 6 mm 6082-T6, tapped M5 rows for 2 DIN rails, M6 to pan/deck", explode=(0, sy * 140, 0),
            flat=None, notes=f"structural wall + DIN panel ({'power' if sy > 0 else 'safety/control'} bay)")
    # corner posts (deck support at the ends), bent 3 mm
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * POSTS[0][0], sy * POSTS[0][1]
            add(f"A04_post_{'F' if sx > 0 else 'R'}{'L' if sy > 0 else 'R'}", box(x - 15, x + 15, y - 15, y + 15, PAN_Z1, DECK_Z0)
                .cut(box(x - 12, x + 12, y - 12, y + 12, PAN_Z1 - 1, DECK_Z0 + 1)), "EN AW-6082-T6",
                "30x30x3 square tube EN 755-2, cut + drill", explode=(sx * 60, 0, 0))
    # caster towers: roof plate (castor under, scanner on top) on 4 legs; the castor swivels between the legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * CASTER_XY[0], sy * CASTER_XY[1]
            tw = box(cx - 60, cx + 60, cy - 60, cy + 60, TOWER_ROOF[0], TOWER_ROOF[1])
            for lx in (-1, 1):
                for ly in (-1, 1):
                    tw = tw.fuse(box(cx + lx * 60 - (15 if lx > 0 else 0), cx + lx * 60 + (0 if lx > 0 else 15),
                                     cy + ly * 60 - (15 if ly > 0 else 0), cy + ly * 60 + (0 if ly > 0 else 15), PAN_Z1, TOWER_ROOF[0]))
            tw = tw.intersect(poly(outline(COVER_T + 2), 400, 0))
            add(f"A05_caster_tower_{'F' if sx > 0 else 'R'}{'L' if sy > 0 else 'R'}", tw, "S355MC",
                "laser cut 6 mm roof + 4 legs 15x15 (welded), M8 castor pattern; scanner seat machined", explode=(0, 0, -90))


def drives():
    for sy in (-1, 1):
        y = sy * WHEEL_Y
        r = WHEEL_D / 2
        wheel = cyl(r, WHEEL_W, (0, y - WHEEL_W / 2, r), (0, 1, 0))
        yi = y - sy * WHEEL_W / 2
        bx = box(-SWD_BOX["dx"] / 2, SWD_BOX["dx"] / 2, yi, yi - sy * SWD_BOX["dy"], 45, 45 + SWD_BOX["dz"])
        add(f"D01_ezwheel_SWD125_{'L' if sy > 0 else 'R'}", wheel.fuse(bx), "purchased",
            "purchased ez-Wheel SWD 125 EW2A-125HN04B (4:1, brake), safety encoder, CANopen Safety", category="purchased",
            color=(0.95, 0.55, 0.12), explode=(0, sy * 220, -60), mass=SWD_MASS,
            src="ez-Wheel SWD 125 (SOURCED load/torque/speed; envelope ESTIMATE - CAD behind login)")
        add(f"D02_swd_mount_spacer_{'L' if sy > 0 else 'R'}", box(-70, 70, sy * (SPINE_Y), sy * (SPINE_Y + 4), 60, 160) if sy > 0
            else box(-70, 70, -SPINE_Y - 4, -SPINE_Y, 60, 160), "EN AW-6082-T6", "waterjet 4 mm spacer, 6x M8 through the spine",
            explode=(0, sy * 170, -40))


def casters():
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * CASTER_XY[0], sy * CASTER_XY[1]
            r = CASTER_D / 2
            s = cyl(r, 32, (cx - 10, cy - 16, r), (0, 1, 0))
            s = s.fuse(box(cx - 30, cx + 20, cy - 22, cy + 22, r, CASTER_H - 6))
            s = s.fuse(box(cx - CASTER_PLATE[0] / 2, cx + CASTER_PLATE[0] / 2, cy - CASTER_PLATE[1] / 2, cy + CASTER_PLATE[1] / 2,
                           CASTER_H - 6, CASTER_H))
            add(f"C01_caster_{'F' if sx > 0 else 'R'}{'L' if sy > 0 else 'R'}", s, "purchased",
                "purchased swivel castor D100 PU, top plate, ball-bearing swivel (Blickle LKPA-VPA 100 class)",
                category="purchased", color=(0.12, 0.12, 0.13), explode=(0, 0, -140), mass=CASTER_MASS,
                src="Blickle catalogue class (SECONDARY)")


def batteries():
    for k, bx in enumerate(BATT_XS):
        s = box(bx - BATT["Lx"] / 2, bx + BATT["Lx"] / 2, -BATT["Wy"] / 2, BATT["Wy"] / 2, PAN_Z1 + 3, PAN_Z1 + 3 + BATT["H"])
        add(f"B01_battery_{'F' if bx > 0 else 'R'}_DLP-GC2-48V", s, "purchased",
            "purchased Discover AES PRO DLP-GC2-48V, LFP 51.2 V 30 Ah, IEC 62619/CE/UN38.3", category="purchased",
            color=(0.10, 0.28, 0.55), explode=(np.sign(bx) * 330, 0, 0), mass=BATT["mass"],
            src="discoverbattery.com (SOURCED 14 kg, 260x180x254 mm)", notes="mounting orientation lying: confirm with Discover")
        # hold-down frame: 2 straps + EPDM pad
        add(f"B02_battery_pad_{'F' if bx > 0 else 'R'}", box(bx - BATT["Lx"] / 2 + 8, bx + BATT["Lx"] / 2 - 8,
            -BATT["Wy"] / 2 + 8, BATT["Wy"] / 2 - 8, PAN_Z1, PAN_Z1 + 3), "EPDM", "die-cut 3 mm EPDM", explode=(np.sign(bx) * 300, 0, -30))
        for j, dx in enumerate((-55, 85) if bx > 0 else (-85, 55)):
            st = box(bx + dx - 15, bx + dx + 15, -SPINE_Y + SPINE_T, SPINE_Y - SPINE_T, PAN_Z1 + 3 + BATT["H"], PAN_Z1 + 6 + BATT["H"])
            add(f"B03_battery_strap_{'F' if bx > 0 else 'R'}{j}", st, "EN AW-5754-H22",
                "laser cut 3 mm + 2 bends, M6 into spine tapped holes", explode=(np.sign(bx) * 330, 0, 90))


def centre_bay():
    """electronics that sat on the old adapter plate: Jetson + arm-bus DC-DCs (OpenArm variant), on a 3 mm tray on the pan"""
    x0, x1, yb = CENTRE_BAY["x0"], CENTRE_BAY["x1"], CENTRE_BAY["y"]
    add("P10_centre_tray", box(x0, x1, -yb + 2, yb - 2, PAN_Z1, PAN_Z1 + 3).cut(G.rounded_rect(0, 0, 90, 150, 5, PAN_Z1 - 1, 15)),
        "EN AW-5754-H22", "laser cut 3 mm + PEM M4, on 4 rubber mounts", explode=(0, 0, 420))
    z = PAN_Z1 + 3
    for k, (y0, y1) in enumerate(((-127.0, -2.0), (2.0, 127.0))):
        add(f"E50_dcdc_arm_{'R' if k == 0 else 'L'}_DDR480C24", box(-64.6, 64.6, y0, y1, z, z + 85.5), "purchased",
            "purchased Mean Well DDR-480C-24 (arm 24 V bus; OpenArm variant only)", category="purchased",
            color=(0.78, 0.78, 0.8), explode=(0, 0, 470), mass=1.375, src="meanwell.com (SOURCED)")
    zs = z + 85.5 + 16                     # >= 15 mm convection gap above the lying DDR-480 (electrical s.13)
    add("P11_centre_shelf", box(x0, x1, -yb + 2, yb - 2, zs, zs + 3), "EN AW-5754-H22", "laser cut 3 mm shelf on 4 standoffs",
        explode=(0, 0, 520))
    add("E51_jetson_orin_nx_carrier", box(-60, 50, -55, 55, zs + 3, zs + 63), "purchased",
        "purchased NVIDIA Jetson Orin NX 16 GB on fanned carrier (12 V)", category="purchased", color=(0.12, 0.12, 0.13),
        explode=(0, 0, 560), mass=0.7, src="ESTIMATE")
    add("E52_arm_ORing_DRDN40-24_x2", box(55, 77, -110, 110, zs + 3, zs + 93), "purchased",
        "purchased 2x Mean Well DRDN40-24 + 2x maxon DSR 50/5 (arm bus ORing + 27 V clamp, OpenArm variant)", category="purchased",
        color=(0.25, 0.25, 0.28), explode=(0, 0, 560), mass=0.6)
    ZC = 274.0                                                   # centre-bay rails on the spine inner faces
    for sy in (1, -1):
        yi = sy * (SPINE_Y - SPINE_T)
        add(f"E0C_{'L' if sy > 0 else 'R'}_din_rail", box(-76, 53, *sorted((yi, yi - sy * 7.5)), ZC - 17.5, ZC + 17.5), "purchased",
            "DIN rail TS35x7.5, M5 into the spine inner face", category="purchased", color=(0.7, 0.7, 0.72), explode=(0, 0, 600), mass=0.08)
        mods = ([("E57_FAL_FAR_fuses", 35, 82, 70, -76), ("E58_U6_DDR60L5", 40, 125.2, 100, -39), ("E59_JR1_relays", 12.4, 90, 80, 3),
                 ("E5A_XC_deck_terminals", 30, 60, 50, 17.4)] if sy > 0 else
                [("E54_U7_DDR480C24_coffee", 85.5, 125.2, 129.2, -76), ("E55_K4_Finder22", 17.5, 90, 70, 11.5), ("E56_FCF_fuse", 17.5, 82, 70, 31)])
        face = yi - sy * 7.5
        for name, wdt, hgt, dep, x0_ in mods:
            add(name, box(x0_, x0_ + wdt, *sorted((face, face - sy * dep)), ZC - hgt / 2, ZC + hgt / 2), "purchased",
                "purchased DIN module (electrical/din_layout.md, centre bay)", category="purchased",
                color=(0.78, 0.78, 0.8) if "DDR" in name else (0.25, 0.25, 0.28), explode=(0, 0, 640),
                mass={"E54": 1.375, "E58": 0.3}.get(name[:3], 0.15))
    add("E53_deck_grommet", G.rounded_rect(CABLE_PASS[0], CABLE_PASS[1], CABLE_PASS[2] + 10, CABLE_PASS[3] + 10, 6, DECK_Z1, 15)
        .cut(G.rounded_rect(CABLE_PASS[0], CABLE_PASS[1], CABLE_PASS[2] - 10, CABLE_PASS[3] - 10, 8, DECK_Z1 - 1, 8)), "purchased",
        "purchased split cable-entry frame, >= 10 entries (icotek KEL-DPZ class, IP54)", category="purchased", color=(0.08, 0.08, 0.09),
        explode=(0, 0, 300), mass=0.1)


def sensors_and_io():
    for k, (sx, sy, head) in enumerate(SCAN_CORNERS):
        cx, cy = sx * CASTER_XY[0] + 10 * sx, sy * CASTER_XY[1] + 10 * sy      # pushed 14 mm out along the diagonal
        z0 = TOWER_ROOF[1]
        s = place(box(-NS3["D"] / 2, NS3["D"] / 2, -NS3["W"] / 2, NS3["W"] / 2, 0, NS3["H"]), G.rotz(head), (cx, cy, z0))
        add(f"S01_nanoScan3_ProIO_{k}", s, "purchased", "purchased SICK nanoScan3 Pro I/O NANS3-CAAZ30AN1 (PL d, 128 field sets; no encoder inputs per datasheet)",
            category="purchased", color=(0.95, 0.8, 0.1), explode=(sx * 160, sy * 160, 0), mass=NS3["mass"], src="sick.com (SOURCED)")
    # dock collector (rear centre)
    s = box(X0 + 2, X0 + 2 + ROBOPAD["D"], -ROBOPAD["W"] / 2, ROBOPAD["W"] / 2, PAD_Z - ROBOPAD["H"] / 2, PAD_Z + ROBOPAD["H"] / 2)
    add("E01_robopad_collector_RPCOL90", s, "purchased", "purchased Roboteq RoboPad collector RPCOL90-100 (75 A, Hall docked sensor)",
        category="purchased", color=(0.85, 0.45, 0.1), explode=(-200, 0, 0), mass=ROBOPAD["mass"], src="Roboteq datasheet (SOURCED)")
    # E-stops (both sides), service disconnect key (left), status LED band
    for sy in (-1, 1):
        add(f"E02_estop_{'L' if sy > 0 else 'R'}", cyl(20, 38, (0, sy * (Y1 + 36), 268), (0, -sy, 0)), "purchased",
            "purchased Eaton M22-PVT45P + M22-K02 (2 NC) + yellow enclosure plate", category="purchased",
            color=(0.85, 0.1, 0.1), explode=(0, sy * 120, 0), mass=0.08)
    add("E03_service_disconnect_ED250B", box(-340, -270, -210, -140, 145, 235), "purchased",
        "purchased Albright ED250B (with blowouts, 58 V) key-lockable service disconnect, key extension through the rear cover", category="purchased",
        color=(0.85, 0.1, 0.1), explode=(0, 160, 0), mass=0.6, src="albrightinternational.com (SOURCED)")


def din_bays():
    """DIN rails on the spines (layout = amr/electrical/din_layout.md): left (+y) = power, right (-y) = safety/control.
    Upper rails at z 248 (x -258..+258), lower rails beside the drive (x +100..+215 and -215..-100) at z 118.
    Module tuple: (name, width along x, height, depth from the rail face, x_start)."""
    U = [  # left upper: power
        (1, "E10_F0_fuse_NH00_100A", 40, 125, 90, -217), (1, "E11_K0_contactor_SW80B_on_plate", 70, 110, 95, -175),
        (1, "E12_K0P_precharge_relay", 17.5, 90, 70, -103), (1, "E18_branch_fuses_10x38_x6", 110, 82, 70, -83.5),
        (1, "E13_U1_dcdc_DDR480C24", 85.5, 125.2, 129.2, 46), (1, "E14_U2_dcdc_DDR480C24", 85.5, 125.2, 129.2, 133.5),
        (1, "E17_K0T_timer_Finder80", 17.5, 90, 70, 221),
        # right upper: safety / control (rev B: Pilz PNOZmulti 2)
        (-1, "E20_SC1_PNOZ_m_ES_ETH", 22.5, 101.4, 120, -257), (-1, "E21_SC0_PNOZ_m_B0", 45, 101.4, 120, -234.5),
        (-1, "E22_SX1_PNOZ_m_EF_8DI4DO", 22.5, 101.4, 120, -189.5), (-1, "E2F_WF1-3_AUX48_fuses", 52.5, 82, 70, -142),
        (-1, "E25_NET1_switch_FL1008N", 40, 110, 90, -89.5),
        (-1, "E15_U4_dcdc_DDR240C24_S24", 40, 125.2, 100, -47.5), (-1, "E27_XS24_terminals", 70, 60, 50, -5.5),
        (-1, "E2C_K1_contactor_3RT2026", 45, 85, 97, 66.5), (-1, "E2D_K2_contactor_3RT2026", 45, 85, 97, 113.5),
        (-1, "E2G_U5_DDR120C12_FJ", 51.5, 125.2, 102, 160.5)]
    L = [  # lower rails
        (1, "E30_U3_ORing_DRDN40-24", 55, 90, 100, 100), (1, "E31_F8LR_SWD_fuses", 35, 82, 70, 157), (1, "E32_T24_terminals", 24, 60, 50, 194),
        (1, "E16_R1_maxon_DSR50-5_x2", 70, 94, 41, -215), (1, "E19_0V_block", 27, 60, 50, -130),
        (-1, "E33_F7_charge_fuse", 17.5, 82, 70, -215), (-1, "E34_U8_ideal_diode_DRDN40-48", 55, 90, 100, -195), (-1, "E35_RSIG_X0R", 22, 60, 50, -138),
        (-1, "E36_CAN1_PCAN-Ethernet_gw", 45, 100, 90, 100), (-1, "E37_KS_signature_relay", 6.2, 90, 70, -114)]
    for rows, ZR, xa, xb in ((U, 248.0, None, None), (L, 118.0, None, None)):
        for sy, name, wdt, hgt, dep, x0 in rows:
            face = sy * (SPINE_Y + 7.5)
            y0, y1 = sorted((face, face + sy * dep))
            s = box(x0, x0 + wdt, y0, y1, ZR - hgt / 2, ZR + hgt / 2)
            col = (0.95, 0.8, 0.1) if ("flexi" in name or "FX3" in name or "OSSD" in name) else (0.78, 0.78, 0.8) if "dcdc" in name \
                else (0.85, 0.12, 0.1) if "contactor" in name else (0.25, 0.25, 0.28)
            add(name, s, "purchased", "purchased DIN module (amr/electrical/din_layout.md, netlist_amr.yaml)", category="purchased",
                color=col, explode=(0, sy * 260, 0),
                mass={"E13": 1.375, "E14": 1.375, "E15": 0.6, "E11": 0.9, "E10": 0.4, "E16": 0.5}.get(name[:3], 0.25))
    add("E38_G01_LYNK_II_gateway", box(152, 217, -SPINE_Y - 30, -SPINE_Y, 83, 153), "purchased",
        "purchased Discover LYNK II gateway, panel mount on the spine (size ASSUMED)", category="purchased", color=(0.25, 0.25, 0.28),
        explode=(0, -260, 0), mass=0.2)
    for sy in (1, -1):
        y0, y1 = sorted((sy * SPINE_Y, sy * (SPINE_Y + 7.5)))
        add(f"E0{'L' if sy > 0 else 'R'}_din_rail_upper", box(-258, 258, y0, y1, 248 - 17.5, 248 + 17.5), "purchased",
            "DIN rail TS35x7.5 EN 60715, M5 to the spine", category="purchased", color=(0.7, 0.7, 0.72), explode=(0, sy * 250, 0), mass=0.25)
        for xa, xb in (((98, 218) if sy > 0 else (98, 148)), (-218, -98)):     # right front segment shortened: G01 gateway beside it
            add(f"E0{'L' if sy > 0 else 'R'}_din_rail_lower_{'F' if xa > 0 else 'R'}", box(xa, xb, y0, y1, 118 - 17.5, 118 + 17.5), "purchased",
                "DIN rail TS35x7.5 EN 60715", category="purchased", color=(0.7, 0.7, 0.72), explode=(0, sy * 250, 0), mass=0.06)
    # bay fans: 2 x 60 mm IP54 + filter per bay (intake low front, exhaust high rear) on the side covers
    for sy in (1, -1):
        add(f"E40_fan_{'L' if sy > 0 else 'R'}in", box(150, 210, sy * (Y1 - 27), sy * (Y1 - 2), 65, 125) if sy > 0
            else box(150, 210, -(Y1 - 2), -(Y1 - 27), 65, 125), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, intake low (side cover)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(0, sy * 200, 0), mass=0.12)
        add(f"E40_fan_{'L' if sy > 0 else 'R'}out", box(X0 + 2, X0 + 27, sy * 105 - 30, sy * 105 + 30, 243, 303), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, exhaust high (rear cover)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(-200, 0, 0), mass=0.12)
    add("E40_fan_Cin", box(X1 - 27, X1 - 2, -30, 30, 255, 315), "purchased",
        "purchased 60x60x25 mm 24 V IP54 fan + filter grille, centre-bay intake (front cover)", category="purchased",
        color=(0.1, 0.1, 0.11), explode=(200, 0, 0), mass=0.12)
    # rear panel: reset SB1, key selector SK1, M12 enabling-pendant socket SE1
    for k, (yy, nm) in enumerate(((-50, "SB1_reset_blue"), (0, "SK1_key_selector"), (50, "SE1_M12_pendant_socket"))):
        add(f"E41_{nm}", cyl(15, 40, (X0 + 1, yy, 280), (1, 0, 0)), "purchased", "purchased Eaton M22 / M12 panel device", category="purchased",
            color=(0.15, 0.3, 0.8) if k == 0 else (0.2, 0.2, 0.22), explode=(-180, 0, 0), mass=0.05)


def covers():
    zc0, zc1 = PAN_Z0 + 30, DECK_Z0 - 1
    outer = poly(outline(0.0), zc1 - zc0, zc0)
    inner = poly(outline(COVER_T), zc1 - zc0 + 2, zc0 - 1)
    shell = outer.cut(inner)
    # wheel arches, scanner windows (270 deg field at the 2 corners), dock window, e-stop holes
    for sy in (-1, 1):
        shell = shell.cut(box(-WHEEL_D / 2 - 12, WHEEL_D / 2 + 12, sy * (Y1 - 10), sy * (Y1 + 10), zc0 - 1, WHEEL_D + 18))
        shell = shell.cut(cyl(21, 20, (0, sy * (Y1 - 10), 268), (0, sy, 0)))
    # continuous scan slot all round (40 mm, centred on the scan plane): each corner scanner sees its 270 deg
    shell = shell.cut(box(-500, 500, -400, 400, SCAN_Z - 20, SCAN_Z + 20))
    for (sx, sy, head) in SCAN_CORNERS:                  # local notch: scanner housing (134..214) passes the upper band
        cx, cy = sx * (CASTER_XY[0] + 10), sy * (CASTER_XY[1] + 10)
        shell = shell.cut(cyl(80, 100, (cx, cy, TOWER_ROOF[0] - 6)))
    shell = shell.cut(box(X0 - 5, X0 + 10, -ROBOPAD["W"] / 2 - 6, ROBOPAD["W"] / 2 + 6, PAD_Z - ROBOPAD["H"] / 2 - 6, PAD_Z + ROBOPAD["H"] / 2 + 6))
    for yy in (-50, 0, 50):
        shell = shell.cut(cyl(16, 20, (X0 - 5, yy, 280), (1, 0, 0)))
    for sy in (1, -1):
        shell = shell.cut(box(155, 205, sy * (Y1 + 5), sy * (Y1 - 10), 70, 120)).cut(box(X0 - 5, X0 + 10, sy * 105 - 25, sy * 105 + 25, 248, 298))
    shell = shell.cut(cyl(12, 20, (X0 - 5, -175, 190), (1, 0, 0)))          # ED250B key
    shell = shell.cut(box(X1 - 10, X1 + 5, -25, 25, 260, 310))                 # centre-bay intake fan
    # split into 4 removable covers (front, rear, left, right) at x = +-260
    parts = {"F": box(260, 500, -400, 400, 0, 400), "R": box(-500, -260, -400, 400, 0, 400),
             "L": box(-260, 260, 0, 400, 0, 400), "Rt": box(-260, 260, -400, 0, 0, 400)}
    for k, b in parts.items():
        add(f"K0{['F', 'R', 'L', 'Rt'].index(k) + 1}_cover_{k}", shell.intersect(b), "EN AW-5754-H22",
            "laser cut + bent 2 mm 5754, powder coat RAL 9016 + tricolour band; 1/4-turn fasteners (tool-free = NO: Torx, EN ISO 14120)",
            explode={"F": (220, 0, 0), "R": (-220, 0, 0), "L": (0, 220, 0), "Rt": (0, -220, 0)}[k],
            color=(0.92, 0.92, 0.9))
    # bumper strip (rubber, at the bottom edge)
    bump = poly(outline(-4.0), 22, PAN_Z0 + 8).cut(poly(outline(0.0), 24, PAN_Z0 + 7))
    add("K05_rubber_edge", bump, "EPDM", "extruded EPDM edge profile 22 mm, bonded", explode=(0, 0, -40))


def harness():
    """main cable routes (centre lines); IDs match amr/electrical/cable_schedule.csv"""
    H = []
    zF = PAN_Z1 + 3 + BATT["H"] + 18
    H.append(("H01_batt_F_to_fuse", [(210, 60, zF), (210, 150, zF), (100, 175, 255)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H02_batt_R_to_fuse", [(-210, 60, zF), (-210, 150, zF), (-100, 175, 255)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H03_bus48_to_centre_and_deck", [(0, 175, 300), (0, 120, 315), (62, 30, 320), (62, 20, 355)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H04_traction_24V_L", [(60, 175, 210), (40, 175, 190), (0, 170, 160)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H05_traction_24V_R", [(60, 175, 230), (60, 60, 230), (60, -150, 230), (0, -170, 160)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H06_dock_to_charge_path", [(-345, 0, PAD_Z), (-360, 80, PAD_Z), (-300, 160, 160), (-230, 175, 230)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H07_safety_bus_scanner_F", [(-150, -175, 250), (250, -175, 250), (300, -195, 170)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H08_safety_bus_scanner_R", [(-150, -175, 250), (-250, -100, 250), (-300, 150, 250), (-310, 195, 170)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H09_safety_estops", [(-100, -175, 250), (0, -230, 268), (0, -260, 268)], 3.0, (0.95, 0.8, 0.1)))
    H.append(("H10_ethernet_safety_to_deck", [(-50, -175, 300), (-20, -120, 318), (62, -30, 322), (62, -20, 355)], 3.0, (0.2, 0.5, 0.9)))
    for n, pts, r, c in H:
        add(n, tube(pts, r), "harness", "harness (see cable_schedule.csv)", category="harness", color=c, mass=0.0,
            explode=(0, 0, 0))


def dock():
    """wall dock (floor-standing, bolted to floor + wall): RoboPad base + charger + guide wedges + AprilTag/reflector"""
    xd = X0 - 8.0                                   # dock contact face when docked
    base = box(xd - 300, xd - 20, -260, 260, 0, 6)
    base = base.fuse(box(xd - 300, xd - 296, -260, 260, 6, 520))                    # back plate to the wall (4 mm)
    for sy in (-1, 1):                                                               # guide rails: 4 mm sheet, lead-in +-60 mm
        a, b = (xd - 280, sy * 150), (xd + 120, sy * 230)
        L_ = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        base = base.fuse(place(box(0, L_, -2, 2, 0, 70), G.rotz(ang), (a[0], a[1], 6)))
    add("X01_dock_frame", base, "S355MC", "laser cut + bent 4 mm S355MC, welded, powder coat; floor anchors M10 x4, wall M8 x2",
        group="dock", explode=(-200, 0, 0), color=(0.25, 0.26, 0.28))
    add("X02_robopad_base_RPBAS90", box(xd - 34, xd, -ROBOPAD["W"] / 2, ROBOPAD["W"] / 2, PAD_Z - ROBOPAD["H"] / 2, PAD_Z + ROBOPAD["H"] / 2),
        "purchased", "purchased Roboteq RoboPad base (contacts, Hall sensor)", group="dock", category="purchased",
        color=(0.85, 0.45, 0.1), explode=(-260, 0, 0), mass=0.4)
    add("X03_pad_mount", box(xd - 296, xd - 34, -70, 70, 88, 92).fuse(box(xd - 40, xd - 34, -70, 70, 6, 150)), "S355MC", "bent 3 mm bracket", group="dock", explode=(-230, 0, 0))
    add("X04_charger_NPB1700_48", box(xd - 255, xd - 105, -150, -50, 180, 360), "purchased",
        "purchased Mean Well NPB-1700-48 (25 A, CANbus, IEC 60335-2-29) in IP20 housing", group="dock", category="purchased",
        color=(0.7, 0.7, 0.72), explode=(-300, 0, 120), mass=3.3)
    add("X05_dock_controller_relay", box(xd - 255, xd - 175, 50, 150, 220, 330), "purchased",
        "purchased DIN box: CAN controller + DC contactor with blowouts (output OFF unless Hall + handshake); charger reprogrammed to <= 56.8 V", group="dock",
        category="purchased", color=(0.25, 0.25, 0.28), explode=(-300, 0, 120), mass=0.8)
    add("X06_apriltag_reflector_plate", box(xd - 262, xd - 258, -120, 120, 380, 500), "purchased",
        "AprilTag 36h11 + retro-reflective strip (lidar profile)", group="dock", category="purchased",
        color=(0.95, 0.95, 0.95), explode=(-320, 0, 0), mass=0.2)
    add("X07_dock_cover", box(xd - 260, xd - 30, -255, 255, 175, 370).cut(box(xd - 257, xd - 33, -252, 252, 172, 367)),
        "EN AW-5754-H22", "bent 2 mm, powder coat, vent slots", group="dock", explode=(-260, 0, 200), color=(0.92, 0.92, 0.9))


def build():
    chassis(); drives(); casters(); batteries(); centre_bay(); sensors_and_io(); din_bays(); covers(); harness(); dock()
    return PARTS


def export(parts):
    from cadquery import exporters
    for d in ("step", "stl", "dxf", "exploded"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    meta = []
    for n, p in parts.items():
        if p["category"] != "harness":
            exporters.export(p["shape"], str(OUT / "step" / f"{n}.step"))
        tm = G.shape_to_trimesh(p["shape"], tol=0.4)
        tm.export(OUT / "stl" / f"{n}.stl")
        ex = tm.copy(); ex.apply_translation(np.array(p["explode"], float)); ex.export(OUT / "exploded" / f"{n}.stl")
        if p["flat"]:
            z, t = p["flat"]
            sec = cq.Workplane().add(p["shape"]).section(z + t / 2)
            try:
                exporters.export(sec, str(OUT / "dxf" / f"{n}.dxf"), exportType="DXF")
            except Exception as e:
                print("dxf", n, e)
        c = cq.Shape.centerOfMass(p["shape"])
        bb = p["shape"].BoundingBox()
        meta.append(dict(name=n, file=f"{n}.stl", group=p["group"], category=p["category"], material=p["material"],
                         process=p["process"], color=list(p["color"]), explode=list(map(float, p["explode"])),
                         mass_kg=round(p["mass"], 3), com_mm=[round(c.x, 1), round(c.y, 1), round(c.z, 1)],
                         bbox_mm=[round(v, 1) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)],
                         src=p["src"], notes=p["notes"], qty=p["qty"]))
    (OUT / "parts.json").write_text(json.dumps(meta, indent=1))
    return meta


def interference(parts, skip=("harness",)):
    """pairwise solid overlaps (bounding-box prefilter, exact OCC common volume)"""
    names = [n for n, p in parts.items() if p["category"] not in skip and p["group"] != "dock"]
    bad = []
    bbs = {n: parts[n]["shape"].BoundingBox() for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = bbs[a], bbs[b]
            if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
                continue
            v = parts[a]["shape"].intersect(parts[b]["shape"]).Volume()
            if v > 5.0:
                bad.append((a, b, round(v)))
    return bad


if __name__ == "__main__":
    import time
    t = time.time()
    P = build()
    meta = export(P)
    bad = interference(P)
    mb = sum(m["mass_kg"] for m in meta if m["group"] in ("base", "waist"))
    mr = sum(m["mass_kg"] for m in meta if m["group"] == "waist_rot")
    print(f"{len(P)} parts, base {mb:.1f} kg (dock excluded), {time.time() - t:.0f} s")
    print("INTERFERENCES:", len(bad))
    for b in bad:
        print("  ", b)
    json.dump(dict(interferences=bad), open(OUT / "interference.json", "w"), indent=1)
