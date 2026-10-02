"""Giorgio-P con componenti REALI, assemblati in MuJoCo (MjSpec):

  - braccia: Enactic OpenArm 2.0 bimanuale, MJCF ufficiale (Apache 2.0): mesh, masse, motori Damiao
    DM8009/DM4340/DM4310 con le loro coppie massime (40/27/7 Nm), busto "body_link0" originale
  - mani: Inspire RH56DFTP destra/sinistra (URDF Unitree, mesh originali), 6 motori, giunti accoppiati
  - testa: Intel RealSense D435i (RGB 69x42 gradi) su collo a 2 assi; polsi: RealSense D405
  - base: AMR classe AgileX Tracer (ingombro ~0.69 x 0.57 m) + colonna elevabile (corsa 0.40 m)
  - sicurezza: 2 SICK nanoScan3 (275 gradi) sugli spigoli opposti, a 18 cm da terra

Il "rework estetico" sono solo gusci e vernice sopra i pezzi veri (geom solo visivi, senza massa).
"""
import math
import re
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
OA = HERE / "third_party/openarm_mujoco/v2"
INSPIRE = Path.home() / "unitree_ros/robots/g1_description"
LEAP = HERE / "third_party/mujoco_menagerie/leap_hand"
LEAP_CENTER = (0.045, 0.0, -0.058)   # centro flacone nel frame "mano" H (x dita, -z chiusura), stimato dalla cinematica


def leap_frame(side):
    """Frame canonico H della LEAP nel frame del corpo palm: x = direzione dita, -z = direzione di chiusura.
    Ritorna (R_palm_H, origine H nel palm)."""
    m = mujoco.MjModel.from_xml_path(str(LEAP / f"{side}_hand.xml")); d = mujoco.MjData(m)
    pal = m.body("palm").id
    def loc(name):
        mujoco.mj_forward(m, d)
        return (d.geom_xpos[m.geom(name).id] - d.xpos[pal]) @ d.xmat[pal].reshape(3, 3)
    tip_o = loc("mf_tip")
    base = (d.xpos[m.body("mf_bs").id] - d.xpos[pal]) @ d.xmat[pal].reshape(3, 3)
    for f in ("if", "mf", "rf"):
        d.joint(f + "_mcp").qpos = 1.2
    tip_c = loc("mf_tip")
    x = tip_o - base; x /= np.linalg.norm(x)
    c = tip_c - tip_o; zc = c - (c @ x) * x; z = -zc / np.linalg.norm(zc)
    y = np.cross(z, x)
    mujoco.mj_resetData(m, d); mujoco.mj_forward(m, d)
    return np.stack([x, y, z], 1), base, d.xpos[pal].copy(), d.xmat[pal].reshape(3, 3).copy()

LOOKS = {   # corazza, accento, scuro (giunti), visiera, neon ambiente
    "eva":   dict(armor=(0.34, 0.16, 0.52), accent=(0.45, 0.95, 0.15), dark=(0.10, 0.09, 0.12), visor=(1.0, 0.42, 0.05), neon=((0.9, 0.2, 0.9), (0.45, 0.95, 0.15))),
    "akira": dict(armor=(0.78, 0.06, 0.05), accent=(0.95, 0.95, 0.92), dark=(0.09, 0.09, 0.10), visor=(0.2, 0.9, 1.0), neon=((1.0, 0.15, 0.1), (0.2, 0.9, 1.0))),
    "gits":  dict(armor=(0.80, 0.77, 0.70), accent=(0.20, 0.55, 1.00), dark=(0.16, 0.17, 0.19), visor=(1.0, 0.15, 0.15), neon=((0.2, 0.55, 1.0), (0.1, 0.9, 0.7))),
    "blame": dict(armor=(0.30, 0.31, 0.32), accent=(0.85, 0.86, 0.82), dark=(0.05, 0.05, 0.06), visor=(0.92, 0.96, 1.0), neon=((0.7, 0.75, 0.8), (0.95, 0.5, 0.2))),
    "cyber": dict(armor=(0.07, 0.07, 0.08), accent=(0.98, 0.90, 0.08), dark=(0.20, 0.20, 0.22), visor=(0.1, 0.95, 0.95), neon=((0.98, 0.9, 0.08), (0.1, 0.95, 0.95))),
}

