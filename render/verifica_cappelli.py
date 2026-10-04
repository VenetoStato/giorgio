"""Controllo collisioni cappello / testa (lanciato dentro blender_render.py con --debug_py).
Volume della testa = involucro convesso di guscio + visiera + pannello LED (il guscio e' cavo, l'involucro no).
Per ogni oggetto del cappello conta i vertici che entrano nella testa piu' di TOL e la profondita' massima.
Stampa CAPPELLO_OK se nessun vertice entra piu' di TOL."""
import bmesh
import bpy
import numpy as np

TOL = 0.0008
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for nm in ("head_shell", "face_glass", "led_panel"):
    o = bpy.data.objects.get(nm)
    if o is None or o.type != "MESH":
        continue
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    pts += [(o.matrix_world @ v.co)[:] for v in me.vertices]
    oe.to_mesh_clear()
bm = bmesh.new()
for p in pts:
    bm.verts.new(p)
bmesh.ops.convex_hull(bm, input=bm.verts)
bm.faces.ensure_lookup_table()
P = np.array(pts); cen = P.mean(0)
planes = []
for f in bm.faces:
    if not f.is_valid or len(f.verts) < 3:
        continue
    n = np.array(f.normal[:]); v0 = np.array(f.verts[0].co[:])
    if np.linalg.norm(n) < 1e-9:
        continue
    if np.dot(cen - v0, n) > 0:
        n = -n
    planes.append((n, np.dot(n, v0)))
N = np.array([p[0] for p in planes]); D = np.array([p[1] for p in planes])
print("TEST centro dentro:", bool(np.all(N @ cen - D < 0)), "| 30 cm sopra dentro:", bool(np.all(N @ (cen + [0, 0, 0.3]) - D < 0)))
worst = 0.0; tot = 0; per = {}
for o in [o for o in bpy.data.objects if o.name.startswith("hat_") and o.type in ("MESH", "CURVE")]:
    oe = o.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    V = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices]); oe.to_mesh_clear()
    if not len(V):
        continue
    s = V @ N.T - D                                      # >0 fuori da quel piano
    depth = -s.max(1)                                    # >0 = dentro l'involucro, di quanto
    bad = depth > TOL
    if bad.any():
        print(f"COLLISIONE {o.name}: {int(bad.sum())} vertici dentro la testa, max {depth.max() * 1000:.1f} mm")
        tot += int(bad.sum()); worst = max(worst, float(depth.max()))
    per[o.name] = float(-depth.max()) if len(depth) else 0.0
gap = min(per.values()) if per else 0
print("CAPPELLO_OK (gioco minimo %.1f mm)" % (gap * 1000) if tot == 0 else f"CAPPELLO_KO {tot} vertici, peggiore {worst * 1000:.1f} mm")
