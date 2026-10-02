"""Valutazione (metriche su N episodi) e video MuJoCo offscreen della politica.

Esempi:
  python valuta_e_video.py metriche runs/r1/modello.pt --n 50
  python valuta_e_video.py video runs/r1/modello.pt --out dopo.mp4 --secondi 15 --npz traiettoria_dopo.npz
  python valuta_e_video.py video runs/r1/modello_iniziale.pt --out prima.mp4 --secondi 8 --stocastica
"""
import os
os.environ.setdefault("MUJOCO_GL", "egl")
import argparse
import json
import math
import numpy as np
import torch
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

from env_orca import OrcaCubeEnv, XML, PALMO, Z_PALMO
from train import AttoreCritico

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def carica(path, env):
    ck = torch.load(path, map_location=env.dev)
    ac = AttoreCritico(env.obs_dim, env.act_dim).to(env.dev)
    ac.load_state_dict(ck["modello"])
    ac.eval()
    return ac, ck


@torch.no_grad()
def metriche(ckpt, n=50, secondi=10.0, dr=True, stocastica=False, seed=123):
    env = OrcaCubeEnv(n, randomize=dr, seed=seed, ep_len=10 ** 9)
    ac, ck = carica(ckpt, env)
    T = int(round(secondi / env.dt))
    obs = env.reset()
    attivo = torch.ones(n, dtype=torch.bool, device=env.dev)
    rot = torch.zeros(n, device=env.dev)
    caduto = torch.zeros(n, dtype=torch.bool, device=env.dev)
    for _ in range(T):
        a = ac.dist(obs).sample() if stocastica else ac.act_det(obs)
        obs, r, d, to, info = env.step(a)
        rot = torch.where(attivo, info["rot_acc"], rot)
        nuovo = info["caduto"] & attivo
        caduto |= nuovo
        attivo &= ~nuovo
    rot = rot.cpu().numpy()
    ok = ~caduto.cpu().numpy()
    return {
        "checkpoint": ckpt, "passi_addestramento": int(ck.get("passi", 0)),
        "episodi": n, "secondi": secondi, "randomizzazione": dr, "stocastica": stocastica,
        "rad_per_10s_media": float(rot.mean() * 10 / secondi),
        "rad_per_10s_mediana": float(np.median(rot) * 10 / secondi),
        "rad_per_10s_senza_cadute": float(rot[ok].mean() * 10 / secondi) if ok.any() else 0.0,
        "frac_cadute": float(1 - ok.mean()),
        "giri_per_10s_media": float(rot.mean() * 10 / secondi / (2 * math.pi)),
    }


def testo(img, righe, titolo):
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    W, H = im.size
    s = H / 1080
    fb = ImageFont.truetype(FONT_B, int(44 * s))
    f = ImageFont.truetype(FONT, int(34 * s))
    dr.text((int(60 * s), int(50 * s)), titolo, fill=(30, 30, 35), font=fb)
    y = int(115 * s)
    for r in righe:
        dr.text((int(60 * s), y), r, fill=(60, 60, 70), font=f)
        y += int(48 * s)
    return np.asarray(im)


@torch.no_grad()
def video(ckpt, out, secondi, stocastica=False, npz=None, titolo="", W=1920, H=1080, seed=7):
    env = OrcaCubeEnv(1, randomize=False, seed=seed, registra=True, ep_len=10 ** 9)
    ac, ck = carica(ckpt, env)
    obs = env.reset()
    T = int(math.ceil(secondi / env.dt)) + 1
    rot_t, cad_t = [], []
    cad = False
    for _ in range(T):
        a = ac.dist(obs).sample() if stocastica else ac.act_det(obs)
        if cad:
            a = torch.zeros_like(a)
        obs, r, d, to, info = env.step(a)
        if info["caduto"][0].item() and not cad:
            cad = True
            env.reset_idx = lambda ids: None  # niente reset: il cubo cade davvero
        rot_t.append(info["rot_acc"][0].item())
        cad_t.append(cad)
    q = torch.stack(env.frames)[:, 0].cpu().numpy().astype(np.float64)  # 200 Hz
    dt_f = env.mjm.opt.timestep

    m = mujoco.MjModel.from_xml_path(XML)
    m.vis.global_.offwidth, m.vis.global_.offheight = W, H
    d = mujoco.MjData(m)
    rnd = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [PALMO[0] - 0.005, PALMO[1] + 0.015, Z_PALMO + 0.02]
    cam.distance = 0.34
    cam.azimuth = 130
    cam.elevation = -40
    m.vis.headlight.ambient[:] = 0.45
    m.vis.headlight.diffuse[:] = 0.45
    m.light_diffuse[:] *= 1.3
    opt = mujoco.MjvOption()
    fps = 30
    F = int(secondi * fps)
    w = imageio.get_writer(out, fps=fps, codec="libx264", quality=8, macro_block_size=1,
                           ffmpeg_params=["-pix_fmt", "yuv420p"])
    QP, XP, XQ = [], [], []
    for k in range(F):
        t = k / fps
        i = min(int(round(t / dt_f)), len(q) - 1)
        d.qpos[:] = q[i]
        mujoco.mj_forward(m, d)
        QP.append(d.qpos.copy())
        XP.append(d.xpos.copy())
        XQ.append(d.xquat.copy())
        rnd.update_scene(d, cam, opt)
        img = rnd.render()
        j = min(int(t / env.dt), len(rot_t) - 1)
        rr = rot_t[j]
        righe = [f"t = {t:4.1f} s",
                 f"rotazione cubo attorno alla verticale: {rr:+6.2f} rad ({rr / (2 * math.pi):+.2f} giri)"]
        if cad_t[j]:
            righe.append("CUBO CADUTO")
        w.append_data(testo(img, righe, titolo))
    w.close()
    rnd.close()
    if npz:
        np.savez_compressed(npz, qpos=np.array(QP, np.float32), xpos=np.array(XP, np.float32),
                            xquat=np.array(XQ, np.float32), fps=fps, mjcf=XML,
                            body_names=np.array([m.body(b).name for b in range(m.nbody)]),
                            joint_names=np.array([m.joint(j).name for j in range(m.njnt)]),
                            lato_cubo_m=2 * float(m.geom_size[m.geom("cubo_col").id][0]),
                            checkpoint=ckpt)
    return {"rad_finali": rot_t[-1], "caduto": cad_t[-1], "secondi": secondi}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cosa", choices=["metriche", "video"])
    ap.add_argument("ckpt")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--secondi", type=float, default=10.0)
    ap.add_argument("--stocastica", action="store_true")
    ap.add_argument("--nodr", action="store_true")
    ap.add_argument("--out", default="video.mp4")
    ap.add_argument("--npz", default=None)
    ap.add_argument("--titolo", default="Mano ORCA v2 - rotazione cubo in mano (RL)")
    ap.add_argument("--W", type=int, default=1920)
    ap.add_argument("--H", type=int, default=1080)
    a = ap.parse_args()
    if a.cosa == "metriche":
        print(json.dumps(metriche(a.ckpt, a.n, a.secondi, not a.nodr, a.stocastica), indent=1))
    else:
        print(video(a.ckpt, a.out, a.secondi, a.stocastica, a.npz, a.titolo, a.W, a.H))