# dimensioni (m)
AMR_L, AMR_W, AMR_H = 0.702, 0.61, 0.25        # AgileX Tracer 2.0: 702 x 610 x 169 mm + piastra e carter (0.25 m)
AMR_MASS = 55.0                               # Tracer 2.0: 54-56 kg
COLUMN_STROKE = 0.40
SCAN_Z = 0.18
SCANNERS = [((AMR_L / 2 - 0.03, -(AMR_W / 2 - 0.03)), -math.pi / 4), ((-(AMR_L / 2 - 0.03), AMR_W / 2 - 0.03), 3 * math.pi / 4)]
PED_TOP = 0.698                               # quota spalle OpenArm sopra la base del busto originale
GROUP_ENV, GROUP_HUMAN, GROUP_ROBOT = 0, 1, 2  # i raggi degli scanner vedono solo i gruppi 0 e 1


def _q(R):
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, np.asarray(R, float).reshape(-1))
    return q


def _hand_spec(side):
    """mano Inspire RH56DFTP da URDF; side = 'right'|'left'"""
    src = (INSPIRE / f"inspire_hand/FTP_{side}_hand.urdf").read_text()
    mimic = re.findall(r'<joint name="([^"]+)"[^>]*>(?:(?!</joint>).)*?<mimic joint="([^"]+)" multiplier="([^"]+)"', src, flags=re.S)
    src = re.sub(r"<mujoco>.*?</mujoco>", "", src, flags=re.S)
    src = re.sub(r"(<robot[^>]*>)", r'\1<mujoco><compiler meshdir="%s" discardvisual="true" fusestatic="false" strippath="true"/></mujoco>'
                 % (INSPIRE / "meshes"), src, count=1)
    tmp = HERE / f"robots/_inspire_{side}.urdf"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(src)
    return mujoco.MjSpec.from_file(str(tmp)), mimic


