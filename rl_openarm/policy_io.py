"""Interfaccia della politica: costanti, osservazione e azione. Unica definizione condivisa da
addestramento (GPU, env_openarm.py) ed esecuzione su CPU (standalone e Giorgio, run_cpu.py).

Tutto e' espresso nel frame base del braccio: la politica non sa su quale robot e' montato il braccio."""
import numpy as np
import torch

CTRL_DT = 0.04          # 25 Hz
EP_LEN = 150            # 6 s
ACT_SCALE = 0.05        # rad per passo di controllo (max 1.25 rad/s sul target)
GOAL_DZ = 0.12          # obiettivo di sollevamento nella ricompensa (margine sopra i 10 cm del criterio)
SUCC_DZ = 0.10          # successo: cubo >= 10 cm sopra la quota iniziale, vicino alla pinza...
SUCC_HOLD = 25          # ...per almeno 1 s consecutivo
Q_HOME = [0.2, 0.1, 0.0, 1.6, 0.0, 0.0, 0.0]
G_OPEN, G_CLOSE = -0.7854, 0.4    # comando pinza destra (ctrlrange ufficiale): -0.785 aperta, >0 stringe
OBS_DIM = 7 + 7 + 1 + 8 + 3 + 3 + 3 + 3 + 8
ACT_DIM = 8


def grip_cmd(a):
    """a<=0 -> aperta; 0..1 -> chiusura progressiva (oltre lo 0 il servo stringe)."""
    if isinstance(a, torch.Tensor):
        return G_OPEN + (G_CLOSE - G_OPEN) * a.clamp(0, 1)
    return G_OPEN + (G_CLOSE - G_OPEN) * float(np.clip(a, 0, 1))


def build_obs_torch(q, qd, qf, target, gtarget, grasp_b, cube_b, goal_b, last_a):
    qh = torch.tensor(Q_HOME, device=q.device)
    return torch.cat([q - qh, 0.1 * qd, qf[:, None], target - qh, gtarget[:, None],
                      grasp_b * 3, cube_b * 3, (cube_b - grasp_b) * 5, (goal_b - cube_b) * 5, last_a], -1)


def build_obs_np(q, qd, qf, target, gtarget, grasp_b, cube_b, goal_b, last_a):
    qh = np.array(Q_HOME)
    o = np.concatenate([q - qh, 0.1 * qd, [qf], target - qh, [gtarget], grasp_b * 3, cube_b * 3,
                        (cube_b - grasp_b) * 5, (goal_b - cube_b) * 5, last_a])
    return np.clip(np.nan_to_num(o), -10, 10).astype(np.float32)
