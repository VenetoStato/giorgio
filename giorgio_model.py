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

LOOKS = {   # corazza, accento, scuro (giunti), visiera, neon ambiente, metallo
    "gb":    dict(armor=(0.86, 0.86, 0.84), accent=(1.0, 0.55, 0.22), dark=(0.045, 0.047, 0.052), visor=(0.015, 0.015, 0.02),
                  neon=((0.9, 0.9, 0.92), (1.0, 0.55, 0.22)), metal=(0.62, 0.63, 0.66), light=True),
    "eva":   dict(armor=(0.34, 0.16, 0.52), accent=(0.45, 0.95, 0.15), dark=(0.10, 0.09, 0.12), visor=(1.0, 0.42, 0.05), neon=((0.9, 0.2, 0.9), (0.45, 0.95, 0.15)), metal=(0.55, 0.56, 0.6), light=False),
    "akira": dict(armor=(0.78, 0.06, 0.05), accent=(0.95, 0.95, 0.92), dark=(0.09, 0.09, 0.10), visor=(0.2, 0.9, 1.0), neon=((1.0, 0.15, 0.1), (0.2, 0.9, 1.0)), metal=(0.55, 0.56, 0.6), light=False),
    "gits":  dict(armor=(0.80, 0.77, 0.70), accent=(0.20, 0.55, 1.00), dark=(0.16, 0.17, 0.19), visor=(1.0, 0.15, 0.15), neon=((0.2, 0.55, 1.0), (0.1, 0.9, 0.7)), metal=(0.55, 0.56, 0.6), light=False),
    "blame": dict(armor=(0.30, 0.31, 0.32), accent=(0.85, 0.86, 0.82), dark=(0.05, 0.05, 0.06), visor=(0.92, 0.96, 1.0), neon=((0.7, 0.75, 0.8), (0.95, 0.5, 0.2)), metal=(0.55, 0.56, 0.6), light=False),
    "cyber": dict(armor=(0.07, 0.07, 0.08), accent=(0.98, 0.90, 0.08), dark=(0.20, 0.20, 0.22), visor=(0.1, 0.95, 0.95), neon=((0.98, 0.9, 0.08), (0.1, 0.95, 0.95)), metal=(0.55, 0.56, 0.6), light=False),
}

# dimensioni (m)
AMR_L, AMR_W, AMR_H = 0.702, 0.61, 0.25        # AgileX Tracer 2.0: 702 x 610 x 169 mm + piastra e carter (0.25 m)
AMR_MASS = 55.0                               # Tracer 2.0: 54-56 kg
CART_MASS = 45.0                              # carrello: telaio alluminio + batteria/alimentatori + 25 kg di zavorra in basso
FOOT_X, FOOT_Y = 0.42, 0.40
WHEEL_R = 0.085
COF_SH = 0.69                                 # mensola dello zaino caffe'
COF_X = -0.225
COF_Y_IN, COF_Y_OUT = -0.10, -0.24             # navetta: sotto l'erogatore / fuori, presa dall'alto
COF_STACK = (-0.105, -0.27)                    # pila bicchieri
COF_LIFT = 0.020
COF_MH = 0.229                                # altezza reale della macchina a capsule (pulsanti sopra la testa)                               # supporto tazzina ribaltabile della Inissia: navetta 9 cm sopra la vaschetta
COF_STACK_Z = 0.12                             # piedistallo della pila
BUF_Z = 0.95                                  # fondo degli alloggi del buffer a bordo
BUFFER_SLOTS = [(0.19, y) for y in (0.11, 0.185, 0.26)]   # vassoio frontale: per lato (y con segno), riferimento base   # per lato (y con segno), nel riferimento della base                   # piedini stabilizzatori su bracci sporgenti (poligono 0.84 x 0.80 m)
SHELL_DIR = str(Path(__file__).resolve().parent / "assets/shells")
COLUMN_STROKE = 0.15
SCAN_Z = 0.18
SCANNERS = [((0.3467, -0.3467), -math.pi / 4), ((-0.3407, 0.3407), 3 * math.pi / 4)]     # pod d'angolo fuori dal Tracer (CAD): piano a 180 mm
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