def build(look="eva", hands="inspire", humans=2, fixed_base=True):
    LK = LOOKS[look]
    sp = mujoco.MjSpec()
    sp.compiler.degree = False
    sp.option.timestep = 0.002
    sp.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    sp.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    sp.option.impratio = 10
    sp.visual.global_.offwidth, sp.visual.global_.offheight = 1920, 1080
    sp.visual.headlight.ambient = [0.25, 0.22, 0.3]
    sp.visual.headlight.diffuse = [0.5, 0.5, 0.55]
    sp.visual.quality.shadowsize = 4096
    sp.visual.rgba.haze = [0.03, 0.02, 0.05, 1]
    sp.stat.center = [0.4, 0, 0.9]
    sp.stat.extent = 3.0

    sp.add_texture(name="sky", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX, builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                   rgb1=[0.05, 0.03, 0.09], rgb2=[0.0, 0.0, 0.0], width=512, height=512)
    sp.add_texture(name="floor", type=mujoco.mjtTexture.mjTEXTURE_2D, builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                   rgb1=[0.06, 0.06, 0.075], rgb2=[0.085, 0.085, 0.1], mark=mujoco.mjtMark.mjMARK_EDGE, markrgb=[0.2, 0.15, 0.3],
                   width=512, height=512)
    mat_floor = sp.add_material(name="floor", texrepeat=[8, 8], reflectance=0.15)
    mat_floor.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "floor"

    def mat(name, rgb, refl=0.1, emission=0.0, spec=0.4, shin=0.5):
        sp.add_material(name=name, rgba=list(rgb) + [1.0], reflectance=refl, emission=emission, specular=spec, shininess=shin)

    mat("armor", LK["armor"], 0.15, spec=0.6, shin=0.7); mat("accent", LK["accent"], emission=0.6)
    mat("dark", LK["dark"], 0.05); mat("visor", LK["visor"], 0.3, emission=0.9)
    mat("neon0", LK["neon"][0], emission=1.0); mat("neon1", LK["neon"][1], emission=1.0)
    mat("bench", (0.11, 0.115, 0.13), 0.1); mat("steel", (0.55, 0.57, 0.6), 0.4, spec=0.8)
    mat("yellow", (0.95, 0.78, 0.05)); mat("scanner", (0.95, 0.8, 0.05)); mat("cam", (0.12, 0.12, 0.13), spec=0.8)
    mat("part", (0.72, 0.74, 0.78), 0.3, spec=0.9, shin=0.9); mat("tray", (0.05, 0.05, 0.06))

    wb = sp.worldbody
    wb.add_light(pos=[0, 0, 4.5], dir=[0, 0, -1], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL, diffuse=[0.55, 0.5, 0.6], castshadow=1)
    wb.add_light(pos=[2.5, -2.5, 3], dir=[-0.6, 0.6, -0.6], diffuse=[0.35, 0.15, 0.45], castshadow=0)
    wb.add_light(pos=[-2.5, 2.5, 3], dir=[0.6, -0.6, -0.6], diffuse=[0.1, 0.35, 0.4], castshadow=0)
    wb.add_geom(name="floor", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[0, 0, 0.05], material="floor", group=GROUP_ENV)

    def vbox(body, name, pos, half, material, group=GROUP_ROBOT, quat=None):
        g = body.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material,
                          contype=0, conaffinity=0, group=group, mass=0)
        if quat is not None:
            g.quat = list(quat)
        return g

    # ---------------------------------------------------------- base mobile (AMR) + colonna
    amr = wb.add_body(name="amr", pos=[0, 0, 0])
    if not fixed_base:
        amr.add_freejoint(name="amr_free")
    # massa reale della base: scatola piena (ruote/batteria in basso)
    amr.add_geom(name="amr_chassis", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.13], size=[AMR_L / 2, AMR_W / 2, 0.075],
                 material="dark", mass=AMR_MASS, group=GROUP_ROBOT, contype=0 if fixed_base else 1, conaffinity=0 if fixed_base else 1)
    if not fixed_base:   # 4 appoggi (ruote motrici + piroette) agli angoli: definiscono il poligono di appoggio
        for sx in (-1, 1):
            for sy in (-1, 1):
                amr.add_geom(name=f"wheel_{sx}_{sy}", type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.055, 0, 0],
                             pos=[sx * (AMR_L / 2 - 0.07), sy * (AMR_W / 2 - 0.05), 0.055], mass=0.5, friction=[1.0, 0.01, 0.01],
                             material="dark", group=GROUP_ROBOT)
    vbox(amr, "amr_top", (0, 0, AMR_H - 0.005), (AMR_L / 2 - 0.02, AMR_W / 2 - 0.02, 0.008), "armor")
    for sx in (-1, 1):
        vbox(amr, f"amr_light{sx}", (sx * (AMR_L / 2 + 0.002), 0, 0.17), (0.003, AMR_W / 2 - 0.06, 0.012), "accent")
    for sy in (-1, 1):
        amr.add_geom(name=f"amr_wheel{sy}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, sy * (AMR_W / 2 - 0.01), 0.085],
                     quat=[0.7071, 0.7071, 0, 0], size=[0.085, 0.03, 0], material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for k, ((sx, sy), h) in enumerate(SCANNERS):      # SICK nanoScan3: 80 x 80 x 85 mm, giallo
        vbox(amr, f"scanner{k}_body", (sx, sy, SCAN_Z), (0.04, 0.04, 0.0425), "scanner")
        amr.add_site(name=f"scanner{k}", pos=[sx + 0.045 * math.cos(h), sy + 0.045 * math.sin(h), SCAN_Z],
                     euler=[0, 0, h], size=[0.01, 0, 0], group=4)
    vbox(amr, "column_outer", (-0.06, 0, AMR_H + 0.22), (0.09, 0.11, 0.22), "dark")   # colonna (LINAK/igus): stadio fisso
    col = amr.add_body(name="column", pos=[-0.06, 0, AMR_H + 0.05])
    col.add_joint(name="lift", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[0, 0, 1], range=[0, COLUMN_STROKE], damping=200, armature=5)
    col.add_geom(name="column_inner", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.2], size=[0.075, 0.095, 0.2],
                 material="steel", mass=6.0, contype=0, conaffinity=0, group=GROUP_ROBOT)

    # ---------------------------------------------------------- busto + braccia OpenArm 2.0 (originali)
    torso = col.add_body(name="torso", pos=[0.06, 0, 0.28])
    oa = mujoco.MjSpec.from_file(str(OA / "openarm_bimanual.xml"))
    for mname in ("pale_silver", "metal_silver", "matte_black"):   # vernice: unico intervento sulle parti vere
        m_ = oa.material(mname)
        if mname == "pale_silver":
            m_.rgba = list(LK["armor"]) + [1]; m_.reflectance = 0.15
        elif mname == "metal_silver":
            m_.rgba = list(LK["accent"]) + [1]; m_.emission = 0.3; m_.reflectance = 0.1
        else:
            m_.rgba = list(LK["dark"]) + [1]
    if hands != "gripper":
        for s in ("left", "right"):          # via la pinza originale: al suo posto la mano
            for fb in (f"openarm_{s}_ee_inner_finger", f"openarm_{s}_ee_outer_finger"):
                oa.delete(oa.body(fb))
            for g in list(oa.body(f"openarm_{s}_ee_base_link").geoms):
                oa.delete(g)
            for a in list(oa.actuators):
                if a.name == f"{s}_finger1_ctrl":
                    oa.delete(a)
        for e in list(oa.equalities):
            oa.delete(e)
        for t in list(oa.tendons):
            oa.delete(t)
    # busto originale OpenArm (body_link0)
    sp.add_mesh(name="body_link0", file=str(OA / "assets/visual/body/body_link0.stl"), scale=[0.001] * 3)
    torso.add_geom(name="torso_link0", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="body_link0", material="dark",
                   contype=0, conaffinity=0, group=GROUP_ROBOT, mass=8.0)
    fr = torso.add_frame(pos=[0, 0, PED_TOP])
    sp.attach(oa, frame=fr, prefix="")
    # gusci (rework estetico): corazza petto, spallacci, schiena
    vbox(torso, "shell_chest", (0.075, 0, PED_TOP - 0.15), (0.03, 0.09, 0.13), "armor")
    vbox(torso, "shell_chest_line", (0.106, 0, PED_TOP - 0.12), (0.002, 0.07, 0.005), "accent")
    torso.add_geom(name="core", type=mujoco.mjtGeom.mjGEOM_SPHERE, pos=[0.105, 0, PED_TOP - 0.06], size=[0.025, 0, 0],
                   material="visor" if look != "eva" else "neon0", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    vbox(torso, "shell_back", (-0.085, 0, PED_TOP - 0.2), (0.025, 0.1, 0.22), "armor")
    for s, sy in (("left", 1), ("right", -1)):
        l2 = sp.body(f"openarm_{s}_link2")
        vbox(l2, f"pauldron_{s}", (0, sy * 0.01, 0.0), (0.075, 0.06, 0.045), "armor")
        vbox(l2, f"pauldron_{s}_stripe", (0.0762, sy * 0.01, 0.0), (0.001, 0.045, 0.006), "accent")
        l5 = sp.body(f"openarm_{s}_link5")
        vbox(l5, f"forearm_{s}", (0.032, 0, -0.06), (0.012, 0.035, 0.05), "armor")

    # ---------------------------------------------------------- collo + testa con RealSense D435i
    neck = torso.add_body(name="neck", pos=[0, 0, PED_TOP + 0.09])
    neck.add_joint(name="head_yaw", axis=[0, 0, 1], range=[-1.6, 1.6], damping=0.5, armature=0.01)
    neck.add_geom(name="neck_g", type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.03, 0.03, 0], material="dark", mass=0.3,
                  contype=0, conaffinity=0, group=GROUP_ROBOT)
    head = neck.add_body(name="head", pos=[0, 0, 0.08])
    head.add_joint(name="head_pitch", axis=[0, 1, 0], range=[-0.6, 0.9], damping=0.5, armature=0.01)
    vbox(head, "helmet", (0, 0, 0.02), (0.075, 0.085, 0.07), "armor").mass = 0
    head.add_geom(name="helmet_mass", type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.05, 0, 0], mass=0.9, rgba=[0, 0, 0, 0],
                  contype=0, conaffinity=0, group=5)
    vbox(head, "visor", (0.072, 0, 0.03), (0.008, 0.075, 0.022), "visor")
    vbox(head, "d435i", (0.083, 0, -0.02), (0.0125, 0.045, 0.0125), "cam")       # 90 x 25 x 25 mm
    for k, y in enumerate((-0.025, 0.0, 0.025)):
        head.add_geom(name=f"d435_lens{k}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0.096, y, -0.02], quat=[0.7071, 0, 0.7071, 0],
                      size=[0.006, 0.001, 0], material="neon1" if k == 1 else "dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    horn = vbox(head, "horn", (0.05, 0, 0.12), (0.008, 0.007, 0.06), "accent" if look != "eva" else "steel")
    horn.quat = list(_q(np.array([[math.cos(-0.5), 0, math.sin(-0.5)], [0, 1, 0], [-math.sin(-0.5), 0, math.cos(-0.5)]])))
    for sy in (-1, 1):
        vbox(head, f"ear{sy}", (-0.01, sy * 0.09, 0.02), (0.035, 0.008, 0.035), "dark")
    # D435i RGB: 69 x 42 gradi, 1280x720 (fovy MuJoCo = verticale). Asse ottico -z della camera -> ruoto verso +x
    head.add_camera(name="head_d435i", pos=[0.098, 0, -0.02], xyaxes=[0, -1, 0, 0, 0, 1], fovy=42.0, resolution=[1280, 720])

    # ---------------------------------------------------------- mani
    for s, sgn in (("right", 1), ("left", -1)):
        ee = sp.body(f"openarm_{s}_ee_base_link")
        # flangia + RealSense D405 (42 x 42 x 23 mm) sul dorso del polso
        ee.add_geom(name=f"{s}_flange", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, -0.012], size=[0.032, 0.012, 0],
                    material="dark", mass=0.15, contype=0, conaffinity=0, group=GROUP_ROBOT)
        if hands == "leap":
            hsp = mujoco.MjSpec.from_file(str(LEAP / f"{s}_hand.xml"))
            for a in hsp.actuators:   # Dynamixel XC330-M288: coppia di stallo ~0.9 Nm, uso 0.5 Nm continuativi
                a.forcerange = [-0.35, 0.35]; a.forcelimited = 1
                a.gainprm[0] = 1.5; a.biasprm[1] = -1.5      # servo cedevole: le dita si adattano invece di spingere
            for g in hsp.geoms:
                g.group = GROUP_ROBOT
                if g.contype:
                    g.contype, g.conaffinity = 2, 0
                    g.friction = [1.2, 0.02, 0.002]; g.condim = 4
            for b_ in hsp.bodies:
                b_.gravcomp = 1.0
            RpH, base, p_hw, R_hw = leap_frame(s)
            # H nel frame del polso OpenArm: x_H (dita) = -z_ee, -z_H (chiusura) = +x_ee  ->  R_ee_H
            R_ee_H = np.stack([[0, 0, -1.0], np.cross([-1.0, 0, 0], [0, 0, -1.0]), [-1.0, 0, 0]], 1)
            R_ee_palm = R_ee_H @ RpH.T
            p_palm = np.array([0, 0, -0.03]) - R_ee_palm @ (base - RpH @ np.array([0.10, 0, 0]))
            R_fr = R_ee_palm @ R_hw.T                      # il palm ha gia' una posa nel file della mano
            f = ee.add_frame(pos=list(p_palm - R_fr @ p_hw), quat=list(_q(R_fr)))
            sp.attach(hsp, frame=f, prefix=f"{s}_")
            hb = sp.body(f"{s}_palm")
            hb.add_site(name=f"{s}_grasp", pos=list(base + RpH @ np.array(LEAP_CENTER)), quat=list(_q(RpH)), size=[0.008, 0, 0], group=4)
            cam_pos = np.array([-0.045, 0, -0.06])
            vbox(ee, f"{s}_d405", cam_pos, (0.0115, 0.021, 0.021), "cam")
            ee.add_camera(name=f"{s}_d405", pos=list(cam_pos + [0.0, 0, -0.025]), xyaxes=[0, 1, 0, 1, 0, 0], fovy=58.0, resolution=[848, 480])
            continue
        if hands == "gripper":
            ee.add_site(name=f"{s}_grasp", pos=[0, 0, -0.15], size=[0.008, 0, 0], group=4)   # centro polpastrelli pinza OpenArm
            cam_pos = np.array([-0.045, 0, -0.06])
            vbox(ee, f"{s}_d405", cam_pos, (0.0115, 0.021, 0.021), "cam")
            ee.add_camera(name=f"{s}_d405", pos=list(cam_pos + [0.0, 0, -0.025]), xyaxes=[0, 1, 0, 1, 0, 0], fovy=58.0, resolution=[848, 480])
            continue
        hs, mimic = _hand_spec(s)
        for g in hs.geoms:
            g.group = GROUP_ROBOT
            g.material = ""
            g.rgba = list(LK["dark"]) + [1] if "force_sensor" in (g.name or "") else list(LK["armor"]) + [1]
            g.friction = [1.2, 0.02, 0.002]
            g.solref = [0.004, 1]; g.priority = 1; g.condim = 4
            g.contype, g.conaffinity = 2, 0   # la mano tocca solo gli oggetti con conaffinity bit 2 (pezzi, banco): niente autocollisioni ne' contro il polso
        for j in hs.joints:
            j.limited = 1
        # assi mano: x = dita, palmo = +y (destra) / -y (sinistra), z = pollice
        # montaggio: dita lungo -z del polso OpenArm, palmo verso +x del polso
        xh, yh = np.array([0, 0, -1.0]), np.array([1.0, 0, 0]) * sgn
        Rm = np.stack([xh, yh, np.cross(xh, yh)], 1)
        f = ee.add_frame(pos=[0, 0, -0.024], quat=list(_q(Rm)))
        f.attach_body(hs.body(f"{s}_wrist_yaw_link"), "", "")
        hb = sp.body(f"{s}_wrist_yaw_link")
        hb.add_site(name=f"{s}_grasp", pos=[0.23, sgn * 0.055, 0.0], size=[0.008, 0, 0], group=4)   # centro presa (pezzo Ø50)
        for slave, master, mult in mimic:
            sp.add_equality(name=f"{slave}_mimic", type=mujoco.mjtEq.mjEQ_JOINT, name1=slave, name2=master,
                            data=[0, float(mult), 0, 0, 0, 0, 0, 0, 0, 0, 0], solref=[0.005, 1])
        # D405 sul dorso della mano, guarda lungo le dita
        cam_pos = np.array([-0.045 * sgn * 0 - 0.045, 0, -0.06])
        vbox(ee, f"{s}_d405", cam_pos + [0, 0, 0], (0.0115, 0.021, 0.021), "cam")
        ee.add_camera(name=f"{s}_d405", pos=list(cam_pos + [0.0, 0, -0.025]), xyaxes=[0, 1, 0, 1, 0, 0], fovy=58.0, resolution=[848, 480])
        # motori Inspire: 6 attuatori lineari (dita ~10 N, pollice ~15 N) -> coppia ai giunti ~0.6-1 Nm
        for jn, fr_ in ((f"{s}_thumb_1_joint", 0.6), (f"{s}_thumb_2_joint", 1.2), (f"{s}_index_1_joint", 0.8),
                        (f"{s}_middle_1_joint", 0.8), (f"{s}_ring_1_joint", 0.8), (f"{s}_little_1_joint", 0.8)):
            sp.joint(jn).damping = [0.05, 0, 0]; sp.joint(jn).armature = 0.002
            sp.add_actuator(name=f"{jn}_ctrl", target=jn, trntype=mujoco.mjtTrn.mjTRN_JOINT,
                            gaintype=mujoco.mjtGain.mjGAIN_FIXED, gainprm=[8.0] + [0] * 9,
                            biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -8.0, -0.2] + [0] * 7,
                            ctrlrange=sp.joint(jn).range, ctrllimited=1, forcerange=[-fr_, fr_], forcelimited=1)
        for j in hs.joints:
            pass
    # compensazione di gravita' FATTA DAI MOTORI (conta nei limiti di coppia reali)
    for s in ("left", "right"):
        for k in range(1, 8):
            sp.joint(f"openarm_{s}_joint{k}").actgravcomp = 1
    for b in sp.bodies:
        if b.name.startswith("openarm_") or b.name.startswith(("right_", "left_")) and hands != "leap":
            b.gravcomp = 1.0
    sp.add_actuator(name="lift_ctrl", target="lift", trntype=mujoco.mjtTrn.mjTRN_JOINT, gaintype=mujoco.mjtGain.mjGAIN_FIXED,
                    gainprm=[2e4] + [0] * 9, biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -2e4, -2e3] + [0] * 7,
                    ctrlrange=[0, COLUMN_STROKE], ctrllimited=1, forcerange=[-2000, 2000], forcelimited=1)
    for jn in ("head_yaw", "head_pitch"):
        sp.add_actuator(name=f"{jn}_ctrl", target=jn, trntype=mujoco.mjtTrn.mjTRN_JOINT, gaintype=mujoco.mjtGain.mjGAIN_FIXED,
                        gainprm=[20.0] + [0] * 9, biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -20.0, -1.5] + [0] * 7,
                        ctrlrange=sp.joint(jn).range, ctrllimited=1, forcerange=[-7, 7], forcelimited=1)
    return sp


if __name__ == "__main__":
    import sys
    sp = build(sys.argv[1] if len(sys.argv) > 1 else "eva")
    m = sp.compile()
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    print("nq", m.nq, "nu", m.nu, "neq", m.neq, "massa robot", round(m.body_subtreemass[m.body("amr").id], 1), "kg")
    print("attuatori", [m.actuator(i).name for i in range(m.nu)])
    print("camere", [m.camera(i).name for i in range(m.ncam)])
    print("spalle", d.body("openarm_right_link2").xpos, "testa", d.body("head").xpos)
