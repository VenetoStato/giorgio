"""Policy interface for the drawer-opening task (shared by GPU training, CPU evaluation on the standalone OpenArm and
on Giorgio). Everything is expressed in the arm base frame (body 'openarm_right_base_link').

Observation (56):
  arm q - q_home (7), 0.1*qd (7), gripper q (1), current joint targets - q_home (7), gripper target (1),
  grasp point from FK *3 (3), gripper approach axis (3), finger closing axis (3),
  handle point "from vision" *3 (3), handle - grasp point *5 (3), drawer pull axis (3), handle bar axis (3; 0 for a knob),
  handle size *10 [bar length or knob dia, bar/knob radius, standoff] (3), drawer opening "from vision" *5 (1),
  last action (8)
Action (8): 7 joint position-target increments (ACT_SCALE rad/step, 25 Hz) + gripper command (same as the lift policy).
"""
import numpy as np
import torch

CTRL_DT = 0.04          # 25 Hz
EP_LEN = 200            # 8 s
ACT_SCALE = 0.05
Q_HOME = [0.1, 0.1, 0.0, 2.3, 0.0, 0.0, 0.0]   # retracted: grasp point ~0.26 m in front of the base, clear of the cabinet
G_OPEN, G_CLOSE = -0.7854, 0.4
OPEN_GOAL = 0.18        # reward target (margin above the success threshold)
SUCC_OPEN = 0.15        # success: drawer opened >= 15 cm ...
SUCC_HOLD = 12          # ... for >= 0.48 s continuously
OBS_DIM = 7 + 7 + 1 + 7 + 1 + 9 + 3 + 3 + 3 + 3 + 3 + 1 + 8
ACT_DIM = 8


def grip_cmd(a):
    if isinstance(a, torch.Tensor):
        return G_OPEN + (G_CLOSE - G_OPEN) * a.clamp(0, 1)
    return G_OPEN + (G_CLOSE - G_OPEN) * float(np.clip(a, 0, 1))


def build_obs_torch(q, qd, qf, target, gtarget, grasp_b, appr_b, fing_b, handle_b, pull_b, bar_b, hsize, opening, last_a):
    qh = torch.tensor(Q_HOME, device=q.device)
    return torch.cat([q - qh, 0.1 * qd, qf[:, None], target - qh, gtarget[:, None], grasp_b * 3, appr_b, fing_b,
                      handle_b * 3, (handle_b - grasp_b) * 5, pull_b, bar_b, hsize * 10, opening[:, None] * 5, last_a], -1)


def build_obs_np(q, qd, qf, target, gtarget, grasp_b, appr_b, fing_b, handle_b, pull_b, bar_b, hsize, opening, last_a):
    qh = np.array(Q_HOME)
    o = np.concatenate([q - qh, 0.1 * qd, [qf], target - qh, [gtarget], grasp_b * 3, appr_b, fing_b,
                        handle_b * 3, (handle_b - grasp_b) * 5, pull_b, bar_b, np.asarray(hsize) * 10, [opening * 5], last_a])
    return np.clip(np.nan_to_num(o), -10, 10).astype(np.float32)
