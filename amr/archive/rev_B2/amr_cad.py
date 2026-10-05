"""Giorgio AMR (own base), rev B2 - parametric CadQuery model: chassis, 2 safety wheel drives, 4 sprung castors,
2 batteries, centre electronics bay, DIN bays, safety scanners, dock contacts, covers, cable harness routes and the
charging dock. Rev B2 (CAD_REV_B2.md): batteries on their side with the top cover outward, Mean Well / Discover
installation rules as invisible keep-out solids (category 'keepout'). Rev B has no waist joint: the 15 mm top deck is the superstructure flange (top at z = 353 mm).

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


# ====================================================================== keep-outs (rev B2)
def keepout(name, shape, owner, rule):
    """invisible check solid: free space required by a manufacturer installation rule. Not exported as a part, not rendered,
    0 kg; checked against every solid except its owner (and other keep-outs: overlapping free spaces are allowed)."""
    PARTS[f"KO_{name}"] = dict(shape=shape, material="purchased", process="keep-out (check solid)", group="keepout",
                               category="keepout", color=(1.0, 0.0, 1.0), explode=(0, 0, 0), mass=0.0, src=rule, flat=None,
                               qty=1, notes=f"owner={owner}", owner=owner)
    return shape


MW_RULE = "Mean Well DDR/DRDN installation manual: vertical, input terminals down, 40 mm above, 20 mm below, 5 mm left/right"


def din(name, x0, dims, zc, face, side, conv=False, color=None, mass=0.25, explode=(0, 0, 0), process=None, src="", notes=""):
    """DIN module on a rail. face = y of the rail front face, side = +1/-1 direction of the module depth.
    conv=True adds the Mean Well keep-out (KO_<name>) around it."""
    w, h, d = dims
    y0, y1 = sorted((face, face + side * d))
    s = box(x0, x0 + w, y0, y1, zc - h / 2, zc + h / 2)
    col = color or ((0.78, 0.78, 0.8) if conv else (0.85, 0.12, 0.1) if "contactor" in name else (0.25, 0.25, 0.28))
    add(name, s, "purchased", process or "purchased DIN module (amr/electrical/din_layout.md, netlist_amr.yaml)", category="purchased",
        color=col, explode=explode, mass=mass, src=src, notes=notes)
    if conv:
        k, a, b = CONV_KO["side"], CONV_KO["above"], CONV_KO["below"]
        keepout(name, box(x0 - k, x0 + w + k, y0, y1, zc - h / 2 - b, zc + h / 2 + a).cut(s), name, MW_RULE)
    return s


def rail(name, xa, xb, zc, face_from, face_to, explode=(0, 0, 0), notes="DIN rail TS35x7.5 EN 60715, M5 to the spine"):
    add(name, box(xa, xb, face_from, face_to, zc - 17.5, zc + 17.5), "purchased", notes, category="purchased",
        color=(0.7, 0.7, 0.72), explode=explode, mass=0.25 * (xb - xa) / 516)


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
    jx = (JETSON_BOX[0] + JETSON_BOX[1]) / 2
    deck = deck.cut(G.rounded_rect(jx, -23, 40, 30, DECK_T + 2, DECK_Z0 - 1, 8))           # rev B2: Jetson cables, under cover K06
    add("A02_top_deck", deck, "EN AW-6082-T6", "waterjet 15 mm 6082-T6 + CNC: column-foot M6 pattern (thread engagement >= 9 mm) and coffee-upright holes (as old P01), spine slots, K06/E51 M4 pattern + cable hole with edge protection; powder coat RAL 9016 textured",
        explode=(0, 0, 260), flat=(DECK_Z0, DECK_T), notes="IS the superstructure flange (old P01 + Ranger deck in one part); bolted to both spines, 4 end posts and bracket A06")

    for sy in (-1, 1):
        y0 = sy * SPINE_Y - (SPINE_T if sy > 0 else 0)
        yc = y0 + SPINE_T / 2
        sp = box(-SPINE_X, SPINE_X, y0, y0 + SPINE_T, PAN_Z1, DECK_Z0)
        sp = sp.cut(box(-60, 60, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 + 5, 97))            # SWD connector window (below the centre lower rail)
        for x in (-200, -140, 200):                                                      # harness windows (also the passive air return)
            sp = sp.cut(box(x - 17, x + 17, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 + 160, PAN_Z1 + 240))
        sp = sp.cut(box(121, 159, y0 - 1, y0 + SPINE_T + 1, 186, 224))                  # rev B2: 40 mm fan cut-out E42 (centre-bay supply)
        add(f"A03_spine_{'L' if sy > 0 else 'R'}", sp, "EN AW-6082-T6",
            "waterjet 6 mm 6082-T6, tapped M5 rows for the DIN rails on BOTH faces, M6 to pan/deck, M5 for the strap tabs and DSR plates",
            explode=(0, sy * 140, 0), flat=None, notes=f"structural wall + DIN panel ({'power' if sy > 0 else 'safety/control'} bay outside, centre bay inside)")
    # rev B2: bracket extending the left spine plane to the front-left corner (carries the corner rail for U7)
    add("A06_corner_bracket_FL", box(SPINE_X, 300, SPINE_Y - SPINE_T, SPINE_Y, 140, DECK_Z0), "EN AW-6082-T6",
        "waterjet 6 mm 6082-T6, splice plate M5 x4 to the spine end, M6 x2 to the deck; tapped M5 for the corner DIN rail",
        explode=(60, 140, 0), notes="no castor/scanner at this corner: free volume above the tower roof")
    # end posts (deck support at the ends), 30x30x3 tube: rev B2 moved to (+-320, +-115)
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
    """rev B2: each pack lies on its side, top cover facing outward (+x front, -x rear), 50 mm keep-out in front of the
    top cover over the full cover face, over-the-top straps (z 300..303) bolted to the spine inner faces. Service: remove
    the end cover (K01/K02 with its K05 edge length) and the 2 straps, unplug, slide the pack out along x."""
    Lx, Wy, H = BATT["Lx"], BATT["Wy"], BATT["H"]
    for bx in BATT_XS:
        sx = float(np.sign(bx))
        xin, xout = sx * BATT_X_IN, sx * (BATT_X_IN + Lx)
        tag = 'F' if bx > 0 else 'R'
        pack = box(xin, xout, -Wy / 2, Wy / 2, BATT_Z0, BATT_Z0 + H)
        add(f"B01_battery_{tag}_DLP-GC2-48V", pack, "purchased",
            "purchased Discover AES PRO DLP-GC2-48V, LFP 51.2 V 30 Ah, IEC 62619/CE/UN38.3", category="purchased",
            color=(0.10, 0.28, 0.55), explode=(sx * 330, 0, 0), mass=BATT["mass"],
            src="discoverbattery.com (SOURCED 14 kg, 260 L x 180 W x 254 H mm)",
            notes=f"lying on its side (805-0027 s.9.2: lying allowed, never upside down); top cover = face x = {xout:+.0f} (outward)")
        keepout(f"B01_{tag}_top_cover_50mm", box(xout, xout + sx * BATT_TOP_KO, -Wy / 2, Wy / 2, BATT_Z0, BATT_Z0 + H),
                f"B01_battery_{tag}_DLP-GC2-48V", "Discover 805-0027 Rev N s.9.2 p.10: maintain >= 50 mm above the top cover")
        add(f"B02_battery_pad_{tag}", box(xin + sx * 8, xout - sx * 8, -Wy / 2 + 8, Wy / 2 - 8, PAN_Z1, BATT_Z0), "EPDM",
            "die-cut 3 mm EPDM (slide surface: PTFE-faced strip on top, ESTIMATE)", explode=(sx * 300, 0, -30))
        for j, xs in enumerate((120.0, 230.0)):
            x = sx * xs
            st = box(x - 15, x + 15, -(SPINE_Y - SPINE_T), SPINE_Y - SPINE_T, BATT_Z0 + H, BATT_Z0 + H + 3)
            add(f"B03_battery_strap_{tag}{j}", st, "EN AW-5754-H22",
                "laser cut 3 mm + 2 bent tabs, M6 into the spine inner faces; over-the-top hold-down (805-0027 s.9.2), removable for service",
                explode=(sx * 330, 0, 90))


def centre_bay():
    """rev B2 centre bay x -78..78 between the packs, |y| <= 131 between the spine inner faces. DIN rails on the spine inner
    faces at two levels: LOW (z 120) = converters only, vertical, input terminals down; HIGH (z 274) = everything else, above
    the converter keep-outs. Facing modules at the same x and z never sum to more than 247 mm depth (2 x 123.5).
    Only ONE DDR-480 fits here under the Mean Well rule (two need 2 x 85.5 + 5 = 176 mm of x, the bay has 156; facing each
    other they need 258.4 > 247 mm): E50L stays, E50R goes to the right bay low front rail, U7 (E54) to the front-left corner.
    Cooling (electrical/din_layout.md s.6 losses, rev B2 contents): E50L ~6.1 W + 2 x DRDN40-24 4.8 W + U6/K4 ~4 W + CAN gw
    ~2 W + LYNK gw ~2 W + relays/fuses ~2 W = ~21 W (rev B1: 52 W incl. Jetson 20 W, UAR 6.1 W, U7 11 W, now moved out).
    Air path: side-bay intake fans (E40_*in) -> side bays -> 2 x 40 mm fans E42 in the spine cut-outs at x = +140 blow into
    the front battery/spine gaps (41 mm wide, open to the centre bay) -> centre bay (over the converters) -> rear
    battery/spine gaps -> rear end of the gaps (x -262) -> rear exhaust fans E40_*out. 2 x 40 mm at ~8 m3/h effective each
    -> ~5.3 W/K -> dT ~4 K at 21 W (ESTIMATE; NTC in the bay read by the Jetson)."""
    x0, x1, yb = CENTRE_BAY["x0"], CENTRE_BAY["x1"], CENTRE_BAY["y"]
    fL, fR = yb - 7.5, -(yb - 7.5)                       # rail front faces (left rail on the +y spine, right rail on the -y spine)
    ex = (0, 0, 520)
    for sy, f in ((1, fL), (-1, fR)):
        s_ = 'L' if sy > 0 else 'R'
        rail(f"E0C_{s_}_din_rail_low", x0 + 1, x1 - 1, Z_CRAIL_LO, sy * yb, f, explode=ex)
        rail(f"E0C_{s_}_din_rail_high", x0 + 1, (x1 - 1) if sy > 0 else 5.0, Z_CRAIL_HI, sy * yb, f, explode=ex)
    # LOW rails: converters (+ keep-outs)
    din("E50_dcdc_arm_L_DDR480C24", -73.0, DDR480, Z_CRAIL_LO, fL, -1, conv=True, mass=1.375, explode=ex,
        process="purchased Mean Well DDR-480C-24 (arm L 24 V bus, OpenArm variant), vertical, input terminals down", src="meanwell.com (SOURCED)")
    din("E52_arm_ORing_L_DRDN40-24", 17.5, DRDN40, Z_CRAIL_LO, fL, -1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DRDN40-24 (arm L bus ORing), vertical")
    din("E52_arm_ORing_R_DRDN40-24", -73.0, DRDN40, Z_CRAIL_LO, fR, 1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DRDN40-24 (arm R bus ORing), vertical")
    din("E58_U6_DDR60L5", -13.0, DDR60, Z_CRAIL_LO, fR, 1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DDR-60L-5 (head 5 V, 52.5 mm wide), vertical", src="DDR-60 spec (SOURCED)")
    din("E56_FCF_fuse", 44.5, (17.5, 82, 70), Z_CRAIL_LO, fR, 1, mass=0.1, explode=ex)
    # HIGH rails: no converters
    for name, xs, dims in (("E57_FAL_FAR_fuses", -76.0, (35, 82, 70)), ("E59_JR1_relays", -39.0, (12.4, 90, 80)),
                           ("E5A_XC_deck_terminals", -24.6, (30, 60, 50)), ("E36_CAN1_PCAN-Ethernet_gw", 7.4, (45, 100, 90))):
        din(name, xs, dims, Z_CRAIL_HI, fL, -1, mass=0.15, explode=ex)
    din("E55_K4_Finder22", -76.0, (17.5, 90, 70), Z_CRAIL_HI, fR, 1, mass=0.15, explode=ex)
    din("E5C_K4_interposing_relay_PLC-RSC", -56.5, (6.2, 90, 80), Z_CRAIL_HI, fR, 1, mass=0.04, explode=ex,
        notes="VERIFICATION 11: K4 coil 92 mA > 75 mA PNOZ auxiliary output")
    add("E38_G01_LYNK_II_gateway", box(10, 75, -yb, -yb + 30, 239, 309), "purchased",
        "purchased Discover LYNK II gateway, panel mount on the right spine inner face (CAD size ASSUMED 65x70x30; sell sheet 120x135x44, see CAD_REV_B2.md)",
        category="purchased", color=(0.25, 0.25, 0.28), explode=ex, mass=0.2)
    # DSR 50/5 clamps on plates in the 41 mm gaps between the packs (|y| <= 90) and the spine inner faces (|y| 131)
    w, h, d = DSR50
    for nm, xa, z0, sy in (("E5B_arm_clamp_L_DSR50-5", 165.0, 100.0, 1), ("E5B_arm_clamp_R_DSR50-5", 165.0, 100.0, -1),
                           ("E16_R1a_traction_clamp_DSR50-5", -259.0, 100.0, 1), ("E16_R1b_traction_clamp_DSR50-5", -259.0, 150.0, 1)):
        add(nm, box(xa, xa + w, sy * yb, sy * (yb - d), z0, z0 + h), "purchased",
            "purchased maxon DSR 50/5 (309687) 27 V, plate mount (any orientation) on the spine inner face, outside the pack slide path |y| <= 90",
            category="purchased", color=(0.25, 0.25, 0.28), explode=(0, sy * 120, 300), mass=0.25, src="maxongroup.com 309687 (SOURCED)")
    # centre-bay supply fans (40 mm) on the inner face of the spine cut-outs at x = +140, in the front gaps
    for sy in (1, -1):
        add(f"E42_gap_fan_{'L' if sy > 0 else 'R'}", box(120, 160, sy * yb, sy * (yb - 20), 185, 225), "purchased",
            "purchased 40x40x20 mm 24 V fan (IP54 class) + finger guard, blows side bay -> front gap -> centre bay",
            category="purchased", color=(0.1, 0.1, 0.11), explode=(0, sy * 120, 300), mass=0.03)
    add("E53_deck_grommet", G.rounded_rect(CABLE_PASS[0], CABLE_PASS[1], CABLE_PASS[2] + 10, CABLE_PASS[3] + 10, 6, DECK_Z1, 15)
        .cut(G.rounded_rect(CABLE_PASS[0], CABLE_PASS[1], CABLE_PASS[2] - 10, CABLE_PASS[3] - 10, 8, DECK_Z1 - 1, 8)), "purchased",
        "purchased split cable-entry frame, >= 10 entries (icotek KEL-DPZ class, IP54)", category="purchased", color=(0.08, 0.08, 0.09),
        explode=(0, 0, 300), mass=0.1)
    # Jetson on the deck at the rear, under a small cover (does not fit the centre bay any more)
    jx0, jx1, jy0, jy1, jz0, jz1 = JETSON_BOX
    add("E51_jetson_orin_nx_carrier", box(jx0, jx1, jy0, jy1, jz0, jz1), "purchased",
        "purchased NVIDIA Jetson Orin NX 16 GB on fanned carrier (12 V), on 4 M4 standoffs on the deck", category="purchased",
        color=(0.12, 0.12, 0.13), explode=(0, 0, 420), mass=0.7, src="ESTIMATE")
    k6 = box(jx0 - 5, jx1 + 5, jy0 - 5, jy1 + 5, DECK_Z1, jz1 + 8).cut(box(jx0 - 3, jx1 + 3, jy0 - 3, jy1 + 3, DECK_Z1 - 1, jz1 + 6))
    for x in np.arange(jx0 + 6, jx1 - 6, 12.0):                       # louvre slots both long sides (Jetson fan in/out)
        k6 = k6.cut(box(x, x + 5, jy0 - 7, jy1 + 7, DECK_Z1 + 15, jz1 - 5))
    add("K06_jetson_cover", k6, "EN AW-5754-H22", "laser cut + bent 2 mm 5754, slotted louvres, powder coat RAL 9016; M4 x4 to the deck",
        explode=(0, 0, 480), color=(0.92, 0.92, 0.9),
        notes="clearance: P22 coffee upright 15 mm (y), column foot P29 63 mm (x), coffee housing SH06 53 mm (z)")


def sensors_and_io():
    for k, (sx, sy, head) in enumerate(SCAN_CORNERS):
        cx, cy = sx * CASTER_XY[0] + 10 * sx, sy * CASTER_XY[1] + 10 * sy      # pushed 14 mm out along the diagonal
        z0 = TOWER_ROOF[1]
        s = place(box(-NS3["D"] / 2, NS3["D"] / 2, -NS3["W"] / 2, NS3["W"] / 2, 0, NS3["H"]), G.rotz(head), (cx, cy, z0))
        add(f"S01_nanoScan3_ProIO_{k}", s, "purchased", "purchased SICK nanoScan3 Pro I/O NANS3-CAAZ30AN1 (PL d, 128 field sets; no encoder inputs per datasheet)",
            category="purchased", color=(0.95, 0.8, 0.1), explode=(sx * 160, sy * 160, 0), mass=NS3["mass"], src="sick.com (SOURCED)")
    # dock collector: rev B2 rear face, off-centre at y = PAD_Y (out of the rear top-cover keep-out |y| <= 90)
    s = box(X0 + 2, X0 + 2 + ROBOPAD["D"], PAD_Y - ROBOPAD["W"] / 2, PAD_Y + ROBOPAD["W"] / 2, PAD_Z - ROBOPAD["H"] / 2, PAD_Z + ROBOPAD["H"] / 2)
    add("E01_robopad_collector_RPCOL90", s, "purchased", "purchased Roboteq RoboPad collector RPCOL90-100 (60 A cont., Hall docked sensor)",
        category="purchased", color=(0.85, 0.45, 0.1), explode=(-200, 0, 0), mass=ROBOPAD["mass"], src="Roboteq datasheet v1.3 (SOURCED)")
    # E-stops (both sides), service disconnect key (rear right), status LED band
    for sy in (-1, 1):
        add(f"E02_estop_{'L' if sy > 0 else 'R'}", cyl(20, 38, (0, sy * (Y1 + 36), 268), (0, -sy, 0)), "purchased",
            "purchased Siemens 3SU1 E-stop + 2x 3SU1400-1AA10-1CA0 NC (positive opening) + yellow enclosure plate", category="purchased",
            color=(0.85, 0.1, 0.1), explode=(0, sy * 120, 0), mass=0.08)
    add("E03_service_disconnect_ED250B", box(-340, -270, -210, -140, 145, 235), "purchased",
        "purchased Albright ED250B-L (with blowouts, 58 V) key-lockable service disconnect, key extension through the rear cover", category="purchased",
        color=(0.85, 0.1, 0.1), explode=(0, 160, 0), mass=0.6, src="albrightinternational.com (SOURCED)")


SIDE_EX = 260


def din_bays():
    """Side DIN bays on the spine OUTER faces (layout = CAD_REV_B2.md s.3; electrical/din_layout.md to be updated by the
    electrical stream): left (+y) = power, right (-y) = safety/control.
    Rails: LOW z 120 at |x| 98..200 (beside the SWD housing) = converters only; MID z 245 at |x| <= 95 (above the SWD
    housing, z >= 180); HIGH z 275 = non-converters above the converter keep-outs (z >= 222.6); corner rails above the
    castor towers without a scanner: front-left (on A06) and rear-right."""
    fL, fR = SPINE_Y + 7.5, -(SPINE_Y + 7.5)
    for sy, f in ((1, fL), (-1, fR)):
        s_ = 'L' if sy > 0 else 'R'
        ex = (0, sy * 250, 0)
        y0r = sy * SPINE_Y
        rail(f"E0{s_}_din_rail_lower_F", 98, 200, Z_RAIL_LO, y0r, f, ex)
        rail(f"E0{s_}_din_rail_lower_R", -218 if sy < 0 else -200, -98, Z_RAIL_LO, y0r, f, ex)
        if sy > 0:
            rail("E0L_din_rail_mid", -95, 95, Z_RAIL_MID, y0r, f, ex)
            rail("E0L_din_rail_upper_F", 96, 192, Z_RAIL_HI, y0r, f, ex)
            rail("E0L_din_rail_upper_R", -258, -100, Z_RAIL_HI, y0r, f, ex)
            rail("E0L_din_rail_corner_FL", 202, 298, Z_RAIL_CNR_FL, y0r, f, ex, notes="DIN rail TS35x7.5, M5 to the spine end + A06")
        else:
            rail("E0R_din_rail_upper", -217, 261, Z_RAIL_HI, y0r, f, ex)
            rail("E0R_din_rail_corner_RR", -258, -218, Z_RAIL_CNR_RR, y0r, f, ex)
    exL, exR = (0, SIDE_EX, 0), (0, -SIDE_EX, 0)
    # ---------------- LEFT (power)
    din("E13_U1_dcdc_DDR480C24", 105.0, DDR480, Z_RAIL_LO, fL, 1, conv=True, mass=1.375, explode=exL)
    din("E14_U2_dcdc_DDR480C24", -190.5, DDR480, Z_RAIL_LO, fL, 1, conv=True, mass=1.375, explode=exL)
    din("E11_K0_contactor_SW80B_on_plate", -93.0, (70, 110, 95), Z_RAIL_MID, fL, 1, mass=0.9, explode=exL)
    din("E10_F0_fuse_NH00_100A", -20.0, (40, 125, 90), Z_RAIL_MID, fL, 1, mass=0.4, explode=exL,
        notes="central: H01 = H02 in length (805-0027 s.9.7)")
    din("E30_U3_ORing_DRDN40-24", 25.0, DRDN40, Z_RAIL_MID, fL, 1, conv=True, mass=0.3, explode=exL,
        notes="z 200..290 above the SWD housing (top z 180 = keep-out bottom)")
    for name, xs, dims, m in (("E31_F8LR_SWD_fuses", 98.0, (35, 82, 70), 0.1), ("E32_T24_terminals", 135.0, (24, 60, 50), 0.1),
                              ("E19_0V_block", 161.0, (27, 60, 50), 0.1), ("E17_K0T_timer_Finder80", -256.0, (17.5, 90, 70), 0.1),
                              ("E12_K0P_precharge_relay", -236.5, (17.5, 90, 70), 0.1), ("E18_branch_fuses_10x38_x6", -217.0, (110, 82, 70), 0.3)):
        din(name, xs, dims, Z_RAIL_HI, fL, 1, mass=m, explode=exL)
    din("E54_U7_DDR480C24_coffee", 205.0, DDR480, Z_RAIL_CNR_FL, fL, 1, conv=True, mass=1.375, explode=(60, SIDE_EX, 0),
        notes="front-left corner above the castor tower (no scanner here); keep-out below = tower roof top z 134")
    # ---------------- RIGHT (safety / control)
    din("E34_U8_ideal_diode_DRDN40-48", -213.0, DRDN40, Z_RAIL_LO, fR, -1, conv=True, mass=0.3, explode=exR)
    din("E15_U4_dcdc_DDR240C24_S24", -153.0, DDR240, Z_RAIL_LO, fR, -1, conv=True, mass=0.6, explode=exR)
    din("E37_KS_signature_relay", -106.0, (6.2, 90, 70), Z_RAIL_LO, fR, -1, mass=0.04, explode=exR)
    din("E50_dcdc_arm_R_DDR480C24", 105.0, DDR480, Z_RAIL_LO, fR, -1, conv=True, mass=1.375, explode=exR,
        process="purchased Mean Well DDR-480C-24 (arm R 24 V bus, OpenArm variant), vertical, input terminals down",
        notes="moved out of the centre bay (only one DDR-480 fits there under the Mean Well rule)")
    din("E2G_U5_DDR120C12", -254.0, DDR120, Z_RAIL_CNR_RR, fR, -1, conv=True, mass=0.5, explode=(-60, -SIDE_EX, 0),
        notes="rear-right corner above the castor tower; FJ fuse moved to the upper rail (E2H)")
    PZ = (22.5, 101.4, 120)
    up = [("E20_SC1_PNOZ_m_ES_ETH", -215.0, PZ), ("E21_SC0_PNOZ_m_B0", -192.5, (45, 101.4, 120)),
          ("E22_SX1_PNOZ_m_EF_8DI4DO", -147.5, PZ), ("E2J_SX3_PNOZ_m_EF_4DI4DOR", -125.0, PZ), ("E2K_SX4_PNOZ_m_EF_4DI4DOR", -102.5, PZ),
          # -80..-57.5 kept free: SX2 PNOZ m EF 8DI4DO (C48 variant only)
          ("E2F_WF1-3_AUX48_fuses", -56.5, (52.5, 82, 70)), ("E25_NET1_switch_FL1008N", -3.0, (40, 110, 90)),
          ("E33_F7_charge_fuse", 38.0, (17.5, 82, 70)), ("E35_RSIG_X0R", 56.5, (22, 60, 50)), ("E27_XS24_terminals", 79.5, (70, 60, 50)),
          ("E2C_K1_contactor_3RT2026", 150.5, (45, 85, 97)), ("E2D_K2_contactor_3RT2026", 196.5, (45, 85, 97)),
          ("E2H_FJ_fuse_Jetson12V", 242.5, (17.5, 82, 70))]
    for name, xs, dims in up:
        col = (0.95, 0.8, 0.1) if "PNOZ" in name else None
        din(name, xs, dims, Z_RAIL_HI, fR, -1, color=col, explode=exR,
            mass={"E21": 0.45, "E2C": 0.4, "E2D": 0.4, "E25": 0.3}.get(name[:3], 0.2 if "PNOZ" in name else 0.15),
            notes="rev B2 new: VERIFICATION change 1 (relay outputs for SWD STO/INSafe and scanner inputs)" if "4DI4DOR" in name else "")
    # bay fans: 60 mm IP54 + filter. Intake: side covers at the middle (above the wheel arch, clear of the low converters);
    # exhaust: rear cover at y +-150, z 235..295 (clear of the rear top-cover keep-out |y| <= 90)
    for sy in (1, -1):
        add(f"E40_fan_{'L' if sy > 0 else 'R'}in", box(-30, 30, sy * (Y1 - 27), sy * (Y1 - 2), 150, 210), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, intake (side cover, above the wheel arch)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(0, sy * 200, 0), mass=0.12)
        add(f"E40_fan_{'L' if sy > 0 else 'R'}out", box(X0 + 2, X0 + 27, sy * 150 - 30, sy * 150 + 30, 235, 295), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, exhaust high (rear cover)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(-200, 0, 0), mass=0.12)
    # rear panel above the rear pack: reset SB1, key selector SK1, M12 enabling-pendant socket SE1
    for k, (yy, nm) in enumerate(((-50, "SB1_reset_blue"), (0, "SK1_key_selector"), (50, "SE1_M12_pendant_socket"))):
        add(f"E41_{nm}", cyl(15, 40, (X0 + 1, yy, E41_Z), (1, 0, 0)), "purchased", "purchased Siemens 3SU1 / M12 panel device", category="purchased",
            color=(0.15, 0.3, 0.8) if k == 0 else (0.2, 0.2, 0.22), explode=(-180, 0, 0), mass=0.05)


E41_Z = 318.0


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
    shell = shell.cut(box(X0 - 5, X0 + 10, PAD_Y - ROBOPAD["W"] / 2 - 6, PAD_Y + ROBOPAD["W"] / 2 + 6, PAD_Z - ROBOPAD["H"] / 2 - 6, PAD_Z + ROBOPAD["H"] / 2 + 6))
    for yy in (-50, 0, 50):
        shell = shell.cut(cyl(16, 20, (X0 - 5, yy, E41_Z), (1, 0, 0)))
    for sy in (1, -1):
        shell = shell.cut(box(-25, 25, sy * (Y1 + 5), sy * (Y1 - 10), 155, 205))                   # side intake fans
        shell = shell.cut(box(X0 - 5, X0 + 10, sy * 150 - 25, sy * 150 + 25, 240, 290))           # rear exhaust fans
    shell = shell.cut(cyl(12, 20, (X0 - 5, -175, 190), (1, 0, 0)))          # ED250B key
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
    add("K05_rubber_edge", bump, "EPDM", "extruded EPDM edge profile 22 mm, clipped on the cover skirts: the front/rear lengths come off with K01/K02 (battery slide-out path)",
        explode=(0, 0, -40))


def harness():
    """main cable routes (centre lines); IDs match amr/electrical/cable_schedule.csv. Rev B2: the pack terminals are on the
    outward top covers, so H01/H02 leave each pack through its top-cover keep-out (a connection cable is the one thing the
    manual expects there), run beside the pack (|y| 96, clear of the posts) and enter the left bay through the x = +-200
    spine windows; H01 and H02 are mirror images (equal length, 805-0027 s.9.7) ending at F0 (x = 0)."""
    H = []
    H.append(("H01_batt_F_to_fuse", [(345, 60, 285), (345, 96, 285), (240, 110, 245), (200, 134, 237), (120, 200, 300), (0, 200, 305)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H02_batt_R_to_fuse", [(-345, 60, 285), (-345, 96, 285), (-240, 110, 245), (-200, 134, 237), (-120, 200, 300), (0, 200, 305)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H03_bus48_to_centre_and_deck", [(-160, 200, 320), (-140, 160, 237), (-140, 110, 237), (-70, 100, 326), (62, 30, 326), (62, 20, 355)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H04_traction_24V_L", [(105, 200, 200), (60, 190, 190), (0, 175, 185)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H05_traction_24V_R", [(-100, 200, 200), (-200, 175, 237), (-200, 110, 237), (-170, 110, 320), (-170, -110, 320),
                                     (-200, -110, 237), (-200, -175, 237), (0, -175, 185)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H06_dock_to_charge_path", [(-346, PAD_Y, PAD_Z), (-300, -134, 145), (-262, -134, 145), (-215, -165, 120)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H07_safety_bus_scanner_F", [(-150, -200, 330), (250, -200, 330), (300, -205, 220)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H08_safety_bus_scanner_R", [(-150, -200, 330), (-250, -150, 330), (-300, 150, 320), (-310, 195, 225)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H09_safety_estops", [(-100, -200, 330), (0, -235, 300), (0, -262, 268)], 3.0, (0.95, 0.8, 0.1)))
    H.append(("H10_ethernet_safety_to_deck", [(17, -200, 215), (-140, -160, 237), (-140, -110, 237), (-60, -60, 326), (62, -30, 326), (62, -20, 355)], 3.0, (0.2, 0.5, 0.9)))
    for n, pts, r, c in H:
        add(n, tube(pts, r), "harness", "harness (see cable_schedule.csv)", category="harness", color=c, mass=0.0,
            explode=(0, 0, 0))


def dock():
    """wall dock (floor-standing, bolted to floor + wall): RoboPad base + charger + guide rails + AprilTag/reflector.
    Rev B2: the RoboPad base follows the collector to y = PAD_Y; the guide rails and the AprilTag stay on the robot centre
    line (they locate the robot body; the pad offset is a fixed transform in the Nav2 dock plugin). The guide rails run
    OUTSIDE the robot outline (|y| 292..296, robot incl. rubber edge |y| <= 284) instead of under it (rev B1 rails at
    |y| 150..230 overlapped the pan, rear cover and rubber edge when docked - the dock was never in the interference check)."""
    xd = X0 - 8.0                                   # dock contact face when docked
    base = box(xd - 300, xd - 20, -300, 300, 0, 6)
    base = base.fuse(box(xd - 300, xd - 296, -300, 300, 6, 520))                    # back plate to the wall (4 mm)
    for sy in (-1, 1):                                                               # guide rails: 4 mm sheet, 8 mm side play + lead-in
        base = base.fuse(box(xd - 296, xd + 60, sy * 292, sy * 296, 6, 76))
        a, b = (xd + 60, sy * 294), (xd + 180, sy * 350)
        L_ = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        base = base.fuse(place(box(0, L_, -2, 2, 0, 70), G.rotz(ang), (a[0], a[1], 6)))
        base = base.fuse(box(xd - 20, xd + 190, sy * 288, sy * 362, 0, 6))             # floor strip under the rail (anchors)
    add("X01_dock_frame", base, "S355MC", "laser cut + bent 4 mm S355MC, welded, powder coat; floor anchors M10 x6, wall M8 x2",
        group="dock", explode=(-200, 0, 0), color=(0.25, 0.26, 0.28))
    add("X02_robopad_base_RPBAS90", box(xd - 34, xd, PAD_Y - ROBOPAD["W"] / 2, PAD_Y + ROBOPAD["W"] / 2, PAD_Z - ROBOPAD["H"] / 2, PAD_Z + ROBOPAD["H"] / 2),
        "purchased", "purchased Roboteq RoboPad base RPBAS90-100 (contacts, Hall sensor)", group="dock", category="purchased",
        color=(0.85, 0.45, 0.1), explode=(-260, 0, 0), mass=0.4)
    add("X03_pad_mount", box(xd - 296, xd - 34, PAD_Y - 70, PAD_Y + 70, 88, 92).fuse(box(xd - 40, xd - 34, PAD_Y - 70, PAD_Y + 70, 6, 150)),
        "S355MC", "bent 3 mm bracket", group="dock", explode=(-230, 0, 0))
    add("X04_charger_NPB1700_48", box(xd - 255, xd - 105, -150, -50, 180, 360), "purchased",
        "purchased Mean Well NPB-1700-48 (25 A, CANbus, IEC 60335-2-29, DIP preset 'flooded' 56.8/53.6 V) in IP20 housing", group="dock", category="purchased",
        color=(0.7, 0.7, 0.72), explode=(-300, 0, 120), mass=3.3)
    add("X05_dock_controller_relay", box(xd - 255, xd - 175, 50, 150, 220, 330), "purchased",
        "purchased DIN box: controller + DC contactor with blowouts (output OFF unless Hall + handshake over Wi-Fi/Ethernet)", group="dock",
        category="purchased", color=(0.25, 0.25, 0.28), explode=(-300, 0, 120), mass=0.8)
    add("X08_dock_OV_relay_59V", box(xd - 170, xd - 147.5, 60, 150, 230, 320), "purchased",
        "purchased DIN DC over-voltage monitoring relay set to 59 V (Finder 71-series class, datasheet covering 60 V DC): opens the dock contactor (VERIFICATION M12, RoboPad <= 60 V under fault)",
        group="dock", category="purchased", color=(0.25, 0.25, 0.28), explode=(-300, 0, 120), mass=0.15, src="ESTIMATE envelope")
    add("X06_apriltag_reflector_plate", box(xd - 262, xd - 258, -120, 120, 380, 500), "purchased",
        "AprilTag 36h11 + retro-reflective strip (lidar profile), on the robot centre line (z 380..500: out of the scan plane)", group="dock", category="purchased",
        color=(0.95, 0.95, 0.95), explode=(-320, 0, 0), mass=0.2)
    add("X07_dock_cover", box(xd - 260, xd - 30, -255, 255, 175, 370).cut(box(xd - 257, xd - 33, -252, 252, 172, 367)),
        "EN AW-5754-H22", "bent 2 mm, powder coat, vent slots", group="dock", explode=(-260, 0, 200), color=(0.92, 0.92, 0.9))


def build():
    chassis(); drives(); casters(); batteries(); centre_bay(); sensors_and_io(); din_bays(); covers(); harness(); dock()
    return PARTS


def export(parts):
    from cadquery import exporters
    import shutil
    for d in ("step", "stl", "dxf", "exploded", "keepout"):
        shutil.rmtree(OUT / d, ignore_errors=True)            # no stale files from deleted parts
        (OUT / d).mkdir(parents=True, exist_ok=True)
    meta, kos = [], []
    for n, p in parts.items():
        if p["category"] == "keepout":                         # check solids: STL for viewing only, not in parts.json
            tm = G.shape_to_trimesh(p["shape"], tol=0.4)
            tm.export(OUT / "keepout" / f"{n}.stl")
            bb = p["shape"].BoundingBox()
            kos.append(dict(name=n, owner=p["owner"], rule=p["src"], file=f"{n}.stl",
                            bbox_mm=[round(v, 1) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)]))
            continue
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
    (OUT / "keepouts.json").write_text(json.dumps(kos, indent=1))
    return meta


def _bb_apart(A, B, tol=0.0):
    return (A.xmax <= B.xmin + tol or B.xmax <= A.xmin + tol or A.ymax <= B.ymin + tol or B.ymax <= A.ymin + tol
            or A.zmax <= B.zmin + tol or B.zmax <= A.zmin + tol)


def _common(a, b):
    return a.intersect(b).Volume()


def interference(parts, skip=("harness",)):
    """1) pairwise solid overlaps of the robot (bounding-box prefilter, exact OCC common volume > 5 mm3);
    2) every keep-out against every robot solid except its owner (keep-out vs keep-out = free space vs free space: allowed);
    3) dock (docked) against the robot."""
    robot = [n for n, p in parts.items() if p["category"] not in skip + ("keepout",) and p["group"] != "dock"]
    dockp = [n for n, p in parts.items() if p["group"] == "dock"]
    kos = [n for n, p in parts.items() if p["category"] == "keepout"]
    bbs = {n: parts[n]["shape"].BoundingBox() for n in robot + dockp + kos}
    bad, ko_bad, dock_bad, ko_checked = [], [], [], 0
    for i, a in enumerate(robot):
        for b in robot[i + 1:]:
            if _bb_apart(bbs[a], bbs[b]):
                continue
            v = _common(parts[a]["shape"], parts[b]["shape"])
            if v > 5.0:
                bad.append((a, b, round(v)))
    for k in kos:
        for b in robot:
            if b == parts[k]["owner"]:
                continue
            ko_checked += 1
            if _bb_apart(bbs[k], bbs[b]):
                continue
            v = _common(parts[k]["shape"], parts[b]["shape"])
            if v > 5.0:
                ko_bad.append((k, b, round(v)))
    for a in dockp:
        for b in robot:
            if _bb_apart(bbs[a], bbs[b]):
                continue
            v = _common(parts[a]["shape"], parts[b]["shape"])
            if v > 5.0:
                dock_bad.append((a, b, round(v)))
    return bad, ko_bad, dock_bad, ko_checked


def slide_paths(parts):
    """battery service: the volume each pack sweeps when pulled out along x must hold only the pack itself, its keep-out,
    its pad and the removable end cover (K01/K02 + the K05 edge length clipped to it)."""
    res = {}
    allowed = ("K01_cover_F", "K02_cover_R", "K05_rubber_edge")
    for bx in BATT_XS:
        sx = float(np.sign(bx)); tag = 'F' if bx > 0 else 'R'
        path = box(sx * BATT_X_IN, sx * (X1 + 30), -BATT["Wy"] / 2, BATT["Wy"] / 2, BATT_Z0 + 0.01, BATT_Z0 + BATT["H"] - 0.01)
        pb = path.BoundingBox()
        hits = []
        for n, p in parts.items():
            if p["category"] in ("harness", "keepout") or p["group"] == "dock" or n.startswith(f"B01_battery_{tag}") or n in allowed:
                continue
            if _bb_apart(pb, p["shape"].BoundingBox()):
                continue
            v = _common(path, p["shape"])
            if v > 1.0:
                hits.append((n, round(v)))
        res[tag] = hits
    return res


if __name__ == "__main__":
    import time
    t = time.time()
    P = build()
    meta = export(P)
    bad, ko_bad, dock_bad, nko = interference(P)
    sp = slide_paths(P)
    mb = sum(m["mass_kg"] for m in meta if m["group"] in ("base", "waist"))
    nparts = len(meta)
    print(f"{nparts} parts (+{sum(1 for p in P.values() if p['category'] == 'keepout')} keep-outs), base {mb:.1f} kg (dock excluded), {time.time() - t:.0f} s")
    print("INTERFERENCES:", len(bad))
    for b in bad:
        print("  ", b)
    print(f"KEEP-OUT VIOLATIONS: {len(ko_bad)} ({nko} keep-out/part pairs checked)")
    for b in ko_bad:
        print("  ", b)
    print("DOCK (docked) INTERFERENCES:", len(dock_bad))
    for b in dock_bad:
        print("  ", b)
    print("BATTERY SLIDE PATHS:", sp)
    json.dump(dict(interferences=bad, keepout_violations=ko_bad, keepout_pairs_checked=nko, dock_interferences=dock_bad,
                   battery_slide_path_obstacles=sp), open(OUT / "interference.json", "w"), indent=1)