def build(look="gb", hands="gripper", humans=2, fixed_base=True, base="cart", buffer=True, coffee=True):
    LK = LOOKS[look]
    sp = mujoco.MjSpec()
    sp.compiler.degree = False
    sp.option.timestep = 0.002
    sp.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    sp.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    sp.option.impratio = 10
    sp.visual.global_.offwidth, sp.visual.global_.offheight = 1920, 1080
    sp.visual.headlight.ambient = [0.35, 0.35, 0.36] if LK.get('light') else [0.25, 0.22, 0.3]
    sp.visual.headlight.diffuse = [0.5, 0.5, 0.55]
    sp.visual.quality.shadowsize = 4096
    sp.visual.rgba.haze = [0.7, 0.71, 0.73, 1] if LK.get("light") else [0.03, 0.02, 0.05, 1]
    sp.stat.center = [0.4, 0, 0.9]
    sp.stat.extent = 3.0

    L = LK.get("light", False)
    sp.add_texture(name="sky", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX, builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                   rgb1=[0.72, 0.73, 0.75] if L else [0.05, 0.03, 0.09], rgb2=[0.42, 0.43, 0.45] if L else [0.0, 0.0, 0.0], width=512, height=512)
    sp.add_texture(name="floor", type=mujoco.mjtTexture.mjTEXTURE_2D, builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                   rgb1=[0.56, 0.56, 0.57] if L else [0.06, 0.06, 0.075], rgb2=[0.58, 0.58, 0.59] if L else [0.085, 0.085, 0.1],
                   mark=mujoco.mjtMark.mjMARK_EDGE, markrgb=[0.5, 0.5, 0.52] if L else [0.2, 0.15, 0.3], width=512, height=512)
    mat_floor = sp.add_material(name="floor", texrepeat=[8, 8], reflectance=0.15)
    mat_floor.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "floor"

    def mat(name, rgb, refl=0.1, emission=0.0, spec=0.4, shin=0.5):
        sp.add_material(name=name, rgba=list(rgb) + [1.0], reflectance=refl, emission=emission, specular=spec, shininess=shin)

    mat("armor", LK["armor"], 0.15, spec=0.6, shin=0.7); mat("accent", LK["accent"], emission=0.6)
    mat("dark", LK["dark"], 0.05); mat("visor", LK["visor"], 0.3, emission=0.9)
    mat("neon0", LK["neon"][0], emission=1.0); mat("neon1", LK["neon"][1], emission=1.0)
    mat("bench", (0.82, 0.8, 0.77) if LK.get("light") else (0.11, 0.115, 0.13), 0.1); mat("steel", (0.55, 0.57, 0.6), 0.4, spec=0.8)
    mat("yellow", (0.95, 0.78, 0.05)); mat("scanner", (0.95, 0.8, 0.05)); mat("cam", (0.12, 0.12, 0.13), spec=0.8)
    mat("part", (0.72, 0.74, 0.78), 0.3, spec=0.9, shin=0.9); mat("tray", (0.05, 0.05, 0.06))

    wb = sp.worldbody
    wb.add_light(pos=[0, 0, 4.5], dir=[0, 0, -1], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL, diffuse=[0.55, 0.5, 0.6], castshadow=1)
    side_cols = ([0.35, 0.34, 0.33], [0.25, 0.27, 0.3]) if LK.get("light") else ([0.35, 0.15, 0.45], [0.1, 0.35, 0.4])
    wb.add_light(pos=[2.5, -2.5, 3], dir=[-0.6, 0.6, -0.6], diffuse=side_cols[0], castshadow=0)
    wb.add_light(pos=[-2.5, 2.5, 3], dir=[0.6, -0.6, -0.6], diffuse=side_cols[1], castshadow=0)
    wb.add_geom(name="floor", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[0, 0, 0.05], material="floor", group=GROUP_ENV)

    def vbox(body, name, pos, half, material, group=GROUP_ROBOT, quat=None):
        g = body.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), material=material,
                          contype=0, conaffinity=0, group=group, mass=0)
        if quat is not None:
            g.quat = list(quat)
        return g

    # ---------------------------------------------------------- base: carrello con piedini (default) o AMR Tracer 2.0
    amr = wb.add_body(name="amr", pos=[0, 0, 0])            # nome storico: e' la base, carrello o AMR
    if not fixed_base:
        amr.add_freejoint(name="amr_free")
    cart = base == "cart"
    base_mass = CART_MASS if cart else AMR_MASS
    ch = amr.add_geom(name="amr_chassis", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.13], size=[AMR_L / 2 - 0.02, AMR_W / 2 - 0.02, 0.07],
                      material="dark", mass=base_mass, group=GROUP_ROBOT)
    if fixed_base:
        ch.contype = ch.conaffinity = 0
    # carenatura della base (guscio unico, Tracer nascosto): fascia scura degli scanner, striscia LED di stato, paraurti in gomma
    for nm_ in ("base_skirt", "scan_band", "led_band", "bumper"):
        sp.add_mesh(name=nm_, file=SHELL_DIR + f"/{nm_}.obj")
    amr.add_geom(name="base_cover", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="base_skirt", pos=[0, 0, 0.170], material="armor",
                 contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    amr.add_geom(name="scan_window", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="scan_band", pos=[0, 0, SCAN_Z], material="visor",
                 contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    amr.add_geom(name="bumper", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="bumper", pos=[0, 0, 0.058], material="dark",
                 contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    sp.add_mesh(name="tricolor_band", file=SHELL_DIR + "/tricolor_band.obj")
    for k_, (col_, z_) in enumerate((((0.0, 0.55, 0.27), 0.132), ((0.97, 0.97, 0.95), 0.108), ((0.80, 0.09, 0.12), 0.084))):   # tricolore attorno alla base
        amr.add_geom(name=f"tricolore{k_}", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="tricolor_band", pos=[0, 0, z_],
                     rgba=list(col_) + [1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for k_, sy_ in enumerate((-0.020, 0.020)):        # collettore Roboteq RoboPad (2 poli, 75 A, +-5 mm) sul muso: faccia a x 0.406 (CAD)
        amr.add_geom(name=f"charge_pad{k_}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.402, sy_, 0.14], size=[0.004, 0.008, 0.012],
                     rgba=[0.72, 0.45, 0.2, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    # impianto elettrico sotto la carenatura (visibile nei render in trasparenza): 48 V SELV, un solo punto di ricarica
    PW = [("pw_battery", (0.184, 0.0, 0.2195), (0.135, 0.20, 0.0375), (0.15, 0.32, 0.62)),      # LiFePO4 15s 30 Ah (1,44 kWh), 13 kg (CAD)
          ("pw_bms", (0.184, 0.0, 0.262), (0.06, 0.08, 0.005), (0.10, 0.45, 0.20)),
          ("pw_dcdc0", (-0.10, 0.13, 0.232), (0.035, 0.045, 0.022), (0.75, 0.75, 0.78)),       # DC-DC 48 -> 24 V, braccio sinistro
          ("pw_dcdc1", (-0.10, -0.13, 0.232), (0.035, 0.045, 0.022), (0.75, 0.75, 0.78)),      # DC-DC 48 -> 24 V, braccio destro
          ("pw_contactor", (0.02, 0.15, 0.232), (0.025, 0.04, 0.022), (0.85, 0.12, 0.10)),     # contattori di sicurezza K1/K2
          ("pw_pnoz", (0.02, -0.15, 0.232), (0.02, 0.045, 0.022), (0.95, 0.80, 0.10)),         # Pilz PNOZmulti
          ("pw_charger", (-0.26, 0.15, 0.232), (0.05, 0.05, 0.022), (0.25, 0.25, 0.27)),       # caricatore isolato per la batteria del Tracer
          ("pw_jetson", (-0.26, -0.15, 0.232), (0.05, 0.05, 0.020), (0.12, 0.12, 0.13)),       # NVIDIA Jetson AGX Orin
          ("pw_tracer", (0.0, 0.0, 0.135), (0.33, 0.28, 0.07), (0.10, 0.10, 0.11))]            # AgileX Tracer 2.0
    for nm_, p_, h_, c_ in PW:
        amr.add_geom(name=nm_, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(p_), size=list(h_), rgba=list(c_) + [1],
                     contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for k_, (a_, b_) in enumerate((((0.40, -0.02, 0.14), (0.30, -0.02, 0.215)), ((0.40, 0.02, 0.14), (0.30, 0.02, 0.215)),     # RoboPad -> batteria
                                   ((0.05, 0.10, 0.225), (0.02, 0.15, 0.232)),                                               # batteria -> contattori
                                   ((0.02, 0.12, 0.25), (-0.10, 0.13, 0.25)), ((0.05, -0.10, 0.225), (-0.10, -0.13, 0.25)),  # -> DC-DC
                                   ((-0.10, 0.13, 0.255), (-0.06, 0.03, 0.29)), ((-0.10, -0.13, 0.255), (-0.06, -0.03, 0.29)))):  # DC-DC -> colonna
        a_, b_ = np.array(a_), np.array(b_)
        amr.add_geom(name=f"pw_cable{k_}", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=list(a_) + list(b_), size=[0.005, 0, 0],
                     rgba=[0.95, 0.45, 0.1, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    amr.add_geom(name="status_led0", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="led_band", pos=[0, 0, 0.262],
                 rgba=[0.2, 1.0, 0.45, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for k_ in (1, 2, 3):                                   # compatibilita': una sola striscia continua
        amr.add_geom(name=f"status_led{k_}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.2], size=[1e-4, 1e-4, 1e-4],
                     rgba=[0.2, 1.0, 0.45, 0], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    if cart:   # 4 ruote piroettanti + 4 piedini stabilizzatori a vite su bracci sporgenti (appoggio da fermo)
        for sx in (-1, 1):
            for sy in (-1, 1):
                amr.add_geom(name=f"caster_{sx}_{sy}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[sx * 0.26, sy * 0.22, 0.04],
                             quat=[0.7071, 0.7071, 0, 0], size=[0.04, 0.015, 0], material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
                fx, fy = sx * FOOT_X, sy * FOOT_Y
                vbox(amr, f"outrigger_{sx}_{sy}", (sx * (FOOT_X + 0.30) / 2, sy * (FOOT_Y + 0.25) / 2, 0.075),
                     (abs(FOOT_X - 0.30) / 2 + 0.02, abs(FOOT_Y - 0.25) / 2 + 0.02, 0.012), "dark")
                amr.add_geom(name=f"foot_{sx}_{sy}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[fx, fy, 0.035], size=[0.035, 0.035, 0],
                             material="steel", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
                if not fixed_base:
                    amr.add_geom(name=f"wheel_{sx}_{sy}", type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.03, 0, 0], pos=[fx, fy, 0.03],
                                 mass=0.3, friction=[1.0, 0.01, 0.01], rgba=[0, 0, 0, 0], group=GROUP_ROBOT)
    else:
        # AgileX Tracer 2.0: 2 ruote motrici centrali (differenziale) + 4 piroette agli angoli
        if fixed_base:
            for sy in (-1, 1):
                amr.add_geom(name=f"amr_wheel{sy}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, sy * (AMR_W / 2 - 0.04), 0.085],
                             quat=[0.7071, 0.7071, 0, 0], size=[0.085, 0.03, 0], material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
        else:
            for sy, nm in ((1, "left"), (-1, "right")):
                wb_ = amr.add_body(name=f"drive_{nm}", pos=[0, sy * (AMR_W / 2 - 0.04), WHEEL_R])
                wb_.add_joint(name=f"drive_{nm}", axis=[0, 1, 0], damping=0.5, armature=0.05)
                wb_.add_geom(name=f"drive_{nm}_vis", type=mujoco.mjtGeom.mjGEOM_CYLINDER, quat=[0.7071, 0.7071, 0, 0], size=[WHEEL_R, 0.03, 0],
                             material="dark", mass=0, contype=0, conaffinity=0, group=GROUP_ROBOT)
                # contatto ruota-pavimento come sfera: il cilindro in MuJoCo rotola "a scatti" e fa vibrare tutta la base
                wb_.add_geom(name=f"drive_{nm}_g", type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[WHEEL_R, 0, 0],
                             mass=2.0, friction=[1.2, 0.01, 0.001], condim=3, group=3, rgba=[0, 0, 0, 0])
                # motore mozzo Tracer: velocita' comandata, coppia limitata
                sp.add_actuator(name=f"drive_{nm}_vel", target=f"drive_{nm}", trntype=mujoco.mjtTrn.mjTRN_JOINT,
                                gaintype=mujoco.mjtGain.mjGAIN_FIXED, gainprm=[40.0] + [0] * 9, biastype=mujoco.mjtBias.mjBIAS_AFFINE,
                                biasprm=[0, 0, -40.0] + [0] * 7, ctrlrange=[-25, 25], ctrllimited=1, forcerange=[-60, 60], forcelimited=1)
            for sx in (-1, 1):
                for sy in (-1, 1):   # piroette sospese (molla + smorzatore): sempre a terra, niente beccheggio in frenata
                    cb = amr.add_body(name=f"caster_{sx}_{sy}", pos=[sx * (AMR_L / 2 - 0.07), sy * (AMR_W / 2 - 0.07), 0.040])
                    cb.add_joint(name=f"caster_susp_{sx}_{sy}", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[0, 0, 1], range=[-0.02, 0.02],
                                 stiffness=8000.0, springref=-0.006, damping=700.0, armature=0.5)
                    cb.add_geom(name=f"caster_{sx}_{sy}_g", type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.035, 0, 0], mass=0.3,
                                friction=[0.02, 0.001, 0.001], condim=1, material="dark", group=GROUP_ROBOT)
    for k, ((sx, sy), h) in enumerate(SCANNERS):      # SICK nanoScan3: 80 x 80 x 85 mm, giallo
        vbox(amr, f"scanner{k}_body", (sx, sy, SCAN_Z), (0.035, 0.035, 0.04), "dark")      # dentro la carenatura, dietro la fascia scura
        amr.add_site(name=f"scanner{k}", pos=[sx + 0.045 * math.cos(h), sy + 0.045 * math.sin(h), SCAN_Z],
                     euler=[0, 0, h], size=[0.01, 0, 0], group=4)
    # vassoio frontale (buffer a bordo): ripiano davanti al petto, tra le braccia, 6 alloggi profondi 90 mm
    if buffer:
        PK, WT, PH_ = 0.060, 0.009, 0.060                   # alloggi lisci (POM): 5 mm di gioco, pareti 60 mm, imbocco svasato
        CHM, tt, r2 = 0.016, 0.002, math.sqrt(0.5)           # svasatura a 45 gradi da 16 mm: assorbe ~2 cm di errore della pinza
        ys_all = sorted([sy * y for sy in (-1, 1) for _, y in BUFFER_SLOTS]); xb = BUFFER_SLOTS[0][0]
        x0, x1 = xb - PK / 2 - WT, xb + PK / 2 + WT
        y0, y1 = ys_all[0] - PK / 2 - WT, ys_all[-1] + PK / 2 + WT
        amr.add_geom(name="tray_plate", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[(x0 + x1) / 2, 0, BUF_Z - 0.006], size=[(x1 - x0) / 2 + 0.01, (y1 - y0) / 2 + 0.01, 0.006],
                     material="armor", group=GROUP_ROBOT, mass=0.8)
        for x_ in (x0 + WT / 2, x1 - WT / 2):
            amr.add_geom(name=f"tray_wx{x_:.3f}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[x_, 0, BUF_Z + (PH_ - CHM) / 2], size=[WT / 2, (y1 - y0) / 2, (PH_ - CHM) / 2],
                         material="armor", group=GROUP_ROBOT, mass=0.1, friction=[0.05, 0.01, 0.001])
        walls_y = [y0 + WT / 2] + [(ys_all[i] + ys_all[i + 1]) / 2 for i in range(len(ys_all) - 1)] + [y1 - WT / 2]
        for y_ in walls_y:
            amr.add_geom(name=f"tray_wy{y_:.3f}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[xb, y_, BUF_Z + (PH_ - CHM) / 2], size=[PK / 2 + WT, WT / 2, (PH_ - CHM) / 2],
                         material="armor", group=GROUP_ROBOT, mass=0.05, friction=[0.05, 0.01, 0.001])
        top_ = BUF_Z + PH_
        for kk, cy_ in enumerate(ys_all):
            for e_, (ox, oy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
                ex, ey = xb + ox * PK / 2, cy_ + oy * PK / 2
                mid = np.array([ex + ox * CHM / 2, ey + oy * CHM / 2, top_ - CHM / 2])
                c_ = mid - tt * np.array([-ox, -oy, 1.0]) * r2
                if ox:
                    q_ = [math.cos(-ox * math.pi / 8), 0, math.sin(-ox * math.pi / 8), 0]; sz = (CHM * r2, PK / 2 + CHM, tt)
                else:
                    q_ = [math.cos(oy * math.pi / 8), math.sin(oy * math.pi / 8), 0, 0]; sz = (PK / 2 + CHM, CHM * r2, tt)
                amr.add_geom(name=f"tray_ch{kk}_{e_}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(c_), quat=q_, size=list(sz),
                             material="armor", group=GROUP_ROBOT, mass=0.01, friction=[0.05, 0.01, 0.001])
        amr.add_geom(name="tray_band", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[x1 + 0.0015, 0, BUF_Z + PH_ - 0.01], size=[0.0015, (y1 - y0) / 2 - 0.02, 0.004],
                     material="accent", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
        for sy in (-1, 1):                                   # bracci di sostegno dal busto
            amr.add_geom(name=f"tray_arm{sy}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[(x0 + 0.02) / 2, sy * 0.06, BUF_Z - 0.03],
                         size=[(x0 + 0.02) / 2 + 0.03, 0.012, 0.015], material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.3)
    # zaino caffe' sul retro: macchina a capsule commerciale qualsiasi (classe 120 x 230 x 320 mm, ~2.4 kg) su mensola dietro la colonna,
    # frontale verso il lato destro del robot. Il braccio destro: prende un bicchiere dalla pila, lo posa sulla navetta,
    # preme il pulsante sulla testa; la navetta (attuatore lineare 150 mm) porta il bicchiere sotto l'erogatore e lo riporta fuori.
    if coffee:
        sh = COF_SH
        def cg(name, typ, pos, size, material=None, rgba=None, mesh=None, collide=False, quat=None, mass=0):
            g = amr.add_geom(name=name, type=typ, pos=list(pos), size=list(size), contype=1 if collide else 0, conaffinity=1 if collide else 0,
                             group=GROUP_ROBOT, mass=mass)
            if material: g.material = material
            if rgba is not None: g.rgba = list(rgba)
            if mesh: g.meshname = mesh
            if quat is not None: g.quat = list(quat)
            return g
        B, CY, MSH = mujoco.mjtGeom.mjGEOM_BOX, mujoco.mjtGeom.mjGEOM_CYLINDER, mujoco.mjtGeom.mjGEOM_MESH
        for nm_ in ("inissia_body", "inissia_head", "inissia_tank"):
            sp.add_mesh(name=nm_, file=SHELL_DIR + f"/{nm_}.obj")
        mx = COF_X
        cg("cm_mount", B, (-0.235, -0.17, sh - 0.008), (0.085, 0.135, 0.008), "armor", mass=1.2)            # mensola (sotto navetta e pila)
        sp.add_mesh(name="coffee_housing", file=SHELL_DIR + "/coffee_housing.obj")
        cg("cm_housing", MSH, (-0.255, 0.058, COF_SH - 0.029), (0, 0, 0), "armor", mesh="coffee_housing")              # guscio dello zaino (z 0.300-0.862)
        cg("cm_band", B, (-0.255, -0.0635, COF_SH + 0.19), (0.07, 0.0015, 0.012), "accent")                            # fascia accento Giorgio
        cg("logo_back", B, (-0.255, -0.0640, COF_SH + 0.055), (0.055, 0.0012, 0.055), rgba=[1, 1, 1, 1])               # logo Giorgio (tazzina) sullo zaino
        cg("cm_vent", B, (-0.255, -0.0635, COF_SH - 0.16), (0.05, 0.0015, 0.03), "dark")                              # griglia di aerazione
        cg("cm_body", MSH, (mx, 0.035, sh + 0.097), (0, 0, 0), rgba=[0.20, 0.21, 0.22, 1], mesh="inissia_body", mass=2.4)   # macchina generica, grafite
        cg("cm_head", MSH, (mx, -0.075, sh + 0.192), (0, 0, 0), rgba=[0.08, 0.08, 0.09, 1], mesh="inissia_head")
        cg("cm_tank", MSH, (mx, 0.155, sh + 0.087), (0, 0, 0), rgba=[0.65, 0.8, 0.95, 0.45], mesh="inissia_tank")
        cg("cm_lever", B, (mx, -0.055, sh + COF_MH - 0.004), (0.045, 0.04, 0.004), rgba=[0.10, 0.10, 0.11, 1])
        cg("cm_btn1", CY, (mx + 0.02, -0.105, sh + COF_MH), (0.009, 0.003, 0), rgba=[1.0, 0.55, 0.2, 1])      # espresso
        cg("cm_btn2", CY, (mx - 0.02, -0.105, sh + COF_MH), (0.009, 0.003, 0), rgba=[0.3, 0.3, 0.32, 1])      # lungo
        cg("cm_spout", CY, (mx, COF_Y_IN, sh + 0.150), (0.009, 0.012, 0), "steel")
        cg("cm_stream", CY, (mx, COF_Y_IN, sh + (0.035 + 0.138) / 2), (0.0022, (0.138 - 0.035) / 2, 0), rgba=[0.35, 0.18, 0.07, 0.0])
        cg("cm_drip", B, (mx, -0.10, sh + 0.004), (0.05, 0.045, 0.004), "steel")
        cg("cm_bin", B, (mx, 0.04, sh + 0.03), (0.05, 0.05, 0.03), rgba=[0.08, 0.08, 0.09, 1])                # capsule usate
        cg("cm_support", B, (mx, COF_Y_IN, sh + COF_LIFT / 2), (0.006, 0.03, COF_LIFT / 2), "steel")
        cg("cm_rail", B, (mx, (COF_Y_OUT + COF_Y_IN) / 2, sh + COF_LIFT + 0.003), (0.012, (COF_Y_IN - COF_Y_OUT) / 2 + 0.03, 0.003), "steel")
        cg("cm_logo", B, (mx - 0.061, 0.035, sh + 0.17), (0.0008, 0.035, 0.008), rgba=[0.9, 0.9, 0.9, 1])
        # navetta: piattello con 4 pioli che trattengono il bicchiere
        sb = amr.add_body(name="cm_shuttle", pos=[mx, COF_Y_OUT, sh + COF_LIFT + 0.006])
        sb.add_joint(name="cm_shuttle", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[0, 1, 0], range=[0, COF_Y_IN - COF_Y_OUT], damping=30, armature=0.2)
        sb.add_geom(name="cm_plate", type=B, size=[0.04, 0.04, 0.004], material="steel", mass=0.15, friction=[0.8, 0.01, 0.001])
        for k_, (px, py) in enumerate(((0.036, 0.0), (-0.036, 0.0), (0.0, 0.036), (0.0, -0.036))):
            sb.add_geom(name=f"cm_peg{k_}", type=CY, pos=[px, py, 0.012], size=[0.003, 0.009, 0], material="dark", mass=0.005)
        sp.add_actuator(name="cm_shuttle", target="cm_shuttle", trntype=mujoco.mjtTrn.mjTRN_JOINT, gaintype=mujoco.mjtGain.mjGAIN_FIXED,
                        gainprm=[400.0] + [0] * 9, biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=[0, -400.0, -60.0] + [0] * 7,
                        ctrlrange=[0, COF_Y_IN - COF_Y_OUT], ctrllimited=1, forcerange=[-30, 30], forcelimited=1)
        # pila di bicchieri impilati (aperta in alto: si prende il bicchiere di cima), anello di contenimento
        sx_, sy_ = COF_STACK
        zs = sh + COF_STACK_Z
        cg("cup_post", CY, (sx_, sy_, sh + COF_STACK_Z / 2), (0.03, COF_STACK_Z / 2, 0), "armor")
        cg("cup_ring", CY, (sx_, sy_, zs + 0.0225), (0.038, 0.0225, 0), rgba=[0.75, 0.85, 0.95, 0.25])
        for i in range(5):
            cg(f"cup_stack{i}", CY, (sx_, sy_, zs + 0.04 + 0.012 * i), (0.029, 0.04, 0), rgba=[0.97, 0.96, 0.93, 1])
        cg("cup_rest", CY, (sx_, sy_, zs + 0.006 + 0.012 * 5 - 0.002), (0.02, 0.002, 0), rgba=[0, 0, 0, 0], collide=True)
    # colonna: profilo alluminio 80x80 con slitta e morsetti (regolazione manuale), carter di design
    sp.add_mesh(name="column_cover", file=SHELL_DIR + "/column_fixed.obj")                  # carter fisso 180 x 200, z 0.300-0.540 (CAD)
    amr.add_geom(name="column_cover", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="column_cover", pos=[-0.06, 0, 0.42],
                 material="armor", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    amr.add_geom(name="column_sleeve", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.06, 0, 0.366], size=[0.05, 0.05, 0.189],
                 material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=2.40)      # tubo 100x100x3 + flangia
    amr.add_geom(name="base_equipment_mass", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.002, 0.002, 0.271], size=[0.05, 0.05, 0.02],
                 rgba=[0, 0, 0, 0], contype=0, conaffinity=0, group=3, mass=37.7)              # massa fissa sulla base (CAD 46,1 kg meno le parti che in sim hanno gia' massa propria)
    col = amr.add_body(name="column", pos=[-0.06, 0, AMR_H + 0.05])
    col.add_joint(name="lift", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=[0, 0, 1], range=[0, COLUMN_STROKE], damping=200, armature=5)
    col.add_geom(name="column_inner", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0, 0, 0.080], size=[0.04, 0.04, 0.185],
                 material="steel", mass=1.97, contype=0, conaffinity=0, group=GROUP_ROBOT)

    for nm, body_, pos, half in (("col_coll", amr, (-0.06, 0, AMR_H + 0.22), (0.085, 0.10, 0.22)),):
        body_.add_geom(name=nm, type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(pos), size=list(half), group=3, mass=0, rgba=[1, 0, 0, 0.3],
                       contype=2, conaffinity=0)   # urta solo l'ambiente (conaffinity bit 2), non le braccia
    # ---------------------------------------------------------- busto + braccia OpenArm 2.0 (originali)
    torso = col.add_body(name="torso", pos=[0.06, 0, 0.28])
    torso.add_geom(name="torso_coll", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.005, 0, PED_TOP - 0.17], size=[0.095, 0.15, 0.2],
                   group=3, mass=0, rgba=[1, 0, 0, 0.3], contype=2, conaffinity=0)
    # Orbbec Gemini 336L (124 x 29 x 27 mm) sulla parte alta del petto, tra le spalle, inclinata di 45 gradi verso il banco: ben visibile
    GT = math.radians(50)
    gp = np.array([0.108, 0.0, 0.665]); qg = [math.cos(GT / 2), 0, math.sin(GT / 2), 0]
    Rg = np.array([[math.cos(GT), 0, math.sin(GT)], [0, 1, 0], [-math.sin(GT), 0, math.cos(GT)]])
    torso.add_geom(name="gemini_body", type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(gp), quat=qg, size=[0.0135, 0.062, 0.0145],
                   material="cam", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.3)
    torso.add_geom(name="gemini_glass", type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(gp + Rg @ [0.0137, 0, 0]), quat=qg, size=[0.0006, 0.058, 0.011],
                   material="visor", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for k_, yy in enumerate((-0.047, -0.016, 0.016, 0.047)):          # stereo sx, RGB, proiettore IR, stereo dx
        torso.add_geom(name=f"gemini_lens{k_}", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=list(gp + Rg @ [0.0145, yy, 0]),
                       quat=[math.cos((GT + math.pi / 2) / 2), 0, math.sin((GT + math.pi / 2) / 2), 0],
                       size=[0.0065 if k_ != 2 else 0.004, 0.0012, 0], rgba=[0.02, 0.02, 0.03, 1] if k_ != 2 else [0.35, 0.05, 0.05, 1],
                       contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    up = np.array([math.sin(GT), 0, math.cos(GT)])
    torso.add_camera(name="gemini", pos=list(gp + Rg @ [0.016, 0, 0]), xyaxes=list(np.r_[[0, -1.0, 0], up]), fovy=65.0, resolution=[1280, 800])
    oa = mujoco.MjSpec.from_file(str(OA / "openarm_bimanual.xml"))
    for mname in ("pale_silver", "metal_silver", "matte_black"):   # vernice: unico intervento sulle parti vere
        m_ = oa.material(mname)
        if mname == "pale_silver":
            m_.rgba = list(LK["armor"]) + [1]; m_.reflectance = 0.15
        elif mname == "metal_silver":
            m_.rgba = list(LK["metal"]) + [1]; m_.reflectance = 0.3
        else:
            m_.rgba = list(LK["dark"]) + [1]
    HAND = {"right": hands.split("+")[0], "left": hands.split("+")[-1]}
    if hands != "gripper":
        for s in [s_ for s_ in ("left", "right") if HAND[s_] != "gripper"]:          # via la pinza originale: al suo posto la mano
            for fb in (f"openarm_{s}_ee_inner_finger", f"openarm_{s}_ee_outer_finger"):
                oa.delete(oa.body(fb))
            for g in list(oa.body(f"openarm_{s}_ee_base_link").geoms):
                oa.delete(g)
            for a_ in list(oa.actuators):
                if a_.name == f"{s}_finger1_ctrl":
                    oa.delete(a_)
        for e in list(oa.equalities):
            oa.delete(e)
        for t in list(oa.tendons):
            oa.delete(t)
    sp.add_mesh(name="body_link0", file=str(OA / "assets/visual/body/body_link0.stl"), scale=[0.001] * 3)
    torso.add_geom(name="torso_link0", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="body_link0", material="dark",
                   contype=0, conaffinity=0, group=GROUP_ROBOT, mass=13.89)
    fr = torso.add_frame(pos=[0, 0, PED_TOP])
    sp.attach(oa, frame=fr, prefix="")
    # gusci di design (mesh da shells.py)
    for nm in ("torso", "crown", "crown_glass", "pauldron"):
        sp.add_mesh(name=f"shell_{nm}", file=SHELL_DIR + f"/{nm}.obj")
    sp.add_mesh(name="waist_cover", file=SHELL_DIR + "/waist_cover.obj")      # carter di vita 268 x 200: contiene la piastra base OpenArm
    torso.add_geom(name="waist_cover", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="waist_cover", pos=[-0.028, 0, 0.12], material="armor",
                   contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    torso.add_geom(name="shell_torso", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="shell_torso", pos=[0.0, 0, 0.529],
                   material="armor", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    vbox(torso, "torso_accent", (0.104, 0, PED_TOP - 0.07), (0.002, 0.06, 0.003), "accent")
    torso.add_geom(name="logo_chest", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.0995, 0, PED_TOP - 0.20], size=[0.0012, 0.065, 0.065],
                   rgba=[1, 1, 1, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)   # logo Giorgio (tazzina) sul petto
    # spallacci decorativi rimossi: non sono nel CAD validato e col busto da 105 mm lo intersecavano (verifiche/gusci_reali.py)

    # ---------------------------------------------------------- testa fissa "cute": Gemini 336L dietro il frontale, 2 occhi-display, Insta360 sopra
    for nm in ("head", "face", "eye"):
        sp.add_mesh(name=f"shell_{nm}", file=SHELL_DIR + f"/{nm}.obj")
    crown = torso.add_body(name="crown", pos=[0, 0, PED_TOP + 0.13])
    crown.add_geom(name="head_shell", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="shell_head", material="armor",
                   contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.6)
    crown.add_geom(name="face_glass", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="shell_face", pos=[0.06, 0, -0.004],
                   material="visor", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    for sy in (1, -1):    # display rotondi GC9A01 1.28": il disegno dell'occhio si muove sul display (niente motori)
        crown.add_geom(name=f"eye_{'l' if sy > 0 else 'r'}", type=mujoco.mjtGeom.mjGEOM_ELLIPSOID, size=[0.004, 0.0125, 0.017],
                       pos=[0.088, sy * 0.032, 0.008], rgba=[0.45, 0.85, 1.0, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    crown.add_geom(name="crown_neck", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, -0.09], size=[0.03, 0.03, 0],
                   material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.2)
    # baffi a manubrio: due meta' scolpite in policarbonato diffusore con LED dentro, mosse da 2 micro-servo
    for nm in ("moustache_l", "moustache_r"):
        sp.add_mesh(name=f"shell_{nm}", file=SHELL_DIR + f"/{nm}.obj")
    for nm in ("l", "r"):
        crown.add_geom(name=f"mus_{nm}", type=mujoco.mjtGeom.mjGEOM_MESH, meshname=f"shell_moustache_{nm}", pos=[0.094, 0, -0.033],
                       rgba=[0.45, 0.85, 1.0, 1], contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    # Orbbec Gemini 336L dietro il frontale, sotto gli occhi, inclinata di 45 gradi verso il banco
    pitch = math.radians(45)
    up = np.array([math.sin(pitch), 0, math.cos(pitch)])
    # (spostata sul petto: vedi "barra sensori" sul busto)
    # Insta360 X4 sopra la testa ("antenna"): 46 x 38 x 124 mm, due fisheye -> 360 gradi
    crown.add_geom(name="mast", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[-0.01, 0, 0.1], size=[0.007, 0.03, 0],
                   material="dark", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.05)
    crown.add_geom(name="insta360", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-0.01, 0, 0.19], size=[0.019, 0.023, 0.062],
                   material="cam", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0.2)
    for sx in (-1, 1):
        crown.add_geom(name=f"insta_lens{sx}", type=mujoco.mjtGeom.mjGEOM_SPHERE, pos=[-0.01 + sx * 0.019, 0, 0.225], size=[0.012, 0, 0],
                       material="visor", contype=0, conaffinity=0, group=GROUP_ROBOT, mass=0)
    # 6 camere a cubo nel punto degli obiettivi: servono per ricostruire l'immagine equirettangolare 360
    for nm, xy in (("px", [0, -1, 0, 0, 0, 1]), ("nx", [0, 1, 0, 0, 0, 1]), ("py", [1, 0, 0, 0, 0, 1]),
                   ("ny", [-1, 0, 0, 0, 0, 1]), ("pz", [0, -1, 0, -1, 0, 0]), ("nz", [0, -1, 0, 1, 0, 0])):
        crown.add_camera(name=f"pano_{nm}", pos=[-0.01, 0, 0.225], xyaxes=xy, fovy=90.0, resolution=[512, 512])

    # ---------------------------------------------------------- mani
    for s, sgn in (("right", 1), ("left", -1)):
        ee = sp.body(f"openarm_{s}_ee_base_link")
        # flangia + RealSense D405 (42 x 42 x 23 mm) sul dorso del polso
        ee.add_geom(name=f"{s}_flange", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0, 0, -0.012], size=[0.032, 0.012, 0],
                    material="dark", mass=0.15, contype=0, conaffinity=0, group=GROUP_ROBOT)
        if HAND[s] in ("orca", "amazing"):
            # mani open intercambiabili sulla flangia OpenArm: ORCA Hand (CC BY 4.0, MJCF MIT) / Pollen AmazingHand (CC BY 4.0, Apache-2.0)
            side_ = "right" if s == "right" else "left"
            if HAND[s] == "orca":
                hsp = mujoco.MjSpec.from_file(str(HERE / f"third_party/orcahand_description/v2/giorgio_orca_{side_}.xml"))
            else:
                tag = "AH_Right" if s == "right" else "AH_Left"
                hsp = mujoco.MjSpec.from_file(str(HERE / f"third_party/AmazingHand/Demo/AHSimulation/AHSimulation/{tag}/mjcf/robot.xml"))
            for g in hsp.geoms:
                g.group = GROUP_ROBOT
                if g.contype or g.conaffinity:
                    g.contype, g.conaffinity = 2, 0
                    g.friction = [1.2, 0.02, 0.002]; g.condim = 4
            for b_ in hsp.bodies:
                b_.gravcomp = 1.0
            # la mano cresce lungo +z del suo file: la giro perche' cresca lungo -z del polso (verso le dita della pinza)
            f = ee.add_frame(pos=[0, 0, -0.024], quat=[0, 1, 0, 0])
            sp.attach(hsp, frame=f, prefix=f"{s}_")
            if HAND[s] == "orca":
                ee.add_site(name=f"{s}_grasp", pos=[0, -0.03, -0.20], size=[0.008, 0, 0], group=4)
                tipb = next(b_ for b_ in sp.bodies if b_.name.startswith(f"{s}_") and "I-FingerTipAssembly" in b_.name)
                tipb.add_site(name=f"{s}_index_tip", pos=[0, 0, 0], size=[0.006, 0, 0], group=4)
            else:                                            # AmazingHand: palmo verso +x del polso, pollice di fronte
                ee.add_site(name=f"{s}_grasp", pos=[0.035, 0.0, -0.135], size=[0.008, 0, 0], group=4)
            continue
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
            continue
        if HAND[s] == "gripper":
            ee.add_site(name=f"{s}_grasp", pos=[0, 0, -0.15], size=[0.008, 0, 0], group=4)   # centro polpastrelli pinza OpenArm
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
    print("spalle", d.body("openarm_right_link2").xpos, "corona", d.body("crown").xpos)
