"""Policy interface for 'open the cabinet' (drawer OR hinged door, articulation not given), shared by GPU training and
CPU runs (standalone OpenArm and Giorgio). Everything is in the arm base frame ('openarm_right_base_link').

Observation (58):
  arm q - q_home (7), 0.1*qd (7), gripper q (1), joint targets - q_home (7), gripper target (1),
  grasp point *3 (3), gripper approach axis (3), finger closing axis (3),
  handle point "from vision" *3 (3), handle - grasp *5 (3), front-panel outward normal "from vision" (3),
  handle bar axis (3; 0 for a knob), handle size *10 [bar length or knob dia, radius, standoff] (3),
  handle displacement since the episode start *5 (3), last action (8)
Action (8): 7 joint position-target increments (ACT_SCALE rad/step, 25 Hz) + gripper command (as the lift policy).
"""
import math
import numpy as np
import torch

CTRL_DT = 0.04
EP_LEN = 250            # 10 s
ACT_SCALE = 0.05
Q_HOME = [0.1, 0.1, 0.0, 2.3, 0.0, 0.0, 0.0]   # retracted, clear of the cabinet
G_OPEN, G_CLOSE = -0.7854, 0.4
DRAWER_GOAL, DOOR_GOAL = 0.18, math.radians(70)     # reward targets
DRAWER_SUCC, DOOR_SUCC = 0.15, math.radians(60)     # success: drawer >= 15 cm, door >= 60 deg ...
SUCC_HOLD = 12                                      # ... held >= 0.48 s
OBS_DIM = 7 + 7 + 1 + 7 + 1 + 9 + 15 + 3 + 8
ACT_DIM = 8


def grip_cmd(a):
    if isinstance(a, torch.Tensor):
        return G_OPEN + (G_CLOSE - G_OPEN) * a.clamp(0, 1)
    return G_OPEN + (G_CLOSE - G_OPEN) * float(np.clip(a, 0, 1))


def build_obs_torch(q, qd, qf, target, gtarget, grasp_b, appr_b, fing_b, handle_b, normal_b, bar_b, hsize, disp_b, last_a):
    qh = torch.tensor(Q_HOME, device=q.device)
    return torch.cat([q - qh, 0.1 * qd, qf[:, None], target - qh, gtarget[:, None], grasp_b * 3, appr_b, fing_b,
                      handle_b * 3, (handle_b - grasp_b) * 5, normal_b, bar_b, hsize * 10, disp_b * 5, last_a], -1)


def build_obs_np(q, qd, qf, target, gtarget, grasp_b, appr_b, fing_b, handle_b, normal_b, bar_b, hsize, disp_b, last_a):
    qh = np.array(Q_HOME)
    o = np.concatenate([q - qh, 0.1 * qd, [qf], target - qh, [gtarget], grasp_b * 3, appr_b, fing_b,
                        handle_b * 3, (handle_b - grasp_b) * 5, normal_b, bar_b, np.asarray(hsize) * 10, disp_b * 5, last_a])
    return np.clip(np.nan_to_num(o), -10, 10).astype(np.float32)
