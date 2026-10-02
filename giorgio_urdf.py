"""Genera gli URDF delle braccia di Giorgio-P (7 giunti, pinza a due dita sul polso).

Convenzione: robot rivolto verso +x, z in alto. base_link di ogni braccio = centro della spalla.
Braccio pendente a q = 0 (lungo -z). Lo stesso file serve per destro (side=-1) e sinistro (side=+1).
"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/palletizer_demo"))
from core import gripper_urdf  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UPPER, FORE, HAND = 0.30, 0.26, 0.05          # lunghezze segmenti [m]
EFFORT = (120.0, 120.0, 60.0, 60.0, 20.0, 20.0, 15.0)   # coppie di picco tipo QDD Robstride/Damiao [Nm]


def arm_urdf(side):
    """side = -1 destro, +1 sinistro"""
    s = "r" if side < 0 else "l"
    roll = (-1.7, 0.35) if side < 0 else (-0.35, 1.7)
    J = [  # nome, asse, origine (dal link padre), limiti
        ("shoulder_pitch", "0 1 0", "0 0 0", (-3.0, 1.0)),
        ("shoulder_roll", "1 0 0", "0 0 0", roll),
        ("shoulder_yaw", "0 0 1", "0 0 0", (-2.2, 2.2)),
        ("elbow", "0 1 0", f"0 0 {-UPPER}", (-2.6, 0.0)),
        ("wrist_yaw", "0 0 1", "0 0 0", (-2.6, 2.6)),
        ("wrist_pitch", "0 1 0", f"0 0 {-FORE}", (-1.7, 1.7)),
        ("wrist_roll", "0 0 1", "0 0 -0.02", (-2.9, 2.9)),
    ]
    # visivi: cilindri = "muscolo" (attuatori), box = corazza, sfere = giunti (colorati dopo per tipo)
    VIS = {
        "link1": [("sphere", "0.065", "0 0 0")],
        "link2": [("box", "0.11 0.13 0.09", f"0 {side * 0.01} -0.02")],                      # spallaccio
        "link3": [("cylinder", "0.042 0.24", f"0 0 {-UPPER / 2}"), ("box", "0.075 0.07 0.17", f"0.01 0 {-UPPER / 2 + 0.01}")],
        "link4": [("sphere", "0.05", "0 0 0")],
        "link5": [("cylinder", "0.036 0.20", f"0 0 {-FORE / 2}"), ("box", "0.06 0.065 0.13", f"0.012 0 {-FORE / 2 + 0.02}")],
        "link6": [("sphere", "0.038", "0 0 0")],
        "link7": [("cylinder", "0.034 0.03", "0 0 -0.015")],
    }
    MASS = {"link1": 0.8, "link2": 0.9, "link3": 1.6, "link4": 0.4, "link5": 1.1, "link6": 0.3, "link7": 0.25}
    out = [f'<robot name="giorgio_arm_{s}">', '<link name="base_link"/>']
    parent = "base_link"
    for i, (nm, ax, org, (lo, hi)) in enumerate(J):
        ln = f"link{i + 1}"
        out.append(f'<link name="{ln}"><inertial><origin xyz="0 0 -0.05"/><mass value="{MASS[ln]}"/>'
                   f'<inertia ixx="0.004" iyy="0.004" izz="0.002" ixy="0" ixz="0" iyz="0"/></inertial>')
        for kind, dims, xyz in VIS[ln]:
            if kind == "cylinder":
                g = '<cylinder radius="{}" length="{}"/>'.format(*dims.split())
            else:
                g = f'<sphere radius="{dims}"/>' if kind == "sphere" else f'<box size="{dims}"/>'
            out.append(f'<visual><origin xyz="{xyz}"/><geometry>{g}</geometry></visual>')
        out.append("</link>")
        out.append(f'<joint name="{s}_{nm}" type="revolute"><parent link="{parent}"/><child link="{ln}"/>'
                   f'<origin xyz="{org}"/><axis xyz="{ax}"/><limit lower="{lo}" upper="{hi}" effort="{EFFORT[i]}" velocity="3.0"/></joint>')
        parent = ln
    # flangia: z utensile uscente dalla mano (lungo -z del braccio pendente)
    out.append('<link name="tool0"/>')
    out.append(f'<joint name="{s}_tool" type="fixed"><parent link="link7"/><child link="tool0"/>'
               f'<origin xyz="0 0 {-HAND + 0.02}" rpy="3.14159265 0 0"/></joint>')
    out.append("</robot>")
    base = os.path.join(HERE, f"robots/giorgio_arm_{s}_bare.urdf")
    os.makedirs(os.path.dirname(base), exist_ok=True)
    open(base, "w").write("\n".join(out))
    full = os.path.join(HERE, f"robots/giorgio_arm_{s}.urdf")
    grasp = gripper_urdf(base, full, stroke=0.07, finger_len=0.05, finger_w=0.02, body_len=0.05, grip_force=60.0)
    return full, grasp


if __name__ == "__main__":
    for sd in (-1, 1):
        print(arm_urdf(sd))
