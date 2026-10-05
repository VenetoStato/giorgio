"""Superstructure (cad/out/stl, unchanged parts) on the new AMR (rev B2, fixed deck): interference, keep-outs and mass properties.
Writes amr/out/integration.json (rotating mass/CoG per item, clearances)."""
import json, math, sys
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
from amr_params import KEEP_PREFIX
HERE = Path(__file__).parent
CAD = HERE.parent / "cad" / "out"
mp = json.load(open(CAD / "mass_properties.json"))["per_item"]
meta = json.load(open(HERE / "out" / "parts.json"))

sup = {}
for f in sorted((CAD / "stl").glob("*.stl")):
    n = f.stem
    if n.startswith(KEEP_PREFIX) and not n.startswith("tnut"):
        sup[n] = trimesh.load(f)
# masses: per_item (CAD), arms from the 'arms' group (home pose) spread by link volume
arms = json.load(open(CAD / "mass_properties.json"))["arms"]
arm_links = [n for n in sup if n.startswith("openarm_")]
vol = {n: abs(sup[n].volume) if sup[n].is_volume else sup[n].convex_hull.volume for n in arm_links}
rows = []
for n, m in sup.items():
    mass = mp.get(n) if not n.startswith("openarm_") else arms["mass_kg"] * vol[n] / sum(vol.values())
    if mass is None:
        continue
    c = m.center_mass if m.is_volume else m.bounds.mean(axis=0)
    rows.append((n, float(mass), np.array(c, float)))
M = sum(r[1] for r in rows)
C = sum(r[1] * r[2] for r in rows) / M
base_fixed = [(x["name"], x["mass_kg"], np.array(x["com_mm"])) for x in meta if x["group"] in ("base", "waist")]
rot_amr = [(x["name"], x["mass_kg"], np.array(x["com_mm"])) for x in meta if x["group"] == "waist_rot"]

# collision: rotating set (superstructure + waist_rot) vs fixed AMR parts, every 15 deg
import fcl  # noqa  (python-fcl, used through trimesh)
fixed = trimesh.collision.CollisionManager()
for x in meta:
    if x["group"] in ("base", "waist") and x["category"] != "harness":
        fixed.add_object(x["name"], trimesh.load(HERE / "out" / "stl" / x["file"]))
rot_meshes = dict(sup)
for x in meta:
    if x["group"] == "waist_rot":
        rot_meshes[x["name"]] = trimesh.load(HERE / "out" / "stl" / x["file"])
hits, dmin = [], 1e9
for yaw in (0,):                 # rev B: no waist joint, superstructure fixed
    R = trimesh.transformations.rotation_matrix(math.radians(yaw), [0, 0, 1])
    for n, m in rot_meshes.items():
        mm = m.copy(); mm.apply_transform(R)
        hit, names = fixed.in_collision_single(mm, return_names=True)
        names = sorted(set(names) - {"A02_top_deck"})       # parts bolted ON the deck touch it (contact face, not interference)
        if hit and names:        # plate/hub on the bearing inner ring = bolted contact faces, not an interference
            hits.append((yaw, n, names))
        else:
            d = fixed.min_distance_single(mm)
            dmin = min(dmin, d)
# rev B2: keep-out check solids (out/keepout, out/keepouts.json) against the superstructure, and the clearance of the
# deck-mounted Jetson cover K06 / Jetson E51 to the superstructure parts around it
ko_hits = []
kom = trimesh.collision.CollisionManager()
for k in json.load(open(HERE / "out" / "keepouts.json")):
    kom.add_object(k["name"], trimesh.load(HERE / "out" / "keepout" / k["file"]))
for n, m in sup.items():
    hit, names = kom.in_collision_single(m, return_names=True)
    if hit:
        ko_hits.append((n, sorted(names)))
jet = {}
for nm in ("K06_jetson_cover", "E51_jetson_orin_nx_carrier"):
    mj = trimesh.load(HERE / "out" / "stl" / f"{nm}.stl")
    one = trimesh.collision.CollisionManager(); one.add_object(nm, mj)
    jet[nm] = {n: round(float(one.min_distance_single(sup[n])), 1) for n in sup
               if n.startswith(("P22", "P29", "S01", "SH02", "SH06", "SH03", "SH04", "SH05"))}
# swept radius of the rotating set (plan)
rmax = max(np.max(np.hypot(m.vertices[:, 0], m.vertices[:, 1])) for m in rot_meshes.values())
out = dict(superstructure_kept_kg=round(M, 2), superstructure_com_mm=[round(v, 1) for v in C],
           waist_rot_amr_kg=round(sum(r[1] for r in rot_amr), 2),
           rotating_total_kg=round(M + sum(r[1] for r in rot_amr), 2),
           rotating_com_mm=[round(v, 1) for v in (M * C + sum(r[1] * r[2] for r in rot_amr)) / (M + sum(r[1] for r in rot_amr))],
           base_fixed_kg=round(sum(r[1] for r in base_fixed), 2),
           base_fixed_com_mm=[round(v, 1) for v in sum(r[1] * r[2] for r in base_fixed) / sum(r[1] for r in base_fixed)],
           rotating_swept_radius_mm=round(float(rmax), 1), collisions=hits, min_clearance_mm=round(float(dmin), 1),
           keepout_hits_superstructure=ko_hits, jetson_cover_clearance_mm=jet,
           items=[(n, round(m_, 3), [round(v, 1) for v in c]) for n, m_, c in rows])
json.dump(out, open(HERE / "out" / "integration.json", "w"), indent=1)
print({k: v for k, v in out.items() if k != "items"})
