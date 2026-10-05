"""Giorgio AMR (own base), rev B4 - parametric CadQuery model: chassis, 2 safety wheel drives, 4 sprung castors,
2 batteries, centre electronics bay, DIN bays, safety scanners, dock contacts, covers, cable harness routes and the
charging dock. Rev B2 (CAD_REV_B2.md): batteries on their side with the top cover outward, Mean Well / Discover
installation rules as invisible keep-out solids (category 'keepout'). Rev B3 (CAD_REV_B3.md): sprung D80 castors on
MGN15 guides in the spine/battery gaps with swivel keep-outs, DIN layout = electrical/din_layout.md rev B3, LYNK II at its real size. Rev B4 (CAD_REV_B4.md): SWD 125 at its documented 196 mm / 7 kg in drive tunnels E43 (F3/F4), centre bay rearranged, deck doubler A09, PCAN and NPB-750 at their real sizes, SR3 for the 0.7 m/s band. Rev B has no waist joint: the 15 mm top deck is the superstructure flange (top at z = 353 mm).

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
                               qty=1, notes=f"owner={owner}", owner=owner if isinstance(owner, tuple) else (owner,))
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
CORNERS = [(1, 1, "FL"), (1, -1, "FR"), (-1, 1, "RL"), (-1, -1, "RR")]
SCAN_TAGS = {"FR", "RL"}                                 # scanner corners (SCAN_CORNERS); FL / RR carry corner DIN rails instead


def lbox(sx, sy, u0, u1, v0, v1, z0, z1):
    """box in castor-local coordinates (CASTOR_SUSPENSION.md s.6): u = sx*(x - sx*xc), v = sy*(y - sy*yc), outboard positive"""
    xc, yc = CASTER_XY
    return box(sx * (xc + u0), sx * (xc + u1), sy * (yc + v0), sy * (yc + v1), z0, z1)


def lpt(sx, sy, u, v):
    return sx * (CASTER_XY[0] + u), sy * (CASTER_XY[1] + v)


def chassis():
    pan = poly(outline(6.0), PAN_T, PAN_Z0)
    # wheel wells (wheel + 12 mm clearance) and caster holes
    for sy in (-1, 1):
        pan = pan.cut(box(-WHEEL_D / 2 - 14, WHEEL_D / 2 + 14, sy * (WHEEL_Y - WHEEL_W / 2 - 10), sy * (WHEEL_Y + WHEEL_W / 2 + 12),
                          PAN_Z0 - 1, PAN_Z1 + 1))
    for sx, sy, _ in CORNERS:                            # rev B3: corner cut r 86 about the castor axis (opens the pan chamfer edge)
        pan = pan.cut(cyl(PAN_CUT_R, PAN_T + 2, (sx * CASTER_XY[0], sy * CASTER_XY[1], PAN_Z0 - 1)))
    for sy in (-1, 1):                                    # rev B4: slot for the coaxial SWD body (D118) from the tunnel inlet to the wheel well
        pan = pan.cut(box(-62, 62, min(sy * 22, sy * 200), max(sy * 22, sy * 200), PAN_Z0 - 1, PAN_Z1 + 1))
    add("A01_floor_pan", pan, "S355MC", "laser cut 5 mm S355MC, deburr, zinc-flake or powder coat; PEM studs M6; corner cuts r 86 about the castor axes; rev B4 SWD slots |x| 62, |y| 22..200 (tunnel inlet + body)",
        explode=(0, 0, -160), flat=(PAN_Z0, PAN_T), notes="low and heavy on purpose: ballast for tipping; rev B3: castor loads go to the spines, not the pan")

    deck = poly(outline(4.0), DECK_T, DECK_Z0)
    cx_, cy_, lx_, ly_ = CABLE_PASS
    deck = deck.cut(G.rounded_rect(cx_, cy_, lx_, ly_, DECK_T + 2, DECK_Z0 - 1, 12))      # grommet: base -> superstructure cables
    jx = (JETSON_BOX[0] + JETSON_BOX[1]) / 2
    deck = deck.cut(G.rounded_rect(jx, -23, 40, 30, DECK_T + 2, DECK_Z0 - 1, 8))           # rev B2: Jetson cables, under cover K06
    add("A02_top_deck", deck, "EN AW-6082-T6", "waterjet 15 mm 6082-T6 + CNC: column-foot M6 pattern (thread engagement >= 9 mm) and coffee-upright holes (as old P01), spine slots, K06/E51 M4 pattern + cable hole with edge protection; M4 for the DSR plates and the LYNK bracket underneath; powder coat RAL 9016 textured",
        explode=(0, 0, 260), flat=(DECK_Z0, DECK_T), notes="IS the superstructure flange (old P01 + Ranger deck in one part); bolted to both spines, 3 end posts and brackets A06/A07/A08")

    nx0, nx1, nz0, nz1 = SPINE_NOTCH
    for sy in (-1, 1):
        y0 = sy * SPINE_Y - (SPINE_T if sy > 0 else 0)
        sp = box(-SPINE_X, SPINE_X, y0, y0 + SPINE_T, PAN_Z1, DECK_Z0)
        sp = sp.cut(box(-TUNNEL["x"] - 1, TUNNEL["x"] + 1, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 - 1, TUNNEL["z_top"] + 1))   # rev B4: drive notch (SWD body + tunnel E43 pass through)
        for x in (-230, -140, 230):                                                      # harness windows (also the passive air return); rev B3 x +-200 -> +-230 (castor rails at |x| 177.5..192.5)
            sp = sp.cut(box(x - 17, x + 17, y0 - 1, y0 + SPINE_T + 1, PAN_Z1 + 160, PAN_Z1 + 240))
        sp = sp.cut(box(121, 159, y0 - 1, y0 + SPINE_T + 1, 186, 224))                  # rev B2: 40 mm fan cut-out E42 (centre-bay supply)
        for sx in (-1, 1):                                                               # rev B3: end notch (castor swivel space + carriage tongue)
            sp = sp.cut(box(sx * nx0, sx * (nx1 + 1), y0 - 1, y0 + SPINE_T + 1, PAN_Z1 - 1, nz1))
        add(f"A03_spine_{'L' if sy > 0 else 'R'}", sp, "EN AW-6082-T6",
            "waterjet 6 mm 6082-T6, tapped M5 rows for the DIN rails on BOTH faces, M3 x 6 deep for the MGN15R castor rails, M6 to pan/deck, M5 for the strap tabs, M6 slots for the spring brackets; end notches |x| 202..262 z 37..128",
            explode=(0, sy * 140, 0), flat=None, notes=f"rev B4: drive notch |x| 73 z 37..130 (spine section above it 208 mm, CALC s.9); structural wall + DIN panel ({'power' if sy > 0 else 'safety/control'} bay outside, centre bay inside); carries the castor springs, guides and tower roofs (rev B3)")
    # spine-plane corner brackets: A06 (FL, rail for U7 + roof), A07 (RR, rail for U8 + roof + deck corner, replaces the RR post), A08 (RL, left HIGH rail end, above the scanner)
    add("A06_corner_bracket_FL", box(SPINE_X, 300, SPINE_Y - SPINE_T, SPINE_Y, TOWER_ROOF[1], DECK_Z0), "EN AW-6082-T6",
        "waterjet 6 mm 6082-T6, splice plate M5 x4 to the spine end, M6 x2 to the deck, M6 x2 to the tower roof; tapped M5 for the corner DIN rail",
        explode=(60, 140, 0), notes="no scanner at this corner: free volume above the tower roof; carries the FL roof (rev B3)")
    add("A07_corner_bracket_RR", box(-340, -SPINE_X, -SPINE_Y, -(SPINE_Y - SPINE_T), TOWER_ROOF[1], DECK_Z0), "EN AW-6082-T6",
        "waterjet 6 mm 6082-T6, splice plate M5 x4 to the spine end, M6 x3 to the deck, M6 x2 to the tower roof; tapped M5 for the corner DIN rail",
        explode=(-60, -140, 0), notes="rev B3: replaces the RR end post (a post at (-360, -106) would hit the RoboPad collector E01)")
    add("A08_rail_bracket_RL", box(-300, -SPINE_X, SPINE_Y - SPINE_T, SPINE_Y, 220, DECK_Z0), "EN AW-6082-T6",
        "waterjet 6 mm 6082-T6, splice plate M5 x2 to the spine end, M6 x2 to the deck; tapped M5 for the left HIGH rail extension",
        explode=(-60, 140, 0), notes="rev B3: above the RL scanner (z >= 220 > housing top 214.5)")
    add("A10_rail_bracket_FR", box(SPINE_X, 300, -SPINE_Y, -(SPINE_Y - SPINE_T), 220, DECK_Z0), "EN AW-6082-T6",
        "waterjet 6 mm 6082-T6, splice plate M5 x2 to the spine end, M6 x2 to the deck; tapped M5 for the right HIGH rail extension (CAN1, SR3)",
        explode=(60, -140, 0), notes="rev B4: right HIGH rail extended to x 298 (SR3 + CAN1 at its real size); above the FR scanner (z >= 220)")
    d = DOUBLER
    add("A09_deck_doubler", box(d["x0"], d["x1"], -(SPINE_Y - SPINE_T), SPINE_Y - SPINE_T, DECK_Z0 - d["t"], DECK_Z0), "EN AW-6082-T6",
        "waterjet 15 mm 6082-T6 doubler under the deck at the column foot: the 8 foot M6 go through deck + doubler into nuts (or M6 tapped in the doubler); M5 x6 to each spine top edge angle",
        explode=(0, 0, 200), flat=(DECK_Z0 - d["t"], d["t"]),
        notes="rev B4 (G-19): CALC s.9 strip b = 62 mm (bolt pitch, lower bound) with deck + doubler; x -160..34 clear of the DSR plates and the cable hole")
    # end posts (deck support at the ends), 30x30x3 tube: rev B3 (+-360, +-106); none at RR (A07 instead)
    px, py = POSTS[0]
    for sx, sy, tag in CORNERS:
        if tag == "RR":
            continue
        x, y = sx * px, sy * py
        add(f"A04_post_{tag}", box(x - 15, x + 15, y - 15, y + 15, PAN_Z1, DECK_Z0)
            .cut(box(x - 12, x + 12, y - 12, y + 12, PAN_Z1 - 1, DECK_Z0 + 1)), "EN AW-6082-T6",
            "30x30x3 square tube EN 755-2, cut + drill; M6 tab for the tower roof", explode=(sx * 60, 0, 0))
    # tower roofs (rev B3): no legs (they were inside the swivel circle). 6 mm S355MC 128..134, carried by the spine stub above the
    # notch (y 137 edge, |x| 202..262), the corner bracket (A06 FL / A07 RR) and the post tab; the PU bump pad of the castor
    # carriage hits its underside right above the castor axis (bump stop, up to 815 N, CALC s.9).
    for sx, sy, tag in CORNERS:
        xmax = 400 if tag in SCAN_TAGS else 340                                         # scanner seat to the corner; else clear of E01 / covers
        rf = box(sx * 202, sx * xmax, sy * SPINE_Y, sy * 400, TOWER_ROOF[0], TOWER_ROOF[1])
        rf = rf.fuse(box(sx * SPINE_X, sx * xmax, sy * (SPINE_Y - SPINE_T), sy * SPINE_Y, TOWER_ROOF[0], TOWER_ROOF[1]))
        if tag != "RR":                                                                  # tab to the post
            rf = rf.fuse(box(sx * (px - 15), sx * (px + 15), sy * (py + 15), sy * SPINE_Y, TOWER_ROOF[0], TOWER_ROOF[1]))
        rf = rf.intersect(poly(outline(COVER_T + 2), 400, 0))
        add(f"A05_tower_roof_{tag}", rf, "S355MC",
            "laser cut 6 mm S355MC roof, bent flange M6 x3 to the spine stub, M6 to bracket/post; bump-pad landing on the castor axis; scanner seat machined (FR/RL)",
            explode=(0, 0, 90), notes="rev B3: legs removed (inside the swivel circle); roof top z 134 unchanged -> scan plane 184.5")


def drives():
    """rev B4 (F4, CERTAINTY.md): ez-Wheel SWD 125 1-stage + external brake at its documented size: wheel D125 x 49.7, coaxial
    body (gearbox, motor, electronics, brake) to L = 196 mm from the wheel outer face (SWD manual v2.0.2 p.28), 7.0 kg. The body
    reaches |y| 60.85, i.e. through the spine notch into the centre bay (rev B3 had an ESTIMATE 190 x 66 x 135 box above the axle).
    Each drive is held by two 8 mm cheek plates D02 bolted to its gearbox flats (M6 fixing points 50 x 100, manual p.28) and to the
    pan; it runs in its own tunnel E43 (tunnels())."""
    r = WHEEL_D / 2
    rb = SWD_BODY_D / 2
    for sy in (-1, 1):
        s_ = 'L' if sy > 0 else 'R'
        yo = sy * (WHEEL_Y + WHEEL_W / 2)                       # wheel outer face
        yw = sy * (WHEEL_Y - WHEEL_W / 2)                       # wheel inner face
        wheel = cyl(r, WHEEL_W, (0, min(yo, yw), r), (0, 1, 0))
        yi = sy * SWD_Y_IN
        body = cyl(rb, abs(yw - yi), (0, min(yw, yi), r), (0, 1, 0))
        add(f"D01_ezwheel_SWD125_{s_}", wheel.fuse(body), "purchased",
            "purchased ez-Wheel SWD 125 EW2A-125HN04B (4:1 1-stage, external brake), safety encoder, CANopen Safety; L 196 mm, 7.0 kg (manual p.28)",
            category="purchased", color=(0.95, 0.55, 0.12), explode=(0, sy * 220, -60), mass=SWD_MASS,
            src="ez-Wheel SWD manual v2.0.2 p.27-28 (SOURCED L 196 mm, 7 kg, wheel 49.7 mm; body D118 cross-section ESTIMATE)")
        keepout(f"D01_connectors_{s_}", box(-50, 50, min(yi, yi - sy * SWD_CONN_KO), max(yi, yi - sy * SWD_CONN_KO), r, r + rb),
                f"D01_ezwheel_SWD125_{s_}", "SWD manual p.20: I/O, 24 VDC, CAN (M12) and USB (M8) connectors in the upper half of the inboard end face; 40 mm for angled plugs + cable bend")
        for sx in (-1, 1):                                      # cheek plates on the gearbox flats (x +-59), pan to above the axle
            add(f"D02_swd_cheek_{s_}{'F' if sx > 0 else 'A'}", box(sx * 60, sx * 68, sy * 140, sy * 200, PAN_Z1, 118), "EN AW-6082-T6",
                "waterjet 8 mm 6082-T6 cheek: 4 x M6 into the SWD gearbox fixing points (50 x 100, manual p.28), 2 x M6 PEM to the pan, angle to the spine",
                explode=(sx * 40, sy * 170, -40))


def tunnels():
    """rev B4 (F3): each SWD body runs in a 2 mm 5754 tunnel E43 that separates it from the side-bay and centre-bay air. Inlet: the
    pan slot under the inboard end (|y| 22..100, room air from under the robot); the slot outboard of |y| 100 carries an EPDM brush
    strip; the outboard baffle (|y| 205..207, D 121 hole + lip seal around the body) closes the tunnel against the wheel well. Outlet:
    the 60 mm tunnel fan E44 on the hood in the side bay (|y| 140..200) blows the tunnel air into the side bay, ahead of the bay exhaust
    fan E40_*out. The SWD housing therefore sees room air (SWD rating 0..+40 C), the drive losses go to the side bay (thermal model,
    electrical/netlist_amr.yaml 'thermal')."""
    T = TUNNEL
    x, t, zt = T["x"], T["t"], T["z_top"]
    zc = WHEEL_D / 2
    for sy in (-1, 1):
        s_ = 'L' if sy > 0 else 'R'
        ya, yb = sy * T["y_end"], sy * (T["y_baffle"] + 2.0)
        y0, y1 = min(ya, yb), max(ya, yb)
        hood = box(-x, x, y0, y1, zt - t, zt)                                                        # roof
        for sx in (-1, 1):
            hood = hood.fuse(box(sx * (x - t), sx * x, y0, y1, PAN_Z1, zt))                          # side walls
        hood = hood.fuse(box(-x, x, min(ya, ya + sy * t), max(ya, ya + sy * t), PAN_Z1, zt))         # inboard end cap
        bf = box(-x, x, min(sy * T["y_baffle"], sy * (T["y_baffle"] + 2)), max(sy * T["y_baffle"], sy * (T["y_baffle"] + 2)), PAN_Z1, zt)
        bf = bf.cut(cyl(SWD_BODY_D / 2 + 1.5, 10, (0, sy * (T["y_baffle"] - 4), zc), (0, sy, 0)))
        hood = hood.fuse(bf)
        hood = hood.cut(box(-29, 29, min(sy * 141, sy * 199), max(sy * 141, sy * 199), zt - t - 1, zt + 1))   # E44 opening (fan sits on the roof)
        add(f"E43_swd_tunnel_{s_}", hood, "EN AW-5754-H22",
            "laser cut + bent 2 mm 5754, riveted; EPDM lip seal at the spine notch, around the SWD body (baffle) and on the pan slot |y| 100..207 (brush strip); "
            "inlet = pan slot under the inboard end, outlet = tunnel fan E44",
            explode=(0, sy * 200, 140), color=(0.80, 0.81, 0.83),
            notes="F3 fix (CERTAINTY.md): SWD 0..+40 C rating vs side-bay air 44-46 C; the SWD now sees room air (TP-11 acceptance in ce/TEST_PLAN.md)")
        add(f"E44_tunnel_fan_{s_}", box(-30, 30, sy * 140 if sy > 0 else sy * 200, sy * 200 if sy > 0 else sy * 140, zt, zt + 25), "purchased",
            "purchased 60x60x25 mm 24 V fan (same type as E40), on the tunnel hood, blows tunnel air up into the side bay", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(0, sy * 200, 200), mass=0.1)


def swivel_profile(margin=5.0, sweep=True):
    """radius of the castor swivel envelope vs body z (CASTOR_SUSPENSION.md s.4): wheel r_w(z) = hypot(F + sqrt(R^2 - (z-40)^2), w/2)
    for z 0..80, fork r 50 z 80..98 (castor frame), swept over the travel -2.5..+17 (sweep=True), plus margin."""
    F, R, hw = CASTER_TRAIL, CASTER_D / 2, CASTER_W / 2
    def rc(zc):
        if 0.0 <= zc <= 2 * R:
            return math.hypot(F + math.sqrt(max(0.0, R * R - (zc - R) ** 2)), hw)
        if 2 * R < zc <= 98.0:
            return CASTER_FORK_R
        return 0.0
    d0, d1 = SUSP_TRAVEL if sweep else (0.0, 0.0)
    def r(z):
        return max(rc(z - d) for d in np.linspace(d0, d1, 40)) if sweep else rc(z)
    return r, margin


def swivel_solid(sx, sy, z0, z1, margin=5.0, sweep=True, dz=1.0):
    """solid of revolution about the castor axis from the profile above (stacked discs, 1 mm steps)"""
    r, m = swivel_profile(margin, sweep)
    cx, cy = sx * CASTER_XY[0], sy * CASTER_XY[1]
    sol = None
    z = z0
    while z < z1 - 1e-6:
        zt = min(z + dz, z1)
        rr = max(r(z), r(zt), r((z + zt) / 2))
        if rr > 0:
            d = cyl(rr + m, zt - z, (cx, cy, z))
            sol = d if sol is None else sol.fuse(d)
        z = zt
    return sol.clean()


def casters():
    """rev B3 sprung castor (CASTOR_SUSPENSION.md s.6), drawn in castor-local coordinates at each corner. Moving parts: castor C01,
    carriage weldment C02, PU bump pad C03, MGN15H blocks C08, spring ends C04. Fixed: spring bracket C05, droop stop C06,
    MGN15R rail C07 (all on the spine inner face, in the 41 mm spine/battery gap)."""
    zp = CASTER_H
    for sx, sy, tag in CORNERS:
        L = lambda *a: lbox(sx, sy, *a)
        xc, yc = sx * CASTER_XY[0], sy * CASTER_XY[1]
        # C01 castor: plate 100 x 85 (z 98..102), fork, wheel D80 x 30 trailing 38 mm inward (u -38), axle z 40
        c = L(-CASTER_PLATE[0] / 2, CASTER_PLATE[0] / 2, -CASTER_PLATE[1] / 2, CASTER_PLATE[1] / 2, zp - CASTER_PLATE_T, zp)
        c = c.fuse(L(-46, 10, -19, 19, 88, zp - CASTER_PLATE_T))
        for vs in (-1, 1):
            c = c.fuse(L(-46, -30, vs * 15, vs * 19, 40, 88))
        wx, wy = lpt(sx, sy, -CASTER_TRAIL, 0)
        c = c.fuse(cyl(CASTER_D / 2, CASTER_W, (wx, wy - CASTER_W / 2, CASTER_D / 2), (0, 1, 0)))
        add(f"C01_castor_{tag}_Blickle_L-ALST_80K", c, "purchased",
            "purchased Blickle L-ALST 80K (ID 754464): swivel castor D80 x 30 Softhane 75 ShA, Al centre, ball bearing, 200 kg @ 4 km/h, H 102, plate 100 x 85, holes 80 x 60 d9, offset 38",
            category="purchased", color=(0.12, 0.12, 0.13), explode=(0, 0, -160), mass=CASTER_MASS,
            src="blickle.com/product/l-alst-80k-754464 (SOURCED; plate thickness and fork envelope ESTIMATE until the Blickle CAD)")
        # C02 carriage weldment: carriage plate + tongue (through the spine notch) + mast (bolted to both blocks) + shelf (spring seats)
        w = L(-50, 50, -42.5, 42.5, zp, zp + 6)
        w = w.fuse(L(-55, -13, -65, -40, zp, zp + 6))
        w = w.fuse(L(-105, -65, -73, -65, 60, 184)).fuse(L(-65, -30, -73, -65, 88, 184))
        w = w.fuse(L(-175, -103, -86, -54, 72, 80)).fuse(L(-105, -103, -86, -73, 60, 80))
        w = w.cut(cyl(15, 8, (xc, yc, zp - 1)))                                     # kingpin rivet relief d30 (ESTIMATE)
        add(f"C02_castor_carriage_{tag}", w, "S355MC",
            "weldment: laser cut 6 mm carriage plate + tongue, 8 mm mast + shelf (S355MC), welded, zinc flake; 4 x M8 ISO 10642 into the castor holes; 8 x M3 to the MGN15H blocks; 2 spring spigots d23 x 5",
            explode=(0, 0, -120), notes=f"{'FR/RL mirror' if tag in ('FR', 'RL') else 'FL/RR'} variant; moves with the castor (-2.5..+17 mm)")
        add(f"C03_bump_pad_{tag}", L(-15, 15, -15, 15, zp + 6, zp + 9), "EPDM",
            "PU pad 30 x 30 x 3, 90 Shore A, bonded to the carriage plate (bump stop on the roof underside after 17 mm)",
            color=(0.85, 0.75, 0.2), explode=(0, 0, -100), mass=0.003)
        # C07 rail on the spine inner face, C08 2 blocks (channel around the rail)
        add(f"C07_rail_MGN15R_L190_{tag}", L(-97.5, -82.5, -59, -49, 40, 230), "purchased",
            "purchased HIWIN MGN15R rail L 190 (15 + 4 x 40 + 15), 5 x M3 x 10 into the 6 mm 6082 spine (6 mm engagement, Loctite 243)",
            category="purchased", color=(0.6, 0.6, 0.62), explode=(0, sy * 60, 0), mass=MGN15R["kg_m"] * MGN15R["L"] / 1000,
            src="HIWIN catalogue G99TE24-2410 Table 2-4-19 p.91 (SOURCED)")
        bl = None
        for z0 in (82.0, 147.0):
            b_ = L(-106, -74, -65, -53, z0, z0 + MGN15H["L"]).cut(L(-97.5, -82.5, -59, -48, z0 - 1, z0 + MGN15H["L"] + 1))
            bl = b_ if bl is None else bl.fuse(b_)
        add(f"C08_blocks_MGN15H_x2_{tag}", bl, "purchased",
            "purchased 2 x HIWIN MGN15H block (Z0 preload, standard seals), c/c 65 mm; carriage mast bolted 4 x M3 each",
            category="purchased", color=(0.55, 0.55, 0.6), explode=(0, sy * 60, -60), mass=2 * MGN15H["mass"],
            src="HIWIN G99TE24-2410 p.91: C 6.37 kN, C0 9.11 kN, MR 73.5 N.m (SOURCED)")
        # C04 springs (2 x D-313J-02, installed 51.2 mm), C05 spring bracket, C06 droop stop
        sp = None
        for u in (-158.0, -123.0):
            px_, py_ = lpt(sx, sy, u, -70)
            s_ = cyl(SPRING["De"] / 2, 131.2 - 80, (px_, py_, 80)).cut(cyl(SPRING["Di"] / 2, 60, (px_, py_, 75)))
            sp = s_ if sp is None else sp.fuse(s_)
        add(f"C04_springs_D-313J-02_x2_{tag}", sp, "purchased",
            "purchased 2 x Gutekunst D-313J-02 (d 3.6, De 31.6, L0 53.9, R 14.172 N/mm), installed 51.2 mm = 2 x 38 N; on d23 spigots",
            category="purchased", color=(0.75, 0.2, 0.15), explode=(0, 0, -40), mass=0.105,
            src="federnshop.com D-313J-02 datasheet (SOURCED); mass ESTIMATE")
        b1 = L(-175, -108, -86, -49, 131.2, 139.2).fuse(L(-175, -108, -55, -49, 139.2, 170))
        add(f"C05_spring_bracket_{tag}", b1, "S355MC",
            "laser cut + bent 8 mm S355MC; 4 x M6 in vertical slots +-3 mm to the spine (preload set per corner on a scale); 2 spigots d23 x 5 down",
            explode=(0, 0, 40))
        ds = L(-160, -140, -84, -49, 55.5, 59.5).fuse(L(-160, -140, -53, -49, 55.5, 70))
        bx_, by_ = lpt(sx, sy, -150, -70)
        ds = ds.fuse(cyl(10, 10, (bx_, by_, 59.5)))
        add(f"C06_droop_stop_{tag}", ds, "purchased",
            "rubber buffer d20 x 10 M6 (type A) on a 4 mm S355 angle bolted to the spine; shelf lands on it at -2.5 mm",
            category="purchased", color=(0.07, 0.07, 0.08), explode=(0, 0, -60), mass=0.06)
        own = tuple(f"{p}_{tag}" for p in ("C01_castor", "C02_castor_carriage", "C03_bump_pad", "C04_springs_D-313J-02_x2", "C08_blocks_MGN15H_x2"))
        own = (f"C01_castor_{tag}_Blickle_L-ALST_80K",) + own[1:]
        keepout(f"C01_swivel_{tag}", swivel_solid(sx, sy, PAN_Z0, CASTER_H + SUSP_TRAVEL[1]), own,
                "CASTOR_SUSPENSION.md s.4: swivel envelope of the L-ALST 80K (r_w(z) + fork r 50) swept over -2.5..+17 mm travel + 5 mm")
        keepout(f"C01_swivel_vs_carriage_{tag}", swivel_solid(sx, sy, 0.0, 98.0, margin=3.0, sweep=False), own[:1],
                "CASTOR_SUSPENSION.md s.4: carriage parts move with the castor -> only r_w(z) + 3 mm, no travel sweep")


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
    """centre bay x -78..78 between the packs, |y| <= 131 between the spine inner faces. Rev B4: the coaxial SWD bodies and their
    tunnels E43 fill the lower part (|y| 18..131, z <= 129), so the bay has ONE DIN rail per spine face at z 213 carrying the
    converters (vertical, input terminals down, Mean Well keep-out 130.4..315.6 below the deck doubler A09 at z 323) and FCF;
    the rev B3 HIGH-rail modules moved to the right side bay (E57, E55, E5A, E59 on the right MID rail; CAN1 on the right HIGH rail).
    Facing modules at the same x never sum to more than 247 mm depth (2 x 123.5).
    Cooling (rev B4 contents): E50L ~6.1 W + 3 x DRDN40-24 (E52 L/R, U3) ~8 W + FCF ~0.5 W = ~15 W. Air path unchanged: side-bay
    intake fans (E40_*in) -> side bays -> 2 x 40 mm fans E42 in the spine cut-outs at x = +140 -> front battery/spine gaps -> centre
    bay -> rear gaps -> rear exhaust fans E40_*out (heat-run TP-11). The SWD tunnels are a separate air path (tunnels())."""
    x0, x1, yb = CENTRE_BAY["x0"], CENTRE_BAY["x1"], CENTRE_BAY["y"]
    fL, fR = yb - 7.5, -(yb - 7.5)                       # rail front faces (left rail on the +y spine, right rail on the -y spine)
    ex = (0, 0, 520)
    for sy, f in ((1, fL), (-1, fR)):
        s_ = 'L' if sy > 0 else 'R'
        rail(f"E0C_{s_}_din_rail", x0 + 1, x1 - 1, Z_CRAIL, sy * yb, f, explode=ex)
    din("E50_dcdc_arm_L_DDR480C24", -73.0, DDR480, Z_CRAIL, fL, -1, conv=True, mass=1.375, explode=ex,
        process="purchased Mean Well DDR-480C-24 (arm L 24 V bus, OpenArm variant), vertical, input terminals down", src="meanwell.com (SOURCED)")
    din("E52_arm_ORing_L_DRDN40-24", 17.5, DRDN40, Z_CRAIL, fL, -1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DRDN40-24 (arm L bus ORing), vertical")
    din("E52_arm_ORing_R_DRDN40-24", -73.0, DRDN40, Z_CRAIL, fR, 1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DRDN40-24 (arm R bus ORing), vertical")
    din("E30_U3_ORing_DRDN40-24", -13.0, DRDN40, Z_CRAIL, fR, 1, conv=True, mass=0.3, explode=ex,
        process="purchased Mean Well DRDN40-24 (T24 ORing of U1/U2), vertical, input terminals down")
    din("E56_FCF_fuse", 47.0, (17.5, 82, 70), Z_CRAIL, fR, 1, mass=0.1, explode=ex,
        notes="Mersen HP10M15 gPV in a 10x38 DC holder (rev B4, G-13)")
    # rev B3: DSR 50/5 clamps (94 x 41 x 35, plate mount, any orientation) moved out of the spine/battery gaps (now the castor
    # spring columns) onto the deck underside above the packs: z 303..338 (pack top 300), between the straps (x 135..215)
    w, h, d = DSR50
    for nm, xa, ya in (("E5B_arm_clamp_L_DSR50-5", 150.0, 2.0), ("E5B_arm_clamp_R_DSR50-5", 150.0, -96.0),
                       ("E16_R1a_traction_clamp_DSR50-5", -205.0, 2.0), ("E16_R1b_traction_clamp_DSR50-5", -205.0, -96.0)):   # rev B4: x -205..-164 (doubler A09 from -160)
        add(nm, box(xa, xa + h, ya, ya + w, DECK_Z0 - d, DECK_Z0), "purchased",
            "purchased maxon DSR 50/5 (309687) 27 V on its plate, M4 to the deck underside above the pack (outside the slide path z <= 300)",
            category="purchased", color=(0.25, 0.25, 0.28), explode=(0, 0, 300), mass=0.25, src="maxongroup.com 309687 (SOURCED 94 x 41 x 35 mm)")
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
        cx, cy = sx * SCAN_XY[0], sy * SCAN_XY[1]                                # unchanged since rev B (seat on the tower roof)
        z0 = TOWER_ROOF[1]
        s = place(box(-NS3["D"] / 2, NS3["D"] / 2, -NS3["W"] / 2, NS3["W"] / 2, 0, NS3["H"]), G.rotz(head), (cx, cy, z0))
        add(f"S01_nanoScan3_ProIO_{k}", s, "purchased", "purchased SICK nanoScan3 Pro I/O NANS3-CAAZ30AN1 (PL d, 128 field sets; no encoder inputs per datasheet)",
            category="purchased", color=(0.95, 0.8, 0.1), explode=(sx * 160, sy * 160, 0), mass=NS3["mass"], src="sick.com (SOURCED)")
    # dock collector: rev B2 rear face, off-centre at y = PAD_Y (out of the rear top-cover keep-out |y| <= 90)
    s = box(X0 + 2, X0 + 2 + ROBOPAD["D"], PAD_Y - ROBOPAD["W"] / 2, PAD_Y + ROBOPAD["W"] / 2, PAD_Z - ROBOPAD["H"] / 2, PAD_Z + ROBOPAD["H"] / 2)
    add("E01_robopad_collector_RPCOL90", s, "purchased", "purchased Roboteq RoboPad collector RPCOL90-100 (60 A cont., Hall docked sensor)",
        category="purchased", color=(0.85, 0.45, 0.1), explode=(-200, 0, 0), mass=ROBOPAD["mass"], src="Roboteq datasheet v1.3 (SOURCED)")
    # E-stops (both sides), service disconnect key (rear right), status LED band
    for sy in (-1, 1):                                    # rev B3: x 0 -> 60 (the right side cover inner face above the SWD carries the LYNK II)
        es = cyl(20, 38, (ESTOP_X, sy * (Y1 + 36), 268), (0, -sy, 0))
        es = es.fuse(box(ESTOP_X - 15, ESTOP_X + 15, sy * (Y1 - COVER_T), sy * (Y1 - COVER_T - 40), 248, 288))   # holder + 2 contact modules behind the cover (ESTIMATE)
        add(f"E02_estop_{'L' if sy > 0 else 'R'}", es, "purchased",
            "purchased Siemens 3SU1 E-stop + holder + 2x 3SU1400-1AA10-1CA0 NC (positive opening) + yellow enclosure plate; contact block envelope 30 x 40 x 40 behind the cover",
            category="purchased", color=(0.85, 0.1, 0.1), explode=(0, sy * 120, 0), mass=0.12)
    add("E03_service_disconnect_ED250B", box(-340, -270, -210, -140, 145, 235), "purchased",
        "purchased Albright ED250B-L (with blowouts, 58 V) key-lockable service disconnect, key extension through the rear cover", category="purchased",
        color=(0.85, 0.1, 0.1), explode=(0, 160, 0), mass=0.6, src="albrightinternational.com (SOURCED)")


SIDE_EX = 260
ESTOP_X = 60.0


def din_bays():
    """Side DIN bays on the spine OUTER faces, rev B3 (CAD_REV_B3.md s.3 = electrical/din_layout.md rev B3, one table):
    left (+y) = power, right (-y) = safety/control. Rules: every DDR/DRDN vertical with its Mean Well keep-out (40 above, 20
    below, 5 left/right; true heights 125.2 mm for DDR-120/240/480 and DRDN40); converters only where 185.2 mm of free height
    exists: LOW rails z 120 (|x| 100..190.6 between the SWD housing and the castor swivel keep-out), the left MID rail above the
    SWD (DDR-60 only, 150 mm), and the FL / RR corners above the tower roofs (no scanner there). Everything else on the HIGH rails
    (z 275, modules z >= 224) or the left MID rail."""
    fL, fR = SPINE_Y + 7.5, -(SPINE_Y + 7.5)
    exL, exR = (0, SIDE_EX, 0), (0, -SIDE_EX, 0)
    yL, yR = SPINE_Y, -SPINE_Y
    # ---------------- rails
    rail("E0L_din_rail_lower_F", 100, 195, Z_RAIL_LO, yL, fL, exL)
    rail("E0L_din_rail_lower_R", -195, -100, Z_RAIL_LO, yL, fL, exL)
    rail("E0L_din_rail_mid", -95, 95, Z_RAIL_MID, yL, fL, exL)
    rail("E0L_din_rail_upper_F", 100, 195, Z_RAIL_HI, yL, fL, exL)
    rail("E0L_din_rail_upper_R", -298, -97, Z_RAIL_HI, yL, fL, exL, notes="DIN rail TS35x7.5, M5 to the spine + bracket A08")
    rail("E0L_din_rail_corner_FL", 202, 298, Z_RAIL_CNR_FL, yL, fL, (60, SIDE_EX, 0), notes="DIN rail TS35x7.5, M5 to the spine end + A06")
    rail("E0R_din_rail_lower_F", 100, 195, Z_RAIL_LO, yR, fR, exR)
    rail("E0R_din_rail_lower_R", -193, -98, Z_RAIL_LO, yR, fR, exR)
    rail("E0R_din_rail_upper", -202, 298, Z_RAIL_HI, yR, fR, exR, notes="DIN rail TS35x7.5, M5 to the spine + bracket A10 (rev B4: to x 298)")
    rail("E0R_din_rail_mid_F", 33, 71, Z_RAIL_RMID, yR, fR, exR, notes="DIN rail TS35x7.5, M5 to the spine (rev B4: above the drive tunnel)")
    rail("E0R_din_rail_mid_R", -96, -31, Z_RAIL_RMID, yR, fR, exR, notes="DIN rail TS35x7.5, M5 to the spine (rev B4: above the drive tunnel)")
    rail("E0R_din_rail_net", 73, 97, Z_RAIL_RNET, yR, fR, exR, notes="DIN rail TS35x7.5, M5 to the spine (rev B4: NET1)")
    rail("E0R_din_rail_corner_RR", -265, -203, Z_RAIL_CNR_RR, yR, fR, (-60, -SIDE_EX, 0), notes="DIN rail TS35x7.5, M5 to the spine end + A07")
    # ---------------- LEFT (power)
    din("E13_U1_dcdc_DDR480C24", 105.0, DDR480, Z_RAIL_LO, fL, 1, conv=True, mass=1.375, explode=exL)
    din("E14_U2_dcdc_DDR480C24", -190.5, DDR480, Z_RAIL_LO, fL, 1, conv=True, mass=1.375, explode=exL)
    din("E12_K0P_precharge_relay", -94.0, (17.5, 90, 70), Z_RAIL_MID, fL, 1, mass=0.1, explode=exL,
        notes="Finder 22.32 + Arcol HS50 47R on the spine below the rail")
    din("E11_K0_contactor_SW80B_on_plate", -74.5, (70, 110, 95), Z_RAIL_MID, fL, 1, mass=0.9, explode=exL,
        notes="D0 freewheel diode on the coil spades")
    din("E10_F0_fuse_NH00_100A", -2.5, (40, 125, 90), Z_RAIL_MID, fL, 1, mass=0.4, explode=exL,
        notes="central: H01 = H02 in length (805-0027 s.9.7)")
    din("E58_U6_DDR60L5", 42.5, DDR60, Z_RAIL_MID, fL, 1, conv=True, mass=0.3, explode=exL,
        process="purchased Mean Well DDR-60L-5 (head 5 V), vertical, input terminals down", src="DDR-60 spec (SOURCED 52.5 x 90 x 54.5)",
        notes="rev B3: from the centre bay; keep-out 180..330 = SWD housing top .. 8 mm under the deck")
    for name, xs, dims, m in (("E31_F8LR_SWD_fuses", 101.0, (35, 82, 70), 0.1), ("E32_T24_terminals", 138.0, (24, 60, 50), 0.1),
                              ("E19_0V_block", 164.0, (27, 60, 50), 0.1),
                              ("E2F_WF1-3_AUX48_fuses", -296.0, (52.5, 82, 70), 0.15), ("E18_branch_fuses_10x38_x6", -241.5, (110, 82, 70), 0.3),
                              ("E17_K0T_timer_Finder80", -129.5, (17.5, 90, 70), 0.1)):
        din(name, xs, dims, Z_RAIL_HI, fL, 1, mass=m, explode=exL,
            notes="rev B3: on the left upper rail next to F2/E18 (din_layout.md s.0 item 2)" if name.startswith("E2F") else "")
    din("E54_U7_DDR480C24_coffee", 205.0, DDR480, Z_RAIL_CNR_FL, fL, 1, conv=True, mass=1.375, explode=(60, SIDE_EX, 0),
        notes="front-left corner above the castor tower (no scanner here); keep-out below = tower roof top z 134")
    # ---------------- RIGHT (safety / control)
    din("E2G_U5_DDR120C12", -190.0, DDR120, Z_RAIL_LO, fR, -1, conv=True, mass=0.5, explode=exR,
        notes="rev B3: right LOW rear (x >= -190.6 = RR swivel keep-out at the module bottom z 57.4)")
    din("E15_U4_dcdc_DDR240C24_S24", -153.0, DDR240, Z_RAIL_LO, fR, -1, conv=True, mass=0.6, explode=exR)
    din("E37_KS_signature_relay", -106.0, (6.2, 90, 70), Z_RAIL_LO, fR, -1, mass=0.04, explode=exR)
    din("E50_dcdc_arm_R_DDR480C24", 105.0, DDR480, Z_RAIL_LO, fR, -1, conv=True, mass=1.375, explode=exR,
        process="purchased Mean Well DDR-480C-24 (arm R 24 V bus, OpenArm variant), vertical, input terminals down",
        notes="moved out of the centre bay (only one DDR-480 fits there under the Mean Well rule)")
    din("E34_U8_ideal_diode_DRDN40-48", -262.0, DRDN40, Z_RAIL_CNR_RR, fR, -1, conv=True, mass=0.3, explode=(-60, -SIDE_EX, 0),
        notes="rev B3: rear-right corner above the tower roof (was inside the RR swivel keep-out); H06a from E01 < 0.5 m")
    PZ = (22.5, 101.4, 120)
    # rev B4: NET1 at its documented size, SR3 (SLS[2] 0.7 m/s band, INSafe_3/4) added, CAN1 (real size 22.5 x 99 x 114.5) at the rail end
    # on the A10 extension; x 45..75 (E-stop contact block behind the cover, y <= -236) only modules <= 91.5 mm deep.
    up = [("E2C_K1_contactor_3RT2026", -200.0, (45, 85, 107)), ("E2D_K2_contactor_3RT2026", -153.0, (45, 85, 107)),
          ("E2L_FJ_fuse_Jetson12V", -106.0, (17.5, 82, 70)), ("E33_F7_charge_fuse", -86.5, (17.5, 82, 70)),
          ("E35_RSIG_X0R", -67.0, (22, 60, 50)), ("E27_XS24_terminals_RB1-7", -43.0, (80, 60, 50))]
    xs_ = 39.0
    for name, dims in (("E2J_KI4_interposing_relay", (6.2, 90, 80)), ("E55_K4_Finder22", (17.5, 90, 70)),
                       ("E2K_K0V_LVCO_relay_DUB01CD48500V", (22.5, 80, 99.5)), ("E20_SC1_PNOZ_m_ES_ETH", PZ), ("E21_SC0_PNOZ_m_B0", (45, 101.4, 120)),
                       ("E2H_SR1_PNOZ_m_EF_4DI4DOR", PZ), ("E2I_SR2_PNOZ_m_EF_4DI4DOR", PZ), ("E2M_SR3_PNOZ_m_EF_4DI4DOR", PZ)):
        if name.startswith("E2K") and xs_ < 76.0:
            xs_ = 76.0                                    # K0V (99.5 deep) right of the E-stop contact block (x 45..75)
        up.append((name, xs_, dims))
        xs_ += dims[0] + (0.0 if "PNOZ" in name else 2.0)
    SX2_SLOT = (xs_, xs_ + 22.5)                          # E28 SX2 PNOZ m EF 8DI4DO (C48 variant only) - kept free
    up.append(("E36_CAN1_PCAN-Ethernet_gw", SX2_SLOT[1] + 2.0, PCAN_GW))
    for name, xs, dims in up:
        col = (0.95, 0.8, 0.1) if "PNOZ" in name else None
        din(name, xs, dims, Z_RAIL_HI, fR, -1, color=col, explode=exR,
            mass={"E21": 0.235, "E2C": 0.4, "E2D": 0.4, "E25": 0.3, "E2K": 0.15, "E36": 0.25}.get(name[:3], 0.2 if "PNOZ" in name else 0.15),
            notes={"E2H": "SR1: SWD STO_1/2 + INSafe_1/2 relay contacts", "E2I": "SR2: scanner CI1-CI4 relay contacts",
                   "E2M": "rev B4 SR3: SWD INSafe_3/4 = SLS[2] 0.7 m/s band", "E36": "PEAK IPEH-004010, 22.5 x 99 x 114.5 mm (user manual 2.1.0 p.65)",
                   "E2K": "Carlo Gavazzi DUB01CD48500V, 22.5 x 80 x 99.5 mm (SOURCED datasheet 2025-03-03)",
                   "E2J": "Phoenix PLC-RSC-24DC/21 6.2 mm: K4 coil 92 mA > 75 mA PNOZ auxiliary output"}.get(name[:3], ""))
    # rev B4: right MID rail (z 175) above the drive tunnel, |x| 33..95 (E44R tunnel fan in |x| <= 30): the rev B3 centre HIGH-rail modules
    din("E25_NET1_switch_FL1008N", 73.5, NET1_DIMS, Z_RAIL_RNET, fR, -1, mass=0.3, explode=exR,
        notes="Phoenix FL SWITCH 1008N 1085256, 22.5 x 140.4 x 92.4 mm (datasheet); rev B4: own rail z 164 (too tall for the HIGH rail)")
    for name, xs, dims in (("E57_FAL_FAR_fuses", 35.0, (35, 82, 70)),
                           ("E5A_XC_deck_terminals", -61.0, (30, 60, 50)), ("E59_JR1_relays", -96.5, JR1_DIMS)):
        din(name, xs, dims, Z_RAIL_RMID, fR, -1, mass=0.15, explode=exR,
            notes="rev B4: moved from the centre HIGH rail (the coaxial SWD bodies + tunnels fill the centre bay below z 129)")
    # LYNK II gateway (sell sheet 885-0035: 120 x 135 x 44 mm), on a bracket hung from the deck, against the right side cover,
    # above the SWD (x -92.5..42.5, z 214..334): the HIGH-rail modules in front of it are <= 85.5 mm deep (terminals, fuses, KI4)
    add("E38b_LYNK_bracket", box(-95, 45, -232, -230, 213, DECK_Z0).fuse(box(-95, 45, -276, -230, DECK_Z0 - 2, DECK_Z0)),
        "EN AW-5754-H22", "laser cut + bent 2 mm 5754, M4 x4 to the deck underside, 4 x M4 for the gateway", explode=(0, -SIDE_EX - 60, 0))
    add("E38_G01_LYNK_II_gateway", box(-92.5, 42.5, -276, -232, 214, 334), "purchased",
        "purchased Discover LYNK II Communication Gateway 950-0025, 120 x 135 x 44 mm (sell sheet 885-0035 p.2), on bracket E38b",
        category="purchased", color=(0.15, 0.15, 0.17), explode=(0, -SIDE_EX - 80, 0), mass=0.4, src="Discover 885-0035 (SOURCED size; mass ESTIMATE)")
    # bay fans: 60 mm IP54 + filter. Intake: side covers at the middle (above the wheel arch, clear of the low converters);
    # exhaust: rear cover at y +-152, z 235..295 (clear of the rear top-cover keep-out |y| <= 90 and the RL post)
    for sy in (1, -1):
        add(f"E40_fan_{'L' if sy > 0 else 'R'}in", box(-30, 30, sy * (Y1 - 27), sy * (Y1 - 2), 150, 210), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, intake (side cover, above the wheel arch)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(0, sy * 200, 0), mass=0.12)
        add(f"E40_fan_{'L' if sy > 0 else 'R'}out", box(X0 + 2, X0 + 27, sy * FAN_OUT_Y - 30, sy * FAN_OUT_Y + 30, 235, 295), "purchased",
            "purchased 60x60x25 mm 24 V IP54 fan + filter grille, exhaust high (rear cover)", category="purchased",
            color=(0.1, 0.1, 0.11), explode=(-200, 0, 0), mass=0.12)
    # rear panel above the rear pack: reset SB1, key selector SK1, M12 enabling-pendant socket SE1
    for k, (yy, nm) in enumerate(((-50, "SB1_reset_blue"), (0, "SK1_key_selector"), (50, "SE1_M12_pendant_socket"))):
        add(f"E41_{nm}", cyl(15, 40, (X0 + 1, yy, E41_Z), (1, 0, 0)), "purchased", "purchased Siemens 3SU1 / M12 panel device", category="purchased",
            color=(0.15, 0.3, 0.8) if k == 0 else (0.2, 0.2, 0.22), explode=(-180, 0, 0), mass=0.05)


FAN_OUT_Y = 152.0
E41_Z = 318.0


COVER_TRIM_Z = 70.0                                       # local notch z 62..70 (8 mm), ~50 mm long, at the 4 chamfers: minimum that clears the 5 mm swivel margin (CAD_REV_B3.md s.1)


def covers():
    zc0, zc1 = PAN_Z0 + 30, DECK_Z0 - 1
    outer = poly(outline(0.0), zc1 - zc0, zc0)
    inner = poly(outline(COVER_T), zc1 - zc0 + 2, zc0 - 1)
    shell = outer.cut(inner)
    # wheel arches, scanner windows (270 deg field at the 2 corners), dock window, e-stop holes
    for sy in (-1, 1):
        shell = shell.cut(box(-WHEEL_D / 2 - 12, WHEEL_D / 2 + 12, sy * (Y1 - 10), sy * (Y1 + 10), zc0 - 1, TUNNEL["z_top"] + 2))   # rev B4: arch top 131 (wheel 125, tunnel roof 129)
        shell = shell.cut(cyl(21, 20, (ESTOP_X, sy * (Y1 - 10), 268), (0, sy, 0)))
    # continuous scan slot all round (40 mm, centred on the scan plane): each corner scanner sees its 270 deg
    shell = shell.cut(box(-500, 500, -400, 400, SCAN_Z - 20, SCAN_Z + 20))
    for (sx, sy, head) in SCAN_CORNERS:                  # local notch: scanner housing (134..214) passes the upper band
        cx, cy = sx * SCAN_XY[0], sy * SCAN_XY[1]
        shell = shell.cut(cyl(80, 100, (cx, cy, TOWER_ROOF[0] - 6)))
    shell = shell.cut(box(X0 - 5, X0 + 10, PAD_Y - ROBOPAD["W"] / 2 - 6, PAD_Y + ROBOPAD["W"] / 2 + 6, PAD_Z - ROBOPAD["H"] / 2 - 6, PAD_Z + ROBOPAD["H"] / 2 + 6))
    for yy in (-50, 0, 50):
        shell = shell.cut(cyl(16, 20, (X0 - 5, yy, E41_Z), (1, 0, 0)))
    for sy in (1, -1):
        shell = shell.cut(box(-25, 25, sy * (Y1 + 5), sy * (Y1 - 10), 155, 205))                   # side intake fans
        shell = shell.cut(box(X0 - 5, X0 + 10, sy * FAN_OUT_Y - 25, sy * FAN_OUT_Y + 25, 240, 290))   # rear exhaust fans
    shell = shell.cut(cyl(12, 20, (X0 - 5, -175, 190), (1, 0, 0)))          # ED250B key
    for sx, sy, _ in CORNERS:                            # rev B3: bottom-edge trim at the chamfers: the swept swivel keep-out (r 84.1 at z 62)
        shell = shell.cut(cyl(PAN_CUT_R, COVER_TRIM_Z - zc0 + 1, (sx * CASTER_XY[0], sy * CASTER_XY[1], zc0 - 1)))   # reaches 1.5 mm past the inner chamfer face
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
    H.append(("H01_batt_F_to_fuse", [(345, 60, 285), (330, 100, 285), (262, 110, 250), (230, 134, 237), (120, 200, 300), (17, 200, 305)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H02_batt_R_to_fuse", [(-345, 60, 285), (-330, 100, 285), (-262, 110, 250), (-230, 134, 237), (-120, 200, 300), (17, 200, 305)], 7.0, (0.8, 0.1, 0.1)))
    H.append(("H03_bus48_to_centre_and_deck", [(-160, 200, 320), (-140, 160, 237), (-140, 110, 237), (-70, 100, 326), (62, 30, 326), (62, 20, 355)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H04_traction_24V_L", [(105, 200, 200), (60, 190, 190), (0, 175, 185)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H05_traction_24V_R", [(-100, 200, 200), (-140, 175, 237), (-140, 110, 237), (-120, 60, 320), (-120, -60, 320),
                                     (-140, -110, 237), (-140, -175, 237), (0, -175, 185)], 5.0, (0.9, 0.5, 0.1)))
    H.append(("H06_dock_to_charge_path", [(-346, PAD_Y, PAD_Z), (-310, -140, 150), (-275, -150, 150), (-235, -170, 140)], 6.0, (0.8, 0.1, 0.1)))
    H.append(("H07_safety_bus_scanner_F", [(-150, -200, 330), (250, -200, 330), (300, -205, 220)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H08_safety_bus_scanner_R", [(-150, -200, 330), (-250, -150, 330), (-300, 150, 320), (-310, 195, 225)], 3.5, (0.95, 0.8, 0.1)))
    H.append(("H09_safety_estops", [(-100, -200, 330), (ESTOP_X, -235, 300), (ESTOP_X, -238, 268)], 3.0, (0.95, 0.8, 0.1)))
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
    L_, W_, H_ = NPB750
    add("X04_charger_NPB750_48", box(xd - 250, xd - 250 + W_, -240, -240 + L_, 180, 180 + H_), "purchased",
        "purchased Mean Well NPB-750-48 (11.3 A CC, EMC Class B, CANBus, IEC 60335-2-29, DIP preset 'flooded' 56.8/53.6 V), 230 x 158 x 67 mm, lying",
        group="dock", category="purchased", color=(0.7, 0.7, 0.72), explode=(-300, 0, 120), mass=1.84,
        src="Mean Well NPB-750-SPEC (SOURCED 230*158*67 mm; mass = packing weight 1.84 kg)")
    add("X05_dock_controller_relay", box(xd - 255, xd - 175, 50, 150, 220, 330), "purchased",
        "purchased DIN box: dock controller (Finder OPTA class PLC, Ethernet/Wi-Fi) + DC contactor Albright SW80B (blowouts, 96 V, breaks 600 A) + freewheel diode; pads OFF unless Hall + signature + handshake",
        group="dock", category="purchased", color=(0.25, 0.25, 0.28), explode=(-300, 0, 120), mass=1.4)
    add("X09_dock_OV_relay_DUB01", box(xd - 170, xd - 147.5, 60, 140, 230, 329.5), "purchased",
        "purchased Carlo Gavazzi DUB01CD48500V (22.5 x 80 x 99.5 mm), 20-200 V range, over-voltage, normally energised, bench-set 58.5 V: its NO contact in the dock contactor coil opens > 58.5 V (VERIFICATION M12, RoboPad <= 60 V under fault)",
        group="dock", category="purchased", color=(0.25, 0.25, 0.28), explode=(-300, 0, 120), mass=0.15, src="Carlo Gavazzi DUB01 datasheet 2025-03-03 (SOURCED, docs/fonti)")
    add("X06_apriltag_reflector_plate", box(xd - 262, xd - 258, -120, 120, 380, 500), "purchased",
        "AprilTag 36h11 + retro-reflective strip (lidar profile), on the robot centre line (z 380..500: out of the scan plane)", group="dock", category="purchased",
        color=(0.95, 0.95, 0.95), explode=(-320, 0, 0), mass=0.2)
    add("X07_dock_cover", box(xd - 260, xd - 30, -255, 255, 175, 370).cut(box(xd - 257, xd - 33, -252, 252, 172, 367)),
        "EN AW-5754-H22", "bent 2 mm, powder coat, vent slots", group="dock", explode=(-260, 0, 200), color=(0.92, 0.92, 0.9))


def build():
    chassis(); drives(); tunnels(); casters(); batteries(); centre_bay(); sensors_and_io(); din_bays(); covers(); harness(); dock()
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
            kos.append(dict(name=n, owner=list(p["owner"]), rule=p["src"], file=f"{n}.stl",
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
            if b in parts[k]["owner"]:
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


def travel_check(parts):
    """castor carriage swept over its travel (CASTOR_SUSPENSION.md s.3.4): the moving parts of each corner (castor, carriage,
    bump pad, blocks) translated to the droop (-2.5) and bump (+17) positions must not overlap any fixed robot solid or any
    keep-out other than their own swivel keep-outs. Contacts at the end stops are faces (pad/roof at +17, shelf/buffer at -2.5)."""
    res = []
    for _, _, tag in CORNERS:
        mov = [n for n in parts if n.endswith(tag) or f"_{tag}_" in n]
        mov = [n for n in mov if n.split("_")[0] in ("C01", "C02", "C03", "C08")]
        fixed = [n for n, p in parts.items() if p["category"] != "harness" and p["group"] != "dock" and n not in mov
                 and not n.startswith("C04") and not (p["category"] == "keepout" and n.startswith("KO_C01_swivel") and n.endswith(tag))]
        for dz in SUSP_TRAVEL:
            for n in mov:
                sh = parts[n]["shape"].translate(cq.Vector(0, 0, dz))
                bb = sh.BoundingBox()
                for f in fixed:
                    if _bb_apart(bb, parts[f]["shape"].BoundingBox()):
                        continue
                    v = _common(sh, parts[f]["shape"])
                    if v > 5.0:
                        res.append((tag, dz, n, f, round(v)))
    return res


if __name__ == "__main__":
    import time
    t = time.time()
    P = build()
    meta = export(P)
    bad, ko_bad, dock_bad, nko = interference(P)
    sp = slide_paths(P)
    tr = travel_check(P)
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
    print("CASTOR TRAVEL (-2.5 / +17 mm) OVERLAPS:", len(tr))
    for b in tr:
        print("  ", b)
    json.dump(dict(interferences=bad, keepout_violations=ko_bad, keepout_pairs_checked=nko, dock_interferences=dock_bad,
                   battery_slide_path_obstacles=sp, castor_travel_overlaps=tr), open(OUT / "interference.json", "w"), indent=1)
