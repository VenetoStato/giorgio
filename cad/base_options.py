"""Static mass / CoG / tipping of the current Giorgio superstructure on alternative AgileX bases.
Same method as validate.py (rigid body, quasi-static tip about the support-polygon edge).

    cd ~/giorgio_sim/cad && .env/bin/python base_options.py

The superstructure is taken from the validated Tracer design (mass rows of every part, arms in home pose) and
translated vertically by (deck height - 169 mm). The adapter plate is assumed to keep the same mass on every base.
Base data and its source/confidence: see BASES below and BASE_OPTIONS.md.
"""
import json
import sys

import numpy as np

import model as M
import validate as V
from params import *  # noqa: F401,F403

# deck = top of the mounting rails (mm); support = half wheelbase x, half track y of the wheel contact polygon (mm);
# cog_z = base own CoG height (ESTIMATE ~0.45 x height when not published)
BASES = {
    "Tracer 2.0": dict(mass=55.0, deck=169.0, cog_z=80.0, support=(281.0, 255.0), payload=100.0),
    # Ranger Mini 3.0 manual: 75 kg, rails top 345, CoG 213 above ground (Fig 2.2), wheel centres 494 x 364, 120 kg
    "Ranger Mini 3.0 (own 48 V pack kept)": dict(mass=75.0, deck=345.0, cog_z=213.0, support=(247.0, 182.0), payload=120.0,
                                              drop=("S03", "P10", "B_charge")),
    "Ranger Mini 3.0 (powered from base battery)": dict(mass=75.0, deck=345.0, cog_z=213.0, support=(247.0, 182.0), payload=120.0,
                                                     drop=("S03", "P10", "B_charge", "E01", "P03", "P04", "P05", "B_batt", "B_hold", "E09")),
    # Ranger manual: 100 kg curb (135 kg single battery also stated: 100 used = worse for tipping), rails top ~536 (drawing), 890-900 x 560, 150 kg
    "Ranger Mini 3.0 (base battery, shoulders kept, fixed column)": dict(mass=75.0, deck=345.0, cog_z=213.0, support=(247.0, 182.0), payload=120.0,
        keep_shoulders=True, drop=("S03", "P10", "B_charge", "E01", "P03", "P04", "P05", "B_batt", "B_hold", "E09", "S01", "P13", "P14", "P15", "B_colfoot")),
    "Ranger (base battery, shoulders kept, no column)": dict(mass=100.0, deck=536.0, cog_z=250.0, support=(450.0, 280.0), payload=150.0,
        keep_shoulders=True, drop=("S03", "P10", "B_charge", "E01", "P03", "P04", "P05", "B_batt", "B_hold", "E09", "S01", "P13", "P14", "P15", "W01", "B_colfoot", "SH02")),
    "Ranger (powered from base battery)": dict(mass=100.0, deck=536.0, cog_z=250.0, support=(450.0, 280.0), payload=150.0,
                                            drop=("S03", "P10", "B_charge", "E01", "P03", "P04", "P05", "B_batt", "B_hold", "E09")),
}


def rows_for(config="both"):
    parts, bolts = M.build()
    V.add_bolt_parts(parts, bolts)
    st = json.loads((V.DATA / "sim_static.json").read_text())
    arm_rows = [(f"arm:{b}", v[0], np.array(v[1:]), "lift") for b, v in st["arm_body_mass_com"].items()]
    misc = [("wiring", 3.0, np.array([-50.0, 0, 230.0]), "")]
    rows = V.mass_props(parts, arm_rows + misc)
    tray = ("P19", "P20", "S06", "tnut_tray", "B_tray_post")
    coffee = ("P21", "P22", "P23", "P24", "P25", "P26", "S07", "S08", "S09", "S10", "SH06", "B_upright", "B_rail_", "B_carriage", "B_act_", "B_cupholder", "B_housing")
    if config == "barista":
        rows = [r for r in rows if not r[0].startswith(tray)]
    if config == "logistics":
        rows = [r for r in rows if not r[0].startswith(coffee)]
    return rows


def evaluate(base, rows, tray_payload=True):
    b = BASES[base]
    dz = b["deck"] - TR_H
    drop = tuple(b.get("drop", ()))
    keep = b.get("keep_shoulders", False)
    ext = []
    for n, m, c, mo in rows:
        if n == "tracer2_base" or (drop and n.startswith(drop)):
            continue
        c = np.asarray(c, float)
        # keep_shoulders: torso/arms/coffee stay at the validated heights (task reach unchanged, column shortened by dz,
        # no height adjustment); only the base-level parts (CoG below 400 mm) rise with the deck
        if not keep or (c[2] < 400 and not n.startswith(("S02", "P09"))):
            c = c + np.array([0, 0, dz])
        if keep and mo == "lift":
            mo = ""
        ext.append((n, m, c, mo))
    if tray_payload:
        ext.append(("tray payload", TRAY_PAYLOAD, np.array([BUF_X, 0.0, BUF_Z + 40 + (0 if keep else dz)]), "lift"))
    sup = sum(r[1] for r in ext)
    out = {}
    cases = {
        "nominal": ([], 0.0, False),
        "work 2x4.1 kg": ([("pL", ARM_PAYLOAD_NOM, (300.0, 150.0, 1030.0)), ("pR", ARM_PAYLOAD_NOM, (300.0, -150.0, 1030.0))], 0.0, False),
        "worst lift150 arms fwd 2x6 kg": ([("pL", ARM_PAYLOAD_PEAK, (550.0, 250.0, 1100.0)), ("pR", ARM_PAYLOAD_PEAK, (550.0, -250.0, 1100.0))], STROKE, True),
    }
    for nm, (pl, lift, fwd) in cases.items():
        rr = [(n, m, c + (np.array([150.0, 0, 0]) if (fwd and n.startswith("arm:")) else 0), mo) for n, m, c, mo in ext]
        rr += [(n, m, np.array(c) + np.array([0, 0, 0 if keep else dz]), "lift") for n, m, c in pl]
        rr.append(("base", b["mass"], np.array([0.0, 0.0, b["cog_z"]]), ""))
        m, c = V.total(rr, lift)
        t = V.tipping(m, c, b["support"])
        out[nm] = dict(mass=round(m, 1), cog=np.round(c, 0).tolist(), tip=[round(t[k], 2) for k in ("fwd", "back", "left", "right")])
    ext_m, ext_c = V.total(ext, 0.0)
    return dict(superstructure_plus_tray_kg=round(sup, 1), plus_arm_objects_kg=round(sup + 2 * PRODUCT_PAYLOAD_ARM, 1),
                payload_limit=b["payload"], margin_kg=round(b["payload"] - sup - 2 * PRODUCT_PAYLOAD_ARM, 1),
                ext_cog=np.round(ext_c, 0).tolist(), cases=out)


if __name__ == "__main__":
    extra = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    BASES.update(extra)
    res = {}
    for cfg in ("both", "barista", "logistics"):
        rows = rows_for(cfg)
        for base in BASES:
            res[f"{base} | {cfg}"] = evaluate(base, rows, tray_payload=(cfg != "barista"))
    print(json.dumps(res, indent=1))
    (V.OUT / "base_options.json").write_text(json.dumps(res, indent=1))
