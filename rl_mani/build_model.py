"""Costruisce l'MJCF per RL: mano ORCA v2 destra palmo in su + cubo libero.

- polso bloccato (giunto e attuatore rimossi): 16 DOF dita attuati
- collisioni: mesh originali solo visive, collisioni con primitive (capsule/box)
  stimate dalle mesh (PCA) -> veloce su mujoco_warp
Uscita: orca_cubo_rl.xml (path mesh assoluti, riutilizzabile in Blender).
"""
import os
import numpy as np
import mujoco

ORCA = "/home/gpitton/giorgio_sim/third_party/orcahand_description/v2"
QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, "orca_cubo_rl.xml")
CUBO = 0.0275  # semi-lato cubo nominale (5.5 cm)

XML = f"""
<mujoco model="orca_cubo_rl">
  <include file="{ORCA}/models/assets/options.xml"/>
  <compiler meshdir="{ORCA}/"/>
  <include file="{ORCA}/models/mjcf/orcahand_right.mjcf"/>
  <worldbody>
    <body name="palmo_su" pos="0 0 0.25" euler="1.5708 0 0">
      <body name="right_mount" pos="0 0 0" euler="1.5708 0 0">
        <include file="{ORCA}/models/mjcf/orcahand_right_body.xml"/>
      </body>
    </body>
  </worldbody>
</mujoco>
"""


def fit_primitive(m, d, g):
    """Capsula (dita) o box (palmo/avambraccio) nel frame del body."""
    mid = m.geom_dataid[g]
    a, n = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
    v = m.mesh_vert[a:a + n]
    w = v @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]
    b = m.geom_bodyid[g]
    loc = (w - d.xpos[b]) @ d.xmat[b].reshape(3, 3)
    c = loc.mean(0)
    _, _, vt = np.linalg.svd(loc - c, full_matrices=False)
    p = (loc - c) @ vt.T
    lo, hi = p.min(0), p.max(0)
    ctr = c + ((lo + hi) / 2) @ vt
    half = (hi - lo) / 2
    return b, ctr, vt, half


def build():
    spec = mujoco.MjSpec.from_string(XML)
    # polso bloccato
    spec.delete(spec.actuator("right_wrist_actuator"))
    spec.delete(spec.joint("right_wrist"))
    m = spec.compile()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)

    prims = []
    for g in range(m.ngeom):
        if m.geom_contype[g] == 0 or m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        prims.append((m.geom(g).name, *fit_primitive(m, d, g)))
    # tutte le mesh diventano solo visive
    for gs in spec.geoms:
        if gs.type == mujoco.mjtGeom.mjGEOM_MESH:
            gs.contype = 0
            gs.conaffinity = 0
            gs.group = 2
    for _, b, ctr, vt, half in prims:
        bname = m.body(b).name
        body = spec.body(bname)
        big = any(k in bname for k in ("Carpals", "ForeArm", "TopTower"))
        if big:
            R = vt.T.copy()
            if np.linalg.det(R) < 0:
                R[:, 2] *= -1
            q = np.zeros(4)
            mujoco.mju_mat2Quat(q, R.flatten())
            body.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=half * 0.97, pos=ctr,
                          quat=q, contype=1, conaffinity=1, group=3,
                          rgba=[0.2, 0.6, 1, 0.3], friction=[1.0, 0.005, 0.0001],
                          condim=3, name=f"col_{bname}")
        else:
            r = float(np.mean(half[1:])) * 0.95
            L = max(half[0] - r, 0.002)
            ax = vt[0]
            ft = np.concatenate([ctr - ax * L, ctr + ax * L])
            body.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[r, 0, 0], fromto=ft,
                          contype=1, conaffinity=1, group=3, rgba=[0.2, 0.6, 1, 0.3],
                          friction=[1.0, 0.005, 0.0001], condim=3,
                          name=f"col_{bname}")

    # cubo libero con facce colorate (marcatori solo visivi)
    cubo = spec.worldbody.add_body(name="cubo", pos=[0, 0, 0.35])
    cubo.add_freejoint(name="cubo_libero")
    cubo.add_geom(name="cubo_col", type=mujoco.mjtGeom.mjGEOM_BOX, size=[CUBO] * 3,
                  mass=0.06, rgba=[0.95, 0.93, 0.88, 1], friction=[1.0, 0.005, 0.0001],
                  condim=4, contype=1, conaffinity=1)
    colori = [[0.85, 0.2, 0.2, 1], [0.2, 0.7, 0.3, 1], [0.2, 0.4, 0.9, 1],
              [0.95, 0.75, 0.1, 1], [0.6, 0.3, 0.8, 1], [0.1, 0.75, 0.8, 1]]
    k = 0
    for ax in range(3):
        for s in (1, -1):
            pos = [0, 0, 0]
            pos[ax] = s * CUBO
            size = [CUBO * 0.7] * 3
            size[ax] = 0.0008
            cubo.add_geom(name=f"faccia{k}", type=mujoco.mjtGeom.mjGEOM_BOX, size=size,
                          pos=pos, rgba=colori[k], contype=0, conaffinity=0, mass=0,
                          group=1)
            k += 1
    # pavimento chiaro (solo visivo), luci, camera
    spec.worldbody.add_geom(name="pavimento", type=mujoco.mjtGeom.mjGEOM_PLANE,
                            size=[2, 2, 0.05], rgba=[0.93, 0.93, 0.92, 1],
                            contype=0, conaffinity=0)
    spec.worldbody.add_light(pos=[0.3, -0.4, 1.0], dir=[-0.3, 0.4, -1],
                             diffuse=[0.7, 0.7, 0.7], castshadow=True)
    spec.worldbody.add_light(pos=[-0.4, 0.3, 0.9], dir=[0.4, -0.3, -1],
                             diffuse=[0.35, 0.35, 0.35], castshadow=False)
    # sfondo chiaro e camera per i video
    spec.add_texture(name="cielo", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX,
                     builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                     rgb1=[1, 1, 1], rgb2=[0.86, 0.88, 0.9], width=512, height=512)
    spec.worldbody.add_camera(name="vista", pos=[0.22, -0.42, 0.52],
                              xyaxes=[0.88, 0.47, 0, -0.27, 0.5, 0.82], fovy=40)
    spec.option.timestep = 0.005
    spec.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    spec.option.impratio = 2.0
    spec.visual.global_.offwidth = 1920
    spec.visual.global_.offheight = 1080
    spec.visual.headlight.ambient = [0.35, 0.35, 0.35]
    m2 = spec.compile()
    xml = spec.to_xml()
    with open(OUT, "w") as f:
        f.write(xml)
    return m2


if __name__ == "__main__":
    m = build()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    print("nq", m.nq, "nu", m.nu, "ngeom", m.ngeom, "->", OUT)
    pb = m.body("right_R-Carpals_8d1f1041").id
    print("carpo", d.xpos[pb].round(3))
    for n in ["right_I-FingerTipAssembly_ec49c16c", "right_T-DP_b7429e50", "right_P-FingerTipAssembly_cd219176"]:
        print(n[:20], d.xpos[m.body(n).id].round(3))
    g = m.geom("col_right_R-Carpals_8d1f1041").id
    print("box palmo pos", d.geom_xpos[g].round(3), "size", m.geom_size[g].round(3),
          "\n", d.geom_xmat[g].reshape(3, 3).round(2))
