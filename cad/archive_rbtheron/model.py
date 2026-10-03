"""Giorgio parametric mechanical model (CadQuery). Builds every custom part, the purchased-part envelopes and
every bolted joint, all in the robot base frame at column lift = 0 (see geom.py / params.py).

    parts, bolts = build()        # dict name -> Part, list of fasteners.Bolt

Commenti di progetto in italiano dove servono; nomi dei pezzi in inglese (BOM).
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import numpy as np
from shapely.geometry import Polygon

import fasteners as F
import geom as G
from geom import Hole, Part, box, cyl, V
from params import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OA_STL = ROOT / "third_party/openarm_mujoco/v2/assets/visual/body/body_link0.stl"

PARTS: dict = {}
BOLTS: list = []


def add(p: Part):
    assert p.name not in PARTS, p.name
    PARTS[p.name] = p
    return p


def drill(part: Part, h: Hole):
    part.add_hole(h)
    part.shape = G.cut_hole(part.shape, h)
    return h


def bolt(name, thread, L, stack, female="tap", std="ISO 4762", grade="8.8", washer=True, nut_spec="", group="", assumed="", preload_frac=0.6):
    b = F.Bolt(name=name, thread=thread, L=L, std=std, grade=grade, washer=washer, stack=stack, female=female,
               nut_spec=nut_spec, group=group, assumed=assumed, preload_frac=preload_frac)
    BOLTS.append(b)
    return b


DOWN, UP = (0, 0, -1), (0, 0, 1)


def poly_plate(poly: Polygon, z0, t):
    pts = list(poly.exterior.coords)[:-1]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(t).val()


def oct_poly(inset=0.0):
    return Polygon(TR_OCT).buffer(-inset, join_style=2)


# ====================================================================== purchased: Robotnik RB-THERON
def base_envelope():
    cx = (BS_X0 + BS_X1) / 2
    body = G.rounded_rect(cx, 0, BS_L, BS_W, BS_H - BS_GC, BS_GC, 30)
    for sy in (-1, 1):
        x, y, r = BS_WHEELS[0]
        body = body.fuse(cyl(r, 25, (x, sy * y - 12.5, r), (0, 1, 0)))
        for sx in (-1, 1):
            xc, yc, rc = BS_CASTERS[0]
            body = body.fuse(cyl(rc, 25, (sx * xc, sy * yc - 12.5, rc), (0, 1, 0)))
    body = body.fuse(box(BS_X1, BS_ESTOP_X1, -25, 25, 250, 300))                    # pulsante E-stop anteriore (EST)
    xc_, wc, z0c, z1c = BS_CONTACT
    body = body.fuse(box(xc_ - 3, xc_, -wc / 2, wc / 2, z0c, z1c))                  # contatti di ricarica frontali (EST)
    p = add(Part(BASE_PART, body, "purchased", "purchased (Robotnik RB-THERON, differential drive, safety pack)", category="purchased",
                 color=(0.15, 0.16, 0.18), explode=(0, 0, -250), mass_kg=BS_MASS, mass_src="Robotnik datasheet 70 kg (SOURCED)",
                 notes="envelope from the datasheet drawing + robotnik_description mesh bbox; top holes ASSUMED"))
    p.com_override = np.array([0.0, 0.0, BS_COG_Z])
    p.tap_material = "manufacturer thread (datasheet max insertion)"
    return p


# ====================================================================== base adapter plate (on the RB-THERON top, hole pattern ASSUMED)
ADAPTER_KEEP = []          # (x0, x1, y0, y1) zone portanti da non alleggerire


def adapter_plate():
    s = G.rounded_rect((BS_X0 + BS_X1) / 2 - 2, 0, BS_L - 12, BS_W - 8, AD_T, AD_Z0, 25)
    p = add(Part("P01_base_adapter_plate", s, "EN AW-6082-T6", "waterjet 8 mm + CNC drill/tap (M5/M6), 90 deg countersinks; grid lightening",
                 color=(0.70, 0.71, 0.73), explode=(0, 0, -120),
                 notes="bolts on the RB-THERON top plate: 8 countersunk M6 on an ASSUMED grid (drill to suit; Robotnik STEP requested)"))
    base = PARTS[BASE_PART]
    for k, (x, y) in enumerate(BS_HOLES):
        hn = f"bs{k}"
        drill(p, Hole(hn, (x, y, AD_Z1), DOWN, 6.6, AD_T, "clear", "M6"))
        p.shape = p.shape.cut(cq.Solid.makeCone(6.72, 3.3, 3.42, V(x, y, AD_Z1 - 3.42), V(0, 0, 1)))
        p.shape = p.shape.cut(cyl(6.72, 1, (x, y, AD_Z1 - 0.01)))
        drill(base, Hole(hn, (x, y, BS_H), DOWN, F.ISO["M6"]["tap"], BS_HOLE_DEPTH, "tap", "M6"))
        bolt(f"B_base_{k}", "M6", 20, [(p.name, hn), (BASE_PART, hn)], std="ISO 10642", washer=False, group="G1 adapter->RB-THERON top",
             assumed="RB-THERON top-plate holes: positions/thread/depth ASSUMED (not dimensioned in the datasheet)")
        ADAPTER_KEEP.append((x - 14, x + 14, y - 14, y + 14))
    return p


def lighten_adapter():
    """griglia di finestre 70 x 70 dove non ci sono fori o appoggi (bordo 22 mm, nervature 14 mm)"""
    p = PARTS["P01_base_adapter_plate"]
    holes = [np.array(h.p[:2]) for h in p.holes.values()]
    cell, web, border = 52.0, 12.0, 20.0
    xs = np.arange(BS_X0 + 6 + border, BS_X1 - 6 - border - cell + 1e-6, cell + web)
    ys = np.arange(-BS_W / 2 + border, BS_W / 2 - border - cell + 1e-6, cell + web)
    n = 0
    for x0 in xs:
        for y0 in ys:
            x1, y1 = x0 + cell, y0 + cell
            if any(x0 - 10 < hp[0] < x1 + 10 and y0 - 10 < hp[1] < y1 + 10 for hp in holes):
                continue
            if any(not (x1 < k[0] or x0 > k[1] or y1 < k[2] or y0 > k[3]) for k in ADAPTER_KEEP):
                continue
            p.shape = p.shape.cut(G.rounded_rect((x0 + x1) / 2, (y0 + y1) / 2, cell, cell, AD_T + 2, AD_Z0 - 1, 12))
            n += 1
    return n


def tap_adapter(name, x, y, thread, depth=AD_T):
    p = PARTS["P01_base_adapter_plate"]
    return drill(p, Hole(name, (x, y, AD_Z1), DOWN, F.ISO[thread]["tap"], depth, "tap", thread))


# ====================================================================== column: fixed height (Ranger Air), foot + profile + bracket
FOOT_T = 20.0


def column():
    zf0, zf1 = AD_Z1, AD_Z1 + FOOT_T
    s = G.rounded_rect(COL_X, 0, 160, 160, FOOT_T, zf0, 10)
    s = s.cut(box(COL_X - PROF / 2 - 0.2, COL_X + PROF / 2 + 0.2, -PROF / 2 - 0.2, PROF / 2 + 0.2, zf1 - 5, zf1 + 1))     # tasca spigot
    ft = add(Part("P29_column_foot", s, "EN AW-6082-T6", "CNC 20 mm: 80x80 spigot pocket, M12 cbore from below, 8x M6 cbores",
                  color=(0.72, 0.73, 0.75), explode=(0, 0, 60)))
    ADAPTER_KEEP.append((COL_X - 80, COL_X + 80, -80, 80))
    for k, (bx, by) in enumerate([(COL_X + sx * 62, sy * 62) for sx in (-1, 0, 1) for sy in (-1, 0, 1) if (sx, sy) != (0, 0)]):
        hn = f"f{k}"
        drill(ft, Hole(hn, (bx, by, zf0 + 8), DOWN, 6.6, 8, "clear", "M6", cbore=None))
        ft.shape = ft.shape.cut(cyl(5.75, FOOT_T, (bx, by, zf0 + 8)))                  # lamatura D11.5 per la testa
        tap_adapter(f"col{k}", bx, by, "M6")
        bolt(f"B_colfoot_{k}", "M6", 16, [(ft.name, hn), ("P01_base_adapter_plate", f"col{k}")], washer=False, group="G2 column foot->adapter")
    prof_bot = zf1 - 5
    L = PROF_TOP - prof_bot
    prof = box(COL_X - PROF / 2, COL_X + PROF / 2, -PROF / 2, PROF / 2, prof_bot, PROF_TOP)
    for (sx, sy, along) in ((1, 0, "y"), (-1, 0, "y"), (0, 1, "x"), (0, -1, "x")):
        for off in (-20.0, 20.0):
            if along == "y":
                cx, cy = COL_X + sx * (PROF / 2 - 6), off
                prof = prof.cut(box(cx - 6.5, cx + 6.5, cy - 4, cy + 4, prof_bot - 1, PROF_TOP + 1))
            else:
                cx, cy = COL_X + off, sy * (PROF / 2 - 6)
                prof = prof.cut(box(cx - 4, cx + 4, cy - 6.5, cy + 6.5, prof_bot - 1, PROF_TOP + 1))
    prof = prof.cut(cyl(PROF_CORE_D / 2, L + 2, (COL_X, 0, prof_bot - 1)))
    pr = add(Part("S01_column_profile_item8_80x80L", prof, "EN AW-6063-T66 (profile)",
                  f"purchased item Profil 8 80x80 leicht 0.0.265.80 cut to {L:.0f} mm; tap core M12 both ends",
                  category="purchased", color=(0.8, 0.81, 0.83), explode=(0, 0, 200),
                  mass_kg=PROF_KG_M * L / 1000, mass_src="item24 5.33 kg/m (SOURCED)", notes="core bore diameter ESTIMATE"))
    pr.tap_material = "EN AW-6063-T66 (profile)"
    drill(pr, Hole("core_top", (COL_X, 0, PROF_TOP), DOWN, F.ISO["M12"]["tap"], 30, "tap", "M12"))
    drill(pr, Hole("core_bot", (COL_X, 0, prof_bot), UP, F.ISO["M12"]["tap"], 30, "tap", "M12"))
    drill(ft, Hole("core", (COL_X, 0, zf0), UP, 13.5, FOOT_T - 5, "clear", "M12", cbore=(20.0, 7.5)))
    bolt("B_column_bot_M12", "M12", 30, [(ft.name, "core"), (pr.name, "core_bot")], std="DIN 7984", washer=False, group="G2b profile->column foot")
    tap_adapter("colcb", COL_X, 0, "M12") if False else None
    # la testa M12 sta nella lamatura sotto il piede: foro passante D21 nell'adattatore per l'accesso
    PARTS["P01_base_adapter_plate"].shape = PARTS["P01_base_adapter_plate"].shape.cut(cyl(11, AD_T + 2, (COL_X, 0, AD_Z0 - 1)))
    # staffa colonna -> busto OpenArm (body_link0)
    x0, x1, y0, y1, _ = BL_PLATE
    s = box(x0, x1, y0, y1, BRK_Z0, TORSO_Z)
    s = s.cut(box(COL_X - PROF / 2 - 0.2, COL_X + PROF / 2 + 0.2, -PROF / 2 - 0.2, PROF / 2 + 0.2, BRK_Z0 - 1, BRK_Z0 + 5))
    s = s.cut(G.rounded_rect(25, 0, 74, 124, 15, BRK_Z0 - 1, 8))
    for sy in (-1, 1):
        s = s.cut(G.rounded_rect(-17, sy * 64, 150, 26, 15, BRK_Z0 - 1, 6))
    s = s.cut(G.rounded_rect(-118, 0, 22, 60, 15, BRK_Z0 - 1, 5))
    br = add(Part("P02_column_to_torso_bracket", s, "EN AW-6082-T6",
                  "CNC milled from 20 mm plate: 80x80 spigot pocket 5 mm, underside pockets, M12 cbore, 8x M6 clearance, 4x M4 tapped",
                  color=(0.72, 0.73, 0.75), explode=(0, 0, 280)))
    drill(br, Hole("core", (COL_X, 0, TORSO_Z), DOWN, 13.5, BRK_T - 5, "clear", "M12", cbore=(20.0, 7.5)))
    bolt("B_column_top_M12", "M12", 30, [(br.name, "core"), (pr.name, "core_top")], std="DIN 7984", washer=False,
         group="G3 profile->torso bracket")
    for k, (bx, by) in enumerate(BL_BOLTS):
        drill(br, Hole(f"bl{k}", (bx, by, BRK_Z0), UP, 6.6, BRK_T, "clear", "M6"))
    for k, (bx, by) in enumerate([(88, 88), (88, -88), (-148, 88), (-148, -88)]):
        drill(br, Hole(f"wc{k}", (bx, by, BRK_Z0), UP, F.ISO["M4"]["tap"], 10, "tap", "M4"))
    return ft, pr, br


# ====================================================================== OpenArm body_link0 (purchased, simplified B-rep from the official STL)
def body_link0():
    z0 = TORSO_Z
    x0, x1, y0, y1, t = BL_PLATE
    s = box(x0, x1, y0, y1, z0, z0 + t)
    s = s.fuse(box(-30, 30, -30, 30, z0 + t, z0 + 650))
    # fazzoletti (inviluppo misurato sulle sezioni dello STL)
    rear = cq.Workplane("XZ", origin=(0, 0, 0)).polyline([(-152, z0 + t), (-30, z0 + t), (-30, z0 + 230), (-42, z0 + 200), (-100, z0 + 100), (-129, z0 + 50)]).close().extrude(12).translate((0, 6, 0)).val()
    s = s.fuse(rear)
    for sy in (-1, 1):
        side = cq.Workplane("YZ").polyline([(sy * 30, z0 + t), (sy * 85, z0 + t), (sy * 44, z0 + 50), (sy * 30, z0 + 100)]).close().extrude(10).translate((-5, 0, 0)).val()
        s = s.fuse(side)
    s = s.fuse(box(-72, 53, -79, 79, z0 + 640, z0 + 700)).fuse(box(-85, 65, -63, 63, z0 + 700, z0 + 745))
    s = s.fuse(box(-59, 39, -50, 50, z0 + 745, z0 + 760)).fuse(box(-46, 26, -40.4, 40.4, z0 + 760, z0 + 773))
    s = s.cut(box(23, 30.1, -8.5, 8.5, z0 + t + 1, z0 + 639))          # cava frontale del montante (ASSUMED)
    s = s.cut(box(-30.1, -23, -8.5, 8.5, z0 + 240, z0 + 639))          # cava posteriore (sopra il fazzoletto)
    p = add(Part("OA_body_link0", s, "purchased", "purchased (Enactic OpenArm 2.0 torso)", category="purchased",
                 color=(0.25, 0.25, 0.25), explode=(0, 0, 360), mass_kg=BL_MASS, mass_src="openarm_description URDF 13.89 kg (SOURCED)",
                 motion="lift", mesh_file=str(OA_STL), notes="interference envelope simplified from the official STL; real STL used for clearances/exports"))
    p.mesh_offset = (0.0, 0.0, TORSO_Z)
    for k, (bx, by) in enumerate(BL_BOLTS):
        drill(p, Hole(f"g{k}", (bx, by, z0), UP, F.ISO["M6"]["tap"], t, "tap", "M6"))
        bolt(f"B_body_link0_{k}", "M6", 30, [("P02_column_to_torso_bracket", f"bl{k}"), (p.name, f"g{k}")], group="G4 torso bracket->body_link0",
             assumed="docs.openarm.dev: 48x M6 taps on 30 mm grid; STL shows 5.5 mm holes -> if clearance, use M5x35 + nut")
    p.tap_material = "OpenArm body plate (Al, ASSUMED 5052)"
    # fori della griglia usati da altri (nessuno) - la cava del montante 60x60 per staffe frontali (ASSUMED Misumi serie 6)
    return p


def post_tnut(name, y, z, thread="M6", side=1):
    """T-nut in the front (side=+1, x=+30) or rear (side=-1, x=-30) slot of the body_link0 60x60 post - ASSUMED Misumi series-6 slot 8"""
    tn = add(Part(name, box(side * 24, side * 30, y - 8, y + 8, z - 5, z + 5), "S235 / 1.4301", "purchased T-slot nut slot 8 M6 (ASSUMED Misumi post)",
                  category="fastener", color=(0.6, 0.6, 0.6), explode=(0, 0, 360), motion="lift"))
    drill(tn, Hole("t", (side * 30, y, z), (-side, 0, 0), F.ISO[thread]["tap"], 6.0, "tap", thread))
    return tn


# ====================================================================== battery tray, e-plates, electronics envelopes
def purchased_box(name, x0, x1, y0, y1, z0, z1, mass, src, color=(0.2, 0.2, 0.22), explode=(0, 0, 150), motion=""):
    return add(Part(name, box(x0, x1, y0, y1, z0, z1), "purchased", "purchased", category="purchased", color=color,
                    explode=explode, mass_kg=mass, mass_src=src, motion=motion))


def power():
    z = AD_Z1
    # vasca batteria: lamiera 2 mm piegata con ali laterali
    tx0, tx1, ty = 45.0, 45.0 + BATT["L"] + 8.0, BATT["W"] / 2 + 10.0      # 10 mm laterali per dadi + tamponi EPDM
    t = 2.0
    s = box(tx0, tx1, -ty, ty, z, z + t)
    for sy in (-1, 1):
        s = s.fuse(box(tx0, tx1, sy * ty - (t if sy > 0 else 0), sy * ty + (0 if sy > 0 else t), z, z + 50))
        s = s.fuse(box(tx0, tx1, sy * ty + (0 if sy > 0 else -20), sy * ty + (20 if sy > 0 else 0), z, z + t))
    for sx, xx in ((-1, tx0), (1, tx1)):
        s = s.fuse(box(xx - (0 if sx > 0 else 0) - (t if sx > 0 else 0), xx + (0 if sx > 0 else t), -ty, ty, z, z + 50))
    s = s.cut(G.rounded_rect((tx0 + tx1) / 2, 0, 200, 300, 5, z - 1, 20))         # finestra di alleggerimento sul fondo
    tr = add(Part("P03_battery_tray", s, "EN AW-5754-H22", "laser cut + bent 2 mm sheet, 3 bends per side",
                  color=(0.6, 0.62, 0.65), explode=(0, 0, 120)))
    for sy in (-1, 1):
        for k, x in enumerate((75, 185, 295)):
            hn = f"fl{'L' if sy > 0 else 'R'}{k}"
            y = sy * (ty + 10)
            drill(tr, Hole(hn, (x, y, z + t), DOWN, 6.6, t, "clear", "M6"))
            tap_adapter(f"bt{hn}", x, y, "M6")
            bolt(f"B_batt_tray_{hn}", "M6", 10, [(tr.name, hn), ("P01_base_adapter_plate", f"bt{hn}")], washer=False, group="G8 battery tray->adapter")
            ADAPTER_KEEP.append((x - 12, x + 12, y - 12, y + 12))
    bx0, by0 = (tx0 + tx1) / 2 - BATT["L"] / 2, -BATT["W"] / 2
    purchased_box("E01_battery_48V_15s30Ah_LFP", bx0, bx0 + BATT["L"], by0, by0 + BATT["W"], z + t + 3, z + t + 3 + BATT["H"], BATT["mass"],
                  "ESTIMATE custom flat 15s 30 Ah LFP pack (1.44 kWh)", color=(0.15, 0.32, 0.62))
    add(Part("P04_battery_pad_EPDM", box(bx0 + 10, bx0 + BATT["L"] - 10, by0 + 10, by0 + BATT["W"] - 10, z + t, z + t + 3).cut(
        G.rounded_rect((tx0 + tx1) / 2, 0, 200, 300, 5, z, 20)), "TPU 90A / EPDM", "die-cut 3 mm EPDM sheet", color=(0.05, 0.05, 0.05),
        explode=(0, 0, 130)))
    # barre di ritenuta sopra la batteria (2), estremita' piegate e imbullonate alle pareti della vasca
    ztop = z + t + 3 + BATT["H"]
    for k, x in enumerate((110.0, 270.0)):
        bar = box(x - 15, x + 15, -ty - 3, ty + 3, ztop, ztop + 3)
        for sy in (-1, 1):
            yy = sy * ty
            bar = bar.fuse(box(x - 15, x + 15, yy, yy + 3 * sy, z + 28, ztop + 3))
        pb = add(Part(f"P05_battery_hold_down_{k}", bar, "EN AW-5754-H22", "laser cut + bent 3 mm sheet",
                      color=(0.6, 0.62, 0.65), explode=(0, 0, 220)))
        for sy in (-1, 1):
            yy = sy * (ty + 3)
            hn = f"e{'L' if sy > 0 else 'R'}"
            drill(pb, Hole(hn, (x, yy, z + 38), (0, -sy, 0), 5.5, 3, "clear", "M5"))
            drill(tr, Hole(f"hd{k}{hn}", (x, sy * ty, z + 38), (0, -sy, 0), 5.5, t, "nut", "M5"))
            bolt(f"B_hold_down_{k}{hn}", "M5", 12, [(pb.name, hn), (tr.name, f"hd{k}{hn}")], female="nut", washer=False, group="G8b battery hold-down")
    # piastre elettroniche (3): destra, sinistra, posteriore - 3 mm 5754, componenti fissati con M4 (non verificati)
    ET = 2.0
    def eplate(name, x0, x1, y0, y1, bolts_xy):
        s = G.rounded_rect((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, ET, z, 6)
        e = add(Part(name, s, "EN AW-5754-H22", "laser cut 2 mm sheet + PEM nuts M4 for components",
                     color=(0.55, 0.57, 0.6), explode=(0, 0, 100)))
        for k, (x, y) in enumerate(bolts_xy):
            drill(e, Hole(f"m{k}", (x, y, z + ET), DOWN, 5.5, ET, "clear", "M5"))
            tap_adapter(f"{name[:3]}m{k}", x, y, "M5")
            bolt(f"B_{name[:3]}_{k}", "M5", 10, [(e.name, f"m{k}"), ("P01_base_adapter_plate", f"{name[:3]}m{k}")], group="G9 e-plates->adapter")
            ADAPTER_KEEP.append((x - 12, x + 12, y - 12, y + 12))
        return e
    eplate("P06_eplate_right", -160, 43, -266, -108, [(-153, -115), (-153, -259), (-10, -115), (-10, -259)])
    eplate("P07_eplate_left", -160, 43, 108, 266, [(-153, 115), (-153, 259), (-10, 115), (-10, 259)])
    eplate("P08_eplate_rear", -330, -160, -88, 152, [(-200, -80), (-170, -10), (-323, 36), (-323, 144)])
    ze = z + ET
    purchased_box("E02_dcdc_DDR480C_A", -146, -146 + DCDC["L"], -120 - DCDC["W"], -120, ze, ze + DCDC["H"], DCDC["mass"], "Mean Well DDR-480C-24 (SOURCED)", (0.75, 0.75, 0.78))
    purchased_box("E03_dcdc_DDR480C_B", -146, -146 + DCDC["L"], 120, 120 + DCDC["W"], ze, ze + DCDC["H"], DCDC["mass"], "Mean Well DDR-480C-24 (SOURCED)", (0.75, 0.75, 0.78))
    purchased_box("E04_din_rail_pnoz", -5, 40, -255, -248, ze, ze + 7.5, 0.05, "DIN rail 35x7.5 (EN 60715)", (0.7, 0.7, 0.7))
    purchased_box("E05_pilz_PNOZ_mB0", -5, -5 + PNOZ["L"], -252, -252 + PNOZ["W"], ze + 7.5, ze + 7.5 + PNOZ["H"], PNOZ["mass"], "Pilz 772100 (SOURCED)", (0.95, 0.8, 0.1))
    purchased_box("E06_contactor_K1", -5, -5 + CONTACTOR["L"], 120, 120 + CONTACTOR["W"], ze, ze + CONTACTOR["H"], CONTACTOR["mass"], "ESTIMATE", (0.85, 0.12, 0.1))
    purchased_box("E07_contactor_K2", -5, -5 + CONTACTOR["L"], 194, 194 + CONTACTOR["W"], ze, ze + CONTACTOR["H"], CONTACTOR["mass"], "ESTIMATE", (0.85, 0.12, 0.1))
    purchased_box("E08_jetson_agx_orin_module", -318, -318 + JETSON_MOD["L"], -78, -78 + JETSON_MOD["W"], ze, ze + JETSON_MOD["H"], JETSON_MOD["mass"], "ESTIMATE AGX Orin module + carrier", (0.12, 0.12, 0.13))
    purchased_box("E09_orion_tr_48_48_6", -318, -318 + CHARGER["L"], 40, 40 + CHARGER["W"], ze, ze + CHARGER["H"], 1.3, "Victron Orion-Tr Smart 48/48-6 isolated (electrical lead; envelope ESTIMATE)", (0.25, 0.25, 0.27))
    return tr



# ====================================================================== SICK nanoScan3 corner pods
POD_BACK = NS3_AXIS_FROM_REAR + NS3_PLUG + 6.0 + 3.0        # asse specchio -> faccia esterna dello schienale


SCAN_HEADS = (45.0, -135.0)        # RB-THERON: front-left / rear-right (its own picoScan120 sit in the other two corners)
POD_SHIFT = 35.0                   # spostamento laterale verso il fianco: il pod anteriore resta fuori dalla sagoma della stazione di ricarica


def scanner_centres(gap=3.0):
    """scanner centre on the corner diagonal, pushed out until the pod back plate clears the base outline, then shifted sideways"""
    out = []
    for head in SCAN_HEADS:
        f = np.array([math.cos(math.radians(head)), math.sin(math.radians(head))])
        l = np.array([-f[1], f[0]])
        proj = max(float(np.dot(v, f)) for v in BASE_OUTLINE)
        d = proj + POD_BACK + gap
        c = d * f + POD_SHIFT * l
        out.append((round(c[0], 1), round(c[1], 1), head))
    return out


def scanner_pods():
    out = []
    for k, (cx, cy, head) in enumerate(scanner_centres()):
        R = G.rotz(head)
        f, l = R[:, 0], R[:, 1]          # f = heading, l = left
        zb = SCAN_Z - NS3_PLANE          # base of the housing (129.5)
        ax_rear = NS3_AXIS_FROM_REAR
        c_rear = np.array([cx, cy, 0]) - f * ax_rear       # centro faccia posteriore
        # inviluppo scanner: corpo + cofano + spina di sistema
        def at(local_box):
            (a0, a1, b0, b1, z0, z1) = local_box
            s = box(a0, a1, b0, b1, z0, z1)
            return G.transform_shape(s, R, (cx, cy, 0))
        body = at((-ax_rear, NS3_D - ax_rear, -NS3_W / 2, NS3_W / 2, zb, zb + NS3_H - 30))
        hood = G.transform_shape(cyl(NS3_HOOD_D / 2, 30, (0, 0, zb + NS3_H - 30)), R, (cx, cy, 0))
        plug = at((-ax_rear - NS3_PLUG, -ax_rear, -25, 25, zb + 5, zb + 45))
        sc = add(Part(f"S02_nanoScan3_{k}", body.fuse(hood).fuse(plug), "purchased", "purchased SICK nanoScan3 NANS3-CAAZ30AN1",
                      category="purchased", color=(0.95, 0.8, 0.05), explode=tuple(np.r_[f[:2] * 150, 0]), mass_kg=NS3_MASS,
                      mass_src="SICK datasheet 0.67 kg (SOURCED)"))
        # staffa a U (lamiera 3 mm): fondo sotto lo scanner, 2 guance con i fori M5, schienale verso la Tracer, ala superiore sull'adattatore
        t = 3.0
        loc = []
        loc.append((-ax_rear - NS3_PLUG - 6 - t, NS3_D - ax_rear - 10, -NS3_W / 2 - t, NS3_W / 2 + t, zb - t, zb))         # fondo
        for sy in (-1, 1):
            loc.append((-ax_rear - NS3_PLUG - 6 - t, NS3_D - ax_rear - 10, sy * NS3_W / 2 + (0 if sy > 0 else -t), sy * NS3_W / 2 + (t if sy > 0 else 0), zb - t, zb + 45))
        xb = -ax_rear - NS3_PLUG - 6 - t
        loc.append((xb, xb + t, -NS3_W / 2 - t, NS3_W / 2 + t, zb - t, AD_Z1 + t))                                            # schienale
        sh = None
        for lb in loc:
            s_ = at(lb)
            sh = s_ if sh is None else sh.fuse(s_)
        # ala superiore: va dall'alto dello schienale verso l'interno sopra l'adattatore
        top = at((xb - 60, xb + t, -40, 40, AD_Z1, AD_Z1 + t))
        sh = sh.fuse(top)
        pb = add(Part(f"P09_scanner_pod_bracket_{k}", sh, "EN AW-5754-H22", "laser cut + bent 3 mm sheet (U-cradle + back + top flange)",
                      color=(0.3, 0.3, 0.32), explode=tuple(np.r_[f[:2] * 100, 0])))
        # fori scanner: 2 per lato (M5 x 7.5 ciechi nello scanner)
        for sy in (-1, 1):
            for j, xa in enumerate((-ax_rear + NS3_HOLE_FROM_REAR, -ax_rear + NS3_HOLE_FROM_REAR + NS3_HOLE_PITCH)):
                pl = np.array([cx, cy, 0]) + R @ np.array([xa, sy * (NS3_W / 2 + t), zb + NS3_HOLE_Z])
                ax = R @ np.array([0, -sy, 0])
                hn = f"s{'L' if sy > 0 else 'R'}{j}"
                drill(pb, Hole(hn, tuple(pl), tuple(ax), 5.5, t, "clear", "M5"))
                drill(sc, Hole(hn, tuple(pl + ax * t), tuple(ax), 4.2, 7.5, "tap", "M5"))
                bolt(f"B_scan{k}_{hn}", "M5", 10, [(pb.name, hn), (sc.name, hn)], group=f"G10 scanner {k}->pod", preload_frac=0.3,
                     assumed="hole positions read from the SICK dimension chain (ASSUMED)")
        sc.tap_material = "manufacturer thread (datasheet max insertion)"
        # ala sull'adattatore: 2 x M6
        for j, yl in enumerate((-22.0, 22.0)):
            pl = np.array([cx, cy, 0]) + R @ np.array([xb - 45, yl, 0])
            pl[2] = AD_Z1 + t
            drill(pb, Hole(f"a{j}", tuple(pl), DOWN, 5.5, t, "clear", "M5"))
            tap_adapter(f"pod{k}a{j}", pl[0], pl[1], "M5")
            bolt(f"B_pod{k}_a{j}", "M5", 10, [(pb.name, f"a{j}"), ("P01_base_adapter_plate", f"pod{k}a{j}")], washer=False, group=f"G11 pod {k}->adapter")
            ADAPTER_KEEP.append((pl[0] - 15, pl[0] + 15, pl[1] - 15, pl[1] + 15))
        out.append((sc, pb))
    return out


# ====================================================================== charging collector bracket
def charge_bracket():
    t = 4.0
    xw = 360.0
    s = box(326, xw + t, -55, 55, AD_Z1, AD_Z1 + t).fuse(box(xw, xw + t, -55, 55, 100, AD_Z1 + t))
    cb = add(Part("P10_charge_collector_bracket", s, "EN AW-5754-H22", "laser cut + bent 4 mm sheet (L)",
                  color=(0.3, 0.3, 0.32), explode=(150, 0, 0)))
    zc = 140.0
    col = add(Part("S03_roboteq_RPCOL90_100", box(xw + t, xw + t + ROBOPAD["D"], -ROBOPAD["W"] / 2, ROBOPAD["W"] / 2, zc - ROBOPAD["H"] / 2, zc + ROBOPAD["H"] / 2),
                   "purchased", "purchased Roboteq RoboPad collector", category="purchased", color=(0.72, 0.45, 0.2),
                   explode=(260, 0, 0), mass_kg=ROBOPAD["mass"], mass_src="ESTIMATE"))
    col.tap_material = "manufacturer thread (datasheet max insertion)"
    px, pz = ROBOPAD["pitch"]
    for k, (yy, zz) in enumerate(((-px / 2, zc - pz / 2 + 10), (px / 2, zc - pz / 2 + 10), (-px / 2, zc + pz / 2 - 10), (px / 2, zc + pz / 2 - 10))):
        drill(cb, Hole(f"c{k}", (xw, yy, zz), (1, 0, 0), 4.5, t, "clear", "M4"))
        drill(col, Hole(f"c{k}", (xw + t, yy, zz), (1, 0, 0), 3.3, 8, "tap", "M4"))
        bolt(f"B_charge_col_{k}", "M4", 10, [(cb.name, f"c{k}"), (col.name, f"c{k}")], group="G12 collector->bracket",
             assumed="RoboPad 74 x 56 hole pattern SOURCED; thread depth in the collector ASSUMED 8 mm; vertical pitch reduced to 36 (ASSUMED flange)")
    for k, yy in enumerate((-35.0, 35.0)):
        for j, xx in enumerate((335.0,)):
            hn = f"a{k}{j}"
            drill(cb, Hole(hn, (xx, yy, AD_Z1 + t), DOWN, 6.6, t, "clear", "M6"))
            tap_adapter(f"chg{hn}", xx, yy, "M6")
            bolt(f"B_charge_br_{hn}", "M6", 14, [(cb.name, hn), ("P01_base_adapter_plate", f"chg{hn}")], group="G12b collector bracket->adapter")
    return cb


# ====================================================================== superellipsoid helpers for shells
def se_inside_z(a, b, c, e1, e2, x, y, zc, taper=None, top=True):
    """z of the superellipsoid surface above (top=True) or below (x,y); None if outside. Bisection on z."""
    def Fz(z):
        t = (z - zc) / c
        s = taper(max(-1, min(1, t))) if taper else 1.0
        if abs(t) >= 1:
            return 2.0
        xy = (abs(x / (a * s)) ** (2 / e2) + abs(y / (b * s)) ** (2 / e2)) ** (e2 / e1)
        return xy + abs(t) ** (2 / e1)
    if Fz(zc) > 1:
        return None
    lo, hi = (zc, zc + c) if top else (zc - c, zc)
    for _ in range(60):
        m = (lo + hi) / 2
        inside = Fz(m) <= 1
        if top:
            lo, hi = (m, hi) if inside else (lo, m)
        else:
            lo, hi = (lo, m) if inside else (m, hi)
    return (lo + hi) / 2


def se_shell(a, b, c, e1, e2, center, t, taper=None):
    o = G.superellipsoid_solid(a, b, c, e1, e2, center=center, taper=taper)
    i = G.superellipsoid_solid(a - t, b - t, c - t, e1, e2, center=center, taper=taper)
    return o.cut(i)


# ====================================================================== shells
SK = dict(a=375.0, b=330.0, c=130.0, e1=0.15, e2=0.30, zc=170.0, t=2.5)     # proposed: e1 0.28->0.15, c 125->130, zc 165->170


DECK_TOP = 446.0


def deck_cover():
    """carter del ponte (sopra l'adattatore): scatola arrotondata 2 mm, scende fino al ponte della base; niente gonna attorno alla
    Ranger Air (ha la sua carrozzeria, ruote sterzanti 4WS) e niente paraurti decorativo"""
    t = 2.0
    # appoggiato sul ponte della base, dentro il suo contorno: nulla sporge dal retro (zona di aggancio della stazione AgileX)
    cx_ = (BS_X0 + BS_X1) / 2
    o = cq.Workplane("XY", origin=(cx_, 0, BS_H)).rect(BS_L - 2, BS_W - 2).extrude(DECK_TOP - BS_H).edges("|Z").fillet(28).edges(">Z").fillet(12).val()
    i = cq.Workplane("XY", origin=(cx_, 0, BS_H - 1)).rect(BS_L - 2 - 2 * t, BS_W - 2 - 2 * t).extrude(DECK_TOP - BS_H - t + 1).edges("|Z").fillet(26).val()
    s = o.cut(i)
    s = s.cut(G.rounded_rect(COL_X, 0, 100, 100, 50, DECK_TOP - 20, 10))                     # colonna
    for yc in (-118.0, 175.0):
        s = s.cut(box(-270, -186, yc - 16, yc + 16, DECK_TOP - 20, DECK_TOP + 5))              # montanti zaino
    for k, (cx, cy, head) in enumerate(scanner_centres()):
        R = G.rotz(head)
        s = s.cut(G.transform_shape(box(-NS3_AXIS_FROM_REAR - NS3_PLUG - 95, 150, -NS3_W / 2 - 14, NS3_W / 2 + 14, 100, 500), R, (cx, cy, 0)))
    dc = add(Part("SH01_deck_cover", s, "PA12 (SLS/MJF)", "SLS PA12 2 mm in 2 halves (front/rear), 4 M5 into standoffs; stands on the RB-THERON top inside its outline",
                  category="shell", color=(0.86, 0.86, 0.84), explode=(0, 0, 520)))
    for k, (x, y) in enumerate(((30.0, 92.0), (30.0, -92.0), (-140.0, 97.0), (-140.0, -97.0))):
        zb = DECK_TOP - t - 6.0
        boss = cyl(9, 6, (x, y, zb))
        dc.shape = dc.shape.fuse(boss)
        drill(dc, Hole(f"m{k}", (x, y, DECK_TOP), DOWN, 5.5, DECK_TOP - zb, "clear", "M5"))
        so = add(Part(f"P11_deck_standoff_{k}", cyl(7, zb - AD_Z1, (x, y, AD_Z1)), "EN AW-6082-T6",
                      f"turned D14 x {zb - AD_Z1:.1f} mm, M5 male stud bottom / M5 tapped top", color=(0.7, 0.7, 0.72), explode=(0, 0, 300)))
        drill(so, Hole("top", (x, y, zb), DOWN, F.ISO["M5"]["tap"], 12, "tap", "M5"))
        so.tap_material = "EN AW-6082-T6"
        tap_adapter(f"dk{k}", x, y, "M5")
        ADAPTER_KEEP.append((x - 12, x + 12, y - 12, y + 12))
        bolt(f"B_deck_{k}", "M5", 16, [(dc.name, f"m{k}"), (so.name, "top")], std="ISO 7380", group="G13 deck cover->standoffs", preload_frac=0.15)
    return dc


def column_covers():
    # carter fisso (sul guscio base) attorno al manicotto: tubo superellittico, 2 semigusci
    t = 2.0
    zc0, zc1 = DECK_TOP + 0.2, 540.0
    o = cq.Workplane("XY", origin=(COL_X, 0, zc0)).rect(120, 120).extrude(zc1 - zc0).edges("|Z").fillet(24).val()
    i = cq.Workplane("XY", origin=(COL_X, 0, zc0 - 1)).rect(120 - 2 * t, 120 - 2 * t).extrude(zc1 - zc0 + 2).edges("|Z").fillet(22).val()
    s = o.cut(i)
    cc = add(Part("SH02_column_cover_fixed", s, "PA12 (SLS/MJF)", "SLS PA12 2 mm, 2 halves clipped around the profile (T-slot clips)",
                  category="shell", color=(0.86, 0.86, 0.84), explode=(0, -300, 150)))
    # cintura mobile (sotto il busto, fissata alla staffa P02): chiude la piastra di body_link0
    zw0, zw1 = 562.0, 838.0
    o = cq.Workplane("XY", origin=(-28, 0, zw0)).rect(268, 200).extrude(zw1 - zw0).edges("|Z").fillet(8).val()
    i = cq.Workplane("XY", origin=(-28, 0, zw0 - 1)).rect(268 - 2 * t, 200 - 2 * t).extrude(zw1 - zw0 + 2).edges("|Z").fillet(5).val()
    s = o.cut(i)
    # passaggio bracci del vassoio
    for sy in (-1, 1):
        s = s.cut(box(90, 120, sy * 60 - 16, sy * 60 + 16, 900, 960))
    wc = add(Part("SH03_waist_cover", s, "PA12 (SLS/MJF)", "SLS PA12 3 mm, 2 halves, hangs from P02 on 4 lugs with M4",
                  category="shell", color=(0.86, 0.86, 0.84), explode=(0, 300, 280), motion="lift"))
    for k, (bx, by) in enumerate([(88, 88), (88, -88), (-148, 88), (-148, -88)]):
        # aletta interna dalla parete al foro, sotto la staffa
        sx = 1 if bx > 0 else -1
        sy = 1 if by > 0 else -1
        xw = -28 + sx * (134 - t)
        yw = sy * (100 - t)
        lug = box(min(bx - 7, xw), max(bx + 7, xw), min(by - 7, yw), max(by + 7, yw), BRK_Z0 - 10, BRK_Z0)
        wc.shape = wc.shape.fuse(lug)
        drill(wc, Hole(f"l{k}", (bx, by, BRK_Z0 - 10), UP, 4.5, 10, "clear", "M4"))
        bolt(f"B_waist_{k}", "M4", 16, [(wc.name, f"l{k}"), ("P02_column_to_torso_bracket", f"wc{k}")], group="G14 waist cover->bracket",
             preload_frac=0.3)
    return cc, wc


TORSO_SH = dict(a=105.0, b=105.0, c=261.0, e1=0.45, e2=0.5, cx=0.0,          # proposed (sim: a 135, b 170, c 235, cx -30): arms clear + covers body_link0 top
                zc=TORSO_Z + 529.0, t=2.0)


def torso_taper(t):
    return 0.80 + 0.20 * np.clip((t + 1) / 1.6, 0, 1) ** 0.8


def torso_shell():
    S = TORSO_SH
    s = se_shell(S["a"], S["b"], S["c"], S["e1"], S["e2"], (S["cx"], 0, S["zc"]), S["t"], taper=torso_taper)
    # aperture: fondo (cintura), spalle (bracci), collo/testa, finestra Gemini, bracci vassoio
    s = s.cut(box(-200, 200, -200, 200, 0, TORSO_Z + 312))
    for sy in (-1, 1):
        s = s.cut(cyl(82, 200, (0, sy * 58, ARM_SHOULDER_Z), (0, sy, 0)))
    s = s.cut(box(-200, 200, -200, 200, TORSO_Z + 771, TORSO_Z + 900))           # bordo superiore a 1351: la testa (da 1356) lo chiude
    R = G.roty(GEM_TILT)
    s = s.cut(G.transform_shape(box(-30, 40, -66, 66, -18, 18), R, GEM_POS))
    for sy in (-1, 1):
        s = s.cut(box(40, 150, sy * 60 - 16, sy * 60 + 16, BUF_Z - 40, BUF_Z + 10))
    halves = {}
    for nm, sx, (x0, x1) in (("SH04a_torso_shell_front", 1, (0.0, 300.0)), ("SH04b_torso_shell_rear", -1, (-300.0, 0.0))):
        halves[sx] = add(Part(nm, s.intersect(box(x0, x1, -300, 300, 0, 2000)), "PA12 (SLS/MJF)",
                              "SLS/MJF PA12 3 mm half shell (split x=0, tongue-and-groove seam not modelled), 2 M4 inserts",
                              category="shell", color=(0.86, 0.86, 0.84), explode=(sx * 250, 0, 150), motion="lift"))
    # staffe del guscio sul montante (cava frontale / posteriore ASSUMED): gamba sul montante, braccio, linguetta verso la parete
    for sx, zb_, xt in ((1, TORSO_Z + 450.0, 80.0), (-1, TORSO_Z + 600.0, 82.0)):
        t = 3.0
        leg = box(sx * 30, sx * (30 + t), -20, 20, zb_ - 30, zb_ + 30)
        arm_ = box(sx * 30, sx * (xt + t), -20, 20, zb_ + 27, zb_ + 30)
        tab = box(sx * xt, sx * (xt + t), -20, 20, zb_ - 10, zb_ + 30)
        nmb = "P27_torso_shell_bracket_front" if sx > 0 else "P28_torso_shell_bracket_rear"
        bk = add(Part(nmb, leg.fuse(arm_).fuse(tab), "EN AW-5754-H22", "laser cut + bent 3 mm sheet (Z)", color=(0.3, 0.3, 0.32),
                      explode=(sx * 180, 0, 150), motion="lift"))
        for k, zz in enumerate((zb_ - 18, zb_ + 8)):
            tn = post_tnut(f"tnut_shell_{'f' if sx > 0 else 'r'}{k}", 0, zz, side=sx)
            drill(bk, Hole(f"p{k}", (sx * (30 + t), 0, zz), (-sx, 0, 0), 6.6, t, "clear", "M6"))
            bolt(f"B_shellbr_{'f' if sx > 0 else 'r'}{k}", "M6", 10, [(bk.name, f"p{k}"), (tn.name, "t")], female="tnut", preload_frac=0.15,
                 nut_spec="slot-8 T-nut M6 (OpenArm post, ASSUMED)", group=f"G28 torso shell bracket {'front' if sx > 0 else 'rear'}->post",
                 assumed="post slot ASSUMED (Misumi 60 series)")
        hs_ = halves[sx]
        xw = sx * (xt + t)
        boss = box(xw, sx * 200, -9, 9, zb_ + 2, zb_ + 20).intersect(
            G.superellipsoid_solid(S["a"], S["b"], S["c"], S["e1"], S["e2"], center=(S["cx"], 0, S["zc"]), taper=torso_taper))
        hs_.shape = hs_.shape.fuse(boss)
        for k, yy in enumerate((-5.0, 5.0) if False else (0.0,)):
            pass
        drill(bk, Hole("s0", (sx * xt, 0, zb_ + 11), (sx, 0, 0), 4.5, t, "clear", "M4"))
        drill(hs_, Hole("s0", (xw, 0, zb_ + 11), (sx, 0, 0), F.INSERTS["M4"]["hole"], 10, "insert", "M4"))
        bolt(f"B_shell_{'f' if sx > 0 else 'r'}", "M4", 12, [(bk.name, "s0"), (hs_.name, "s0")], female="insert", preload_frac=0.07,
             group=f"G29 torso shell {'front' if sx > 0 else 'rear'} half->bracket")
    sh = halves[1]
    return sh


HEAD = dict(a=85.0, b=95.0, c=82.0, e1=0.85, e2=0.9, z=TORSO_Z + 828.0, t=2.0)


def head():
    H_ = HEAD
    s = se_shell(H_["a"], H_["b"], H_["c"], H_["e1"], H_["e2"], (0, 0, H_["z"]), H_["t"])
    zpl = TORSO_Z + 773.0                         # cima di body_link0
    s = s.cut(box(-200, 200, -200, 200, 0, zpl + 3))
    s = s.cut(cyl(9, 100, (-10, 0, H_["z"] + 40)))                                   # passaggio asta
    s = s.cut(box(60, 120, -70, 70, H_["z"] - 50, H_["z"] + 40))                     # finestra frontale (visiera)
    hs = add(Part("SH05_head_shell", s, "PA12 (SLS/MJF)", "SLS PA12 2.5 mm, painted; smoked PETG visor bonded",
                  category="shell", color=(0.86, 0.86, 0.84), explode=(0, 0, 520), motion="lift"))
    # piastra collo su body_link0 (fissaggio ASSUMED: 4 x M4 nel coperchio del giunto)
    pl = cyl(64, 3, (0, 0, zpl))
    pl = pl.cut(cyl(8, 5, (-10, 0, zpl - 1)))
    np_ = add(Part("P16_head_neck_plate", pl, "EN AW-5754-H22", "laser cut 3 mm disc D120", color=(0.3, 0.3, 0.32),
                   explode=(0, 0, 470), motion="lift"))
    bl = PARTS["OA_body_link0"]
    mz0 = zpl + 3
    mast = box(-38, 18, -33, 33, mz0, mz0 + 8).fuse(cyl(7, H_["z"] + 128 - mz0, (-10, 0, mz0)))
    ms = add(Part("P17_insta360_mast", mast, "EN AW-6082-T6", "turned D14 rod + milled 56x66x8 foot (one piece, CNC), 1/4\"-20 stud at top",
                  color=(0.1, 0.1, 0.11), explode=(0, 0, 650), motion="lift"))
    for k, (x, y) in enumerate(((-30, 25), (-30, -25), (10, 25), (10, -25))):
        drill(ms, Hole(f"b{k}", (x, y, mz0 + 8), DOWN, 4.5, 8, "clear", "M4"))
        drill(np_, Hole(f"b{k}", (x, y, zpl + 3), DOWN, 4.5, 3, "clear", "M4"))
        drill(bl, Hole(f"top{k}", (x, y, zpl), DOWN, 3.3, 8, "tap", "M4"))
        bolt(f"B_neck_{k}", "M4", 18, [(ms.name, f"b{k}"), (np_.name, f"b{k}"), (bl.name, f"top{k}")], group="G15 neck plate->body_link0",
             assumed="no published holes on the OpenArm J1 housing top: ASSUMED 4x M4, verify with Enactic CAD")
    for k, (x, y) in enumerate(((35, 35), (35, -35), (-20, 52), (-20, -52))):
        rr = 1.18
        lug = cyl(7, 10, (x, y, zpl + 3)).fuse(box(x - 4, x * rr + 4 * np.sign(x), y - 4, y * rr + 4 * np.sign(y), zpl + 3, zpl + 13))
        lug = lug.intersect(G.superellipsoid_solid(H_["a"], H_["b"], H_["c"], H_["e1"], H_["e2"], center=(0, 0, H_["z"])))
        hs.shape = hs.shape.fuse(lug)
        drill(np_, Hole(f"h{k}", (x, y, zpl), UP, 4.5, 3, "clear", "M4"))
        drill(hs, Hole(f"h{k}", (x, y, zpl + 3), UP, F.INSERTS["M4"]["hole"], 10, "insert", "M4"))
        bolt(f"B_head_{k}", "M4", 12, [(np_.name, f"h{k}"), (hs.name, f"h{k}")], female="insert", group="G16 head shell->neck plate", preload_frac=0.07)
    zc = H_["z"] + 128
    add(Part("S04_insta360_X4", box(-10 - X4["D"] / 2, -10 + X4["D"] / 2, -X4["W"] / 2, X4["W"] / 2, zc, zc + X4["H"]), "purchased",
             "purchased Insta360 X4", category="purchased", color=(0.12, 0.12, 0.13), explode=(0, 0, 760), mass_kg=X4["mass"],
             mass_src="Insta360 spec 203 g (SOURCED)", motion="lift"))
    return hs


def gemini():
    R = G.roty(GEM_TILT)
    gp = np.array(GEM_POS)
    body = G.transform_shape(box(-GEM["D"] / 2, GEM["D"] / 2, -GEM["L"] / 2, GEM["L"] / 2, -GEM["H"] / 2, GEM["H"] / 2), R, gp)
    gm = add(Part("S05_orbbec_gemini_336L", body, "purchased", "purchased Orbbec Gemini 336L", category="purchased",
                  color=(0.12, 0.12, 0.13), explode=(300, 0, 0), mass_kg=GEM["mass"], mass_src="Orbbec datasheet 135 g (SOURCED)", motion="lift"))
    gm.tap_material = "manufacturer thread (datasheet max insertion)"
    back = gp + R @ np.array([-GEM["D"] / 2, 0, 0])
    # staffa: piastra parallela al retro + gamba verticale sul montante (cava frontale, ASSUMED)
    t = 2.5
    plate = G.transform_shape(box(-GEM["D"] / 2 - t, -GEM["D"] / 2, -58, 58, -44, 14), R, gp)
    pb_ = gp + R @ np.array([-GEM["D"] / 2 - t / 2, 0, -42.0])
    # braccio: dal montante (x=30) fino al retro della camera
    zl = TORSO_Z + 560.0
    leg = box(30, 30 + t, -20, 20, zl, zl + 60)
    arm = box(30, pb_[0], -20, 20, zl + 60 - t, zl + 60)
    rise = box(pb_[0] - t, pb_[0], -20, 20, zl + 60 - t, pb_[2] + 1.0)
    s = plate.fuse(leg).fuse(arm).fuse(rise)
    gb = add(Part("P18_gemini_bracket", s, "EN AW-5754-H22", "laser cut + bent 2.5 mm sheet", color=(0.1, 0.1, 0.11),
                  explode=(220, 0, 0), motion="lift"))
    ax = R @ np.array([1.0, 0, 0])
    for k, yy in enumerate((-GEM["m4_pitch"] / 2, GEM["m4_pitch"] / 2)):
        pl = gp + R @ np.array([-GEM["D"] / 2 - t, yy, 0])
        drill(gb, Hole(f"g{k}", tuple(pl), tuple(ax), 4.5, t, "clear", "M4"))
        drill(gm, Hole(f"g{k}", tuple(pl + ax * t), tuple(ax), 3.3, 4.0, "tap", "M4"))
        bolt(f"B_gemini_{k}", "M4", 6, [(gb.name, f"g{k}"), (gm.name, f"g{k}")], group="G18 Gemini->bracket", preload_frac=0.05, washer=False,
             assumed="Gemini back M4 max insertion 4 mm, 0.4 N.m (SOURCED): bolt L = t + 3.5")
    for k, zz in enumerate((zl + 15, zl + 45)):
        tn = post_tnut(f"tnut_gemini_{k}", 0, zz)
        drill(gb, Hole(f"p{k}", (30 + t, 0, zz), (-1, 0, 0), 6.6, t, "clear", "M6"))
        bolt(f"B_gemini_post_{k}", "M6", 10, [(gb.name, f"p{k}"), (tn.name, "t")], female="tnut", preload_frac=0.15, nut_spec="slot-8 T-nut M6 (OpenArm post, ASSUMED)",
             group="G19 Gemini bracket->post", assumed="post slot ASSUMED (Misumi 60 series)")
    return gm


def chest_tray():
    """vassoio di kitting: 2 meta' (SLS PA12) su carrello in lamiera fissato al montante; aggancio rapido a perni + nottolino"""
    ys_all = sorted([sy * y for sy in (-1, 1) for y in BUF_YS])
    x0, x1 = BUF_X - POCKET / 2 - WALL, BUF_X + POCKET / 2 + WALL
    y0, y1 = ys_all[0] - POCKET / 2 - WALL, ys_all[-1] + POCKET / 2 + WALL
    zb = BUF_Z - 12.0
    zt = BUF_Z + POCKET_H
    t = 3.0
    # carrello: due bracci dal montante + piano sotto le meta'
    car = box(x0 + 5, x1 - 5, y0 + 20, y1 - 20, zb - t, zb)
    for sy in (-1, 1):
        car = car.fuse(box(30, x0 + 30, sy * 60 - 12, sy * 60 + 12, zb - t, zb))
    car = car.fuse(box(30, 30 + t, -72, 72, zb - 70, zb))
    cr = add(Part("P19_tray_carrier", car, "EN AW-5754-H22", "laser cut + bent 3 mm sheet", color=(0.3, 0.3, 0.32),
                  explode=(260, 0, -60), motion="lift"))
    for k, zz in enumerate((zb - 60, zb - 40, zb - 25, zb - 10)):
        tn = post_tnut(f"tnut_tray_{k}", 0, zz)
        drill(cr, Hole(f"p{k}", (30 + t, 0, zz), (-1, 0, 0), 6.6, t, "clear", "M6"))
        bolt(f"B_tray_post_{k}", "M6", 10, [(cr.name, f"p{k}"), (tn.name, "t")], female="tnut", preload_frac=0.15, nut_spec="slot-8 T-nut M6 (OpenArm post, ASSUMED)",
             group="G20 tray carrier->post", assumed="post slot ASSUMED (Misumi 60 series)")
    for side, sy in (("L", 1), ("R", -1)):
        ya, yb = (0.5, y1) if sy > 0 else (y0, -0.5)
        s = box(x0, x1, ya, yb, zb, zt - CHAMF)
        for yc in [y for y in ys_all if y * sy > 0]:
            s = s.cut(box(BUF_X - POCKET / 2, BUF_X + POCKET / 2, yc - POCKET / 2, yc + POCKET / 2, BUF_Z, zt))
            # svasatura 45 gradi: piramide tronca
            ch = cq.Solid.makeLoft([cq.Wire.makePolygon([V(BUF_X - POCKET / 2, yc - POCKET / 2, zt - CHAMF), V(BUF_X + POCKET / 2, yc - POCKET / 2, zt - CHAMF),
                                                          V(BUF_X + POCKET / 2, yc + POCKET / 2, zt - CHAMF), V(BUF_X - POCKET / 2, yc + POCKET / 2, zt - CHAMF)], close=True),
                                    cq.Wire.makePolygon([V(BUF_X - POCKET / 2 - CHAMF, yc - POCKET / 2 - CHAMF, zt), V(BUF_X + POCKET / 2 + CHAMF, yc - POCKET / 2 - CHAMF, zt),
                                                         V(BUF_X + POCKET / 2 + CHAMF, yc + POCKET / 2 + CHAMF, zt), V(BUF_X - POCKET / 2 - CHAMF, yc + POCKET / 2 + CHAMF, zt)], close=True)], True)
            rim = box(BUF_X - POCKET / 2 - CHAMF + 1, BUF_X + POCKET / 2 + CHAMF - 1, yc - POCKET / 2 - CHAMF + 1, yc + POCKET / 2 + CHAMF - 1, zt - CHAMF, zt).cut(ch)
            s = s.fuse(rim.intersect(box(x0, x1, ya, yb, zt - CHAMF, zt)))
        tp = add(Part(f"P20_tray_half_{side}", s, "PA12 (SLS/MJF)", "MJF PA12 (fits 380x284 bed), 3 pockets 60x60 with 16 mm 45-deg lead-in",
                      category="custom", color=(0.86, 0.86, 0.84), explode=(320, sy * 120, 40), motion="lift"))
        # 2 perni di centraggio (viti a spalla ISO 7379 D8) sul carrello + boccole nella meta'
        for k, yy in enumerate((sy * 120, sy * 230)):
            drill(tp, Hole(f"pin{k}", (BUF_X, yy, zb), UP, 8.2, 8, "bore"))
            drill(cr, Hole(f"pin{side}{k}", (BUF_X, yy, zb), DOWN, 6.6, t, "clear", "M6"))
            sh = add(Part(f"S06_shoulder_screw_{side}{k}", cyl(4, 8, (BUF_X, yy, zb)).fuse(cyl(6.5, 4.5, (BUF_X, yy, zb + 8))) .cut(cyl(2.6, 6, (BUF_X, yy, zb + 8.6))),
                          "S235 / 1.4301", "purchased ISO 7379 shoulder screw D8x8 M6 (locating pin; head relieved in the tray)", category="fastener",
                          color=(0.6, 0.6, 0.6), explode=(320, sy * 120, 0), motion="lift"))
            drill(tp, Hole(f"head{k}", (BUF_X, yy, zb + 8), UP, 14.0, 5, "bore"))
        # nottolino a molla GN 617 al centro (blocca la meta' sul carrello)
        drill(tp, Hole("plunger", (BUF_X, sy * 175, zb), UP, 8.2, 8, "bore"))
        drill(cr, Hole(f"plg{side}", (BUF_X, sy * 175, zb), DOWN, 8.2, t, "bore"))
    return cr


def pauldrons():
    """spallacci (mobili col link2): solo per la verifica di ingombro - fissaggio ASSUMED con 2 M3 nella carcassa del motore J2"""
    return []


# ====================================================================== coffee backpack
def coffee():
    zs = COF_SH
    t = 6.0
    # mensola: piano 6 mm 6082 (filettature M3/M4 dirette) + lingua verso la pila di bicchieri
    shelf = G.rounded_rect(-245, -63, 150, 526, t, zs - t, 20)
    shelf = shelf.fuse(box(-175, -68, -300, -240, zs - t, zs))
    shelf = shelf.cut(box(-330, -262, -330, -302, zs - t - 1, zs + 1))                 # smusso: resta dentro la pianta del guscio
    shelf = shelf.cut(G.rounded_rect(-230, 40, 80, 220, 10, zs - t - 1, 15))              # alleggerimento sotto la macchina
    sh = add(Part("P21_coffee_shelf", shelf, "EN AW-6082-T6", "waterjet 6 mm 6082 plate, drilled + tapped M3/M4", color=(0.6, 0.62, 0.65),
                  explode=(-250, 0, 120)))
    # montanti a C (lamiera 3 mm) dall'adattatore alla mensola
    for k, (yc) in enumerate((-118.0, 175.0)):
        t3 = 2.0
        x0, x1 = -266.0, -190.0
        web = box(x0, x1, yc - t3 / 2, yc + t3 / 2, AD_Z1, zs - t)
        fl1 = box(x0, x0 + t3, yc - 12, yc + 12, AD_Z1 + 25, zs - t - 25)
        fl2 = box(x1 - t3, x1, yc - 12, yc + 12, AD_Z1 + 25, zs - t - 25)
        foot = box(x0, x1, yc - 20, yc + 20, AD_Z1, AD_Z1 + t3)
        top = box(x0, x1, yc - 20, yc + 20, zs - t - t3, zs - t)
        up = add(Part(f"P22_coffee_upright_{k}", web.fuse(fl1).fuse(fl2).fuse(foot).fuse(top), "EN AW-5754-H22",
                      "laser cut + bent 2 mm sheet (C-channel 80x24 with feet)", color=(0.55, 0.57, 0.6), explode=(-250, 0, 60)))
        for j, (xx, yy) in enumerate(((x0 + 15, yc - 10), (x1 - 15, yc + 10))):
            drill(up, Hole(f"f{j}", (xx, yy, AD_Z1 + t3), DOWN, 5.5, t3, "clear", "M5"))
            tap_adapter(f"cu{k}{j}", xx, yy, "M5")
            bolt(f"B_upright{k}_foot{j}", "M5", 10, [(up.name, f"f{j}"), ("P01_base_adapter_plate", f"cu{k}{j}")], washer=False, group="G21 coffee uprights->adapter")
        for j, (xx, yy) in enumerate(((x0 + 15, yc + 10), (x1 - 15, yc - 10))):
            drill(up, Hole(f"t{j}", (xx, yy, zs - t - t3), UP, 4.5, t3, "clear", "M4"))
            drill(sh, Hole(f"u{k}{j}", (xx, yy, zs - t), UP, F.ISO["M4"]["tap"], t, "tap", "M4"))
            bolt(f"B_upright{k}_top{j}", "M4", 8, [(up.name, f"t{j}"), (sh.name, f"u{k}{j}")], washer=False, group="G22 shelf->uprights")
    # macchina (inviluppo da datasheet 119 x 320 x 229, con incavo tazza sotto l'erogatore)
    m = box(INI_X0 - 4.5, INI_X0 - 4.5 + INISSIA["W"], INI_Y0, INI_Y0 + INISSIA["D"], zs, zs + INISSIA["H"])
    z0r, z1r, y0r, y1r = INI_RECESS
    m = m.cut(box(INI_X0 - 6, INI_X0 + INISSIA["W"] + 1, y0r - 1, y1r, z0r, z1r))
    add(Part("S07_coffee_machine_inissia_EN80", m, "purchased", "purchased De'Longhi Inissia EN80 (or equivalent 24 V DC machine)",
             category="purchased", color=(0.2, 0.21, 0.22), explode=(-400, 0, 200), mass_kg=INISSIA["mass"] + 0.7,
             mass_src="De'Longhi 2.4 kg (SOURCED) + 0.7 kg water (tank 0.7 l)"))
    # trattenuta macchina: 2 squadrette PA12 sui piedini (non verificate a bulloni: incollate+M4)
    # navetta: guida MGN12 su rialzo, carrello, braccio-piatto, attuatore P16-150
    xr = COF_X
    rail_y0, rail_y1 = -322.0, -132.0
    riser = box(xr - 10, xr + 10, rail_y0, rail_y1, zs, zs + 4)
    rs = add(Part("P23_shuttle_rail_riser", riser, "EN AW-6082-T6", "CNC 20x4 flat bar", color=(0.6, 0.62, 0.65), explode=(-300, -120, 140)))
    rail = box(xr - 6, xr + 6, rail_y0, rail_y1, zs + 4, zs + 4 + MGN12["rail_h"])
    add(Part("S08_MGN12_rail_190", rail, "purchased", "purchased HIWIN MGN12 rail L=190", category="purchased", color=(0.5, 0.5, 0.52),
             explode=(-300, -120, 160), mass_kg=0.12, mass_src="HIWIN 0.65 kg/m (SECONDARY)"))
    for k, yy in enumerate((rail_y0 + 15, rail_y0 + 95, rail_y1 - 15)):
        drill(sh, Hole(f"r{k}", (xr, yy, zs), DOWN, F.ISO["M3"]["tap"], t, "tap", "M3"))
        drill(rs, Hole(f"r{k}", (xr, yy, zs + 4), DOWN, 3.4, 4, "clear", "M3"))

    for k, yy in enumerate((rail_y0 + 15, rail_y0 + 95, rail_y1 - 15)):
        drill(PARTS["S08_MGN12_rail_190"], Hole(f"r{k}", (xr, yy, zs + 4 + MGN12["rail_h"]), DOWN, 3.5, MGN12["rail_h"], "clear", "M3",
                                                cbore=(6.0, 3.5)))
        bolt(f"B_rail_{k}", "M3", 16, [("S08_MGN12_rail_190", f"r{k}"), (rs.name, f"r{k}"), (sh.name, f"r{k}")], group="G23 MGN12 rail->shelf",
             washer=False)

    # parti mobili (navetta in posizione "fuori": piatto a y=-240)
    off = 55.0
    yc = COF_Y_OUT - off
    zc0 = zs + 4 + MGN12["rail_h"]
    car = box(xr - 13.5, xr + 13.5, yc - 22.7, yc + 22.7, zc0 - 3, zs + 4 + MGN12["H"])
    add(Part("S09_MGN12H_carriage", car.cut(box(xr - 6.5, xr + 6.5, yc - 30, yc + 30, zc0 - 4, zc0)), "purchased", "purchased HIWIN MGN12H block",
             category="purchased", color=(0.5, 0.5, 0.52), explode=(-300, -200, 200), mass_kg=0.054, mass_src="HIWIN (SECONDARY)", motion="shuttle"))
    zt = zs + 4 + MGN12["H"]
    arm = box(xr - 13.5, xr + 13.5, yc - 22.7, COF_Y_OUT + 10, zt, zt + 4)
    plate = cyl(42, 4, (xr, COF_Y_OUT, SHUTTLE_PLATE_Z - 4))
    ring = cyl(36, 14, (xr, COF_Y_OUT, SHUTTLE_PLATE_Z)).cut(cyl(33, 16, (xr, COF_Y_OUT, SHUTTLE_PLATE_Z - 1)))
    lug = box(-308, xr - 13.5, yc - 6, yc + 6, zt, zt + 4)
    st = add(Part("P24_shuttle_cup_carrier", arm.fuse(plate.cut(box(-500, 500, -500, 500, 0, zt + 4)).fuse(box(xr - 42, xr + 42, COF_Y_OUT - 42, COF_Y_OUT + 42, zt, SHUTTLE_PLATE_Z).intersect(cyl(42, 100, (xr, COF_Y_OUT, zt))))).fuse(ring).fuse(lug),
                  "PA12 (SLS/MJF)", "MJF PA12: carriage arm + cup cradle (ring D72) + actuator lug", color=(0.86, 0.86, 0.84),
                  explode=(-300, -220, 260), motion="shuttle"))
    for k, (dx, dy) in enumerate(((-10, -7.5), (10, -7.5), (-10, 7.5), (10, 7.5))):
        drill(st, Hole(f"c{k}", (xr + dx, yc + dy, zt + 4), DOWN, 3.4, 4, "clear", "M3"))
        drill(PARTS["S09_MGN12H_carriage"], Hole(f"c{k}", (xr + dx, yc + dy, zt), DOWN, 2.5, 4, "tap", "M3"))
        bolt(f"B_carriage_{k}", "M3", 8, [(st.name, f"c{k}"), ("S09_MGN12H_carriage", f"c{k}")], group="G24 cup carrier->carriage", preload_frac=0.2)
    PARTS["S09_MGN12H_carriage"].tap_material = "S235 / 1.4301"
    # attuatore P16-150: corpo fisso verso +y dietro la macchina, stelo verso -y fino alla linguetta
    xa = -302.0
    za = zs + 16.0
    rod_end = yc
    body_y1 = rod_end + P16["closed"] + (COF_Y_IN - COF_Y_OUT)   # fissaggio posteriore
    bodyp = box(xa - P16["w"] / 2, xa + P16["w"] / 2, rod_end + 140 + 10, body_y1, za - P16["h"] / 2, za + P16["h"] / 2)
    rod = cyl(3, 140 + 4, (xa, rod_end + 6, za), (0, 1, 0))
    add(Part("S10_actuonix_P16_150", bodyp, "purchased", "purchased Actuonix P16-150-64-12-P", category="purchased", color=(0.15, 0.15, 0.16),
             explode=(-300, 150, 120), mass_kg=P16["mass"], mass_src="Actuonix datasheet 125 g (SOURCED)"))
    rp = add(Part("S10b_actuonix_rod", rod, "purchased", "actuator rod (moves with shuttle)", category="purchased", color=(0.7, 0.7, 0.7),
                  explode=(-300, -150, 120), mass_kg=0.01, motion="shuttle"))
    rp.check_interference = False          # telescopico: rientra nel corpo dell'attuatore per costruzione
    # supporto posteriore attuatore (squadretta 3 mm)
    bk = box(xa - 15, xa + 12, body_y1, body_y1 + 3, zs, za + 15).fuse(box(xa - 15, xa + 12, body_y1, body_y1 + 25, zs, zs + 3))
    ab = add(Part("P25_actuator_rear_bracket", bk, "EN AW-5754-H22", "laser cut + bent 3 mm sheet", color=(0.55, 0.57, 0.6),
                  explode=(-300, 200, 120)))
    for k, xx in enumerate((xa - 9, xa + 4)):
        drill(ab, Hole(f"f{k}", (xx, body_y1 + 15, zs + 3), DOWN, 4.5, 3, "clear", "M4"))
        drill(sh, Hole(f"ab{k}", (xx, body_y1 + 15, zs), DOWN, F.ISO["M4"]["tap"], t, "tap", "M4"))
        bolt(f"B_act_bracket_{k}", "M4", 10, [(ab.name, f"f{k}"), (sh.name, f"ab{k}")], group="G25 actuator bracket->shelf")
    # piastra elettronica dello zaino: appesa sotto la mensola con 4 distanziali M4 (dentro il guscio, tra i montanti):
    # DC-DC DDR-480C del caffe' + DC-DC 24 V sensori / 12 V CPU / 5 V + switch Ethernet (netlist_rbtheron.yaml)
    zp = 590.0
    x0p, x1p, y0p, y1p = -305.0, -175.0, -104.0, 161.0
    bpp = add(Part("P30_backpack_eplate", G.rounded_rect((x0p + x1p) / 2, (y0p + y1p) / 2, x1p - x0p, y1p - y0p, 2, zp, 6), "EN AW-5754-H22",
                   "laser cut 2 mm sheet + PEM nuts M4, hung under the coffee shelf", color=(0.55, 0.57, 0.6), explode=(-250, 0, -60)))
    for k, (xx, yy) in enumerate(((-297.0, -96.0), (-183.0, -96.0), (-297.0, 153.0), (-183.0, 153.0))):
        so = add(Part(f"P31_backpack_standoff_{k}", cyl(5, zs - t - (zp + 2), (xx, yy, zp + 2)), "EN AW-6082-T6",
                      f"turned D10 x {zs - t - zp - 2:.0f} mm, M4 male stud top / M4 tapped bottom", color=(0.7, 0.7, 0.72), explode=(-250, 0, -30)))
        drill(sh, Hole(f"bp{k}", (xx, yy, zs - t), UP, F.ISO["M4"]["tap"], t, "tap", "M4"))
        drill(so, Hole("bot", (xx, yy, zp + 2), UP, F.ISO["M4"]["tap"], 10, "tap", "M4"))
        so.tap_material = "EN AW-6082-T6"
        drill(bpp, Hole(f"s{k}", (xx, yy, zp), UP, 4.5, 2, "clear", "M4"))
        bolt(f"B_backpack_{k}", "M4", 8, [(bpp.name, f"s{k}"), (so.name, "bot")], group="G31 backpack e-plate->standoffs")
    zc_ = zp + 2
    purchased_box("E11_dcdc_DDR480C_coffee", -303, -303 + 125.2, -100, -100 + 129.2, zc_, zc_ + 85.5, DCDC["mass"],
                  "Mean Well DDR-480C-24 (coffee bus), lying (SOURCED dims)", (0.75, 0.75, 0.78))
    purchased_box("E12_dcdc_S24_CPU_5V", -303, -243, 35, 150, zc_, zc_ + 45, 0.75, "ESTIMATE: 24 V sensors + 12 V CPU + 5 V DC-DCs", (0.75, 0.75, 0.78))
    purchased_box("E13_ethernet_switch", -238, -208, 35, 135, zc_, zc_ + 70, 0.3, "ESTIMATE 5-8 port 24 V DIN switch", (0.2, 0.2, 0.22))
    # porta-bicchieri: colonnina + anello (PA12) sulla lingua della mensola
    sx_, sy_ = COF_STACK
    stem = cyl(15, COF_STACK_Z, (sx_, sy_, zs)).fuse(cyl(30, 14, (sx_, sy_, zs)))
    ring = cyl(40, 45, (sx_, sy_, zs + COF_STACK_Z)).cut(cyl(37, 47, (sx_, sy_, zs + COF_STACK_Z + 3)))
    ring = ring.cut(box(sx_ - 45, sx_ - 16, sy_ - 22, sy_ + 22, zs + COF_STACK_Z - 1, zs + COF_STACK_Z + 50)).cut(box(sx_ + 16, sx_ + 45, sy_ - 22, sy_ + 22, zs + COF_STACK_Z - 1, zs + COF_STACK_Z + 50))   # feritoie per le dita (presa lungo x)
    ch = add(Part("P26_cup_stack_holder", stem.fuse(ring).fuse(box(sx_ - 3, sx_ + 3, sy_ - 37, sy_ + 37, zs + 4, zs + COF_STACK_Z)), "PA12 (SLS/MJF)",
                  "MJF PA12, D80 ring 45 mm with 44 mm finger slots on +-x, stem, 3 inserts M4", color=(0.86, 0.86, 0.84), explode=(-200, -200, 180)))
    for k, ang in enumerate((0, 120, 240)):
        x, y = sx_ + 22 * math.cos(math.radians(ang)), sy_ + 22 * math.sin(math.radians(ang))
        drill(sh, Hole(f"cs{k}", (x, y, zs - t), UP, 4.5, t, "clear", "M4"))
        drill(ch, Hole(f"cs{k}", (x, y, zs), UP, F.INSERTS["M4"]["hole"], 11.0, "insert", "M4"))
    for k in range(3):
        bolt(f"B_cupholder_{k}", "M4", 16, [(sh.name, f"cs{k}"), (ch.name, f"cs{k}")], female="insert", group="G26 cup holder->shelf", preload_frac=0.07)
    # guscio dello zaino: scatola arrotondata aperta davanti (la chiude la cintura) e sul lato erogatore
    tt = 2.0
    xo0, xo1, yo0, yo1, zo0, zo1 = -330.0, -166.0, -135.0, 205.0, DECK_TOP + 4.0, COF_SH + 252.0   # 450 .. 942
    o = cq.Workplane("XY", origin=((xo0 + xo1) / 2, (yo0 + yo1) / 2, zo0)).rect(xo1 - xo0, yo1 - yo0).extrude(zo1 - zo0).edges("|Z").fillet(8).edges(">Z").fillet(6).val()
    i = cq.Workplane("XY", origin=((xo0 + xo1) / 2, (yo0 + yo1) / 2, zo0 - 1)).rect(xo1 - xo0 - 2 * tt, yo1 - yo0 - 2 * tt).extrude(zo1 - zo0 - tt + 1).edges("|Z").fillet(5).val()
    s = o.cut(i)
    s = s.cut(box(xo1 - 30, xo1 + 10, yo0 + 25, yo1 - 25, zo0 - 1, zo1 - 25))                       # fronte aperto verso la colonna
    s = s.cut(box(INI_X0 - 2, INI_X0 + INISSIA["W"] + 2, yo0 - 5, yo0 + 10, zs - 10, zs + INISSIA["H"] + 2))   # lato erogatore aperto
    s = s.cut(box(-320, -230, yo0 - 5, yo0 + 10, zs - 40, zs + 30))                                 # passaggio attuatore/navetta
    s = s.cut(box(-316, -240, -40, 200, zo1 - 10, zo1 + 5))                                         # sportello serbatoio (coperchio a parte)
    s = s.cut(box(INI_X0 - 8, xo1 + 5, yo0 - 5, -45, zs + INISSIA["H"] - 30, zo1 + 5))          # testa/pulsanti accessibili dall'alto (pressione del pulsante)
    hz = add(Part("SH06_coffee_housing", s, "PA12 (SLS/MJF)", "SLS PA12 3 mm (2 pieces), hangs on the shelf edge with 4 M4 inserts",
                  category="shell", color=(0.86, 0.86, 0.84), explode=(-450, 0, 250)))
    for k, (x, y) in enumerate(((-312.0, -60.0), (-312.0, 120.0), (-300.0, 192.0))):
        lug = box(x - 6, x + 6, y - 6, y + 6, zs - t - 10, zs - t)
        lug = lug.fuse(box(xo0, x, y - 6, y + 6, zs - t - 10, zs - t)) if k < 2 else lug.fuse(box(x - 6, x + 6, y, yo1, zs - t - 10, zs - t))
        hz.shape = hz.shape.fuse(lug)
        drill(hz, Hole(f"hz{k}", (x, y, zs - t - 10), UP, 4.5, 10, "clear", "M4"))
        drill(sh, Hole(f"hz{k}", (x, y, zs - t), UP, F.ISO["M4"]["tap"], t, "tap", "M4"))
        bolt(f"B_housing_{k}", "M4", 16, [(hz.name, f"hz{k}"), (sh.name, f"hz{k}")], group="G27 housing->shelf", preload_frac=0.3)
    return sh


# ====================================================================== build all
def build():
    PARTS.clear()
    BOLTS.clear()
    ADAPTER_KEEP.clear()
    base_envelope()
    adapter_plate()
    column()
    body_link0()
    power()
    scanner_pods()
    deck_cover()
    column_covers()
    torso_shell()
    head()
    gemini()
    chest_tray()
    coffee()
    for (x0, x1, y0, y1) in ((-266, -190, -138, -98), (-266, -190, 155, 195)):
        ADAPTER_KEEP.append((x0, x1, y0, y1))
    lighten_adapter()
    return PARTS, BOLTS


if __name__ == "__main__":
    import time
    t0 = time.time()
    P, B = build()
    print(len(P), "parts", len(B), "bolts", f"{time.time() - t0:.1f}s")
    for n, p in P.items():
        print(f"{n:45s} {p.mass():7.3f} kg valid={p.shape.isValid()}")
