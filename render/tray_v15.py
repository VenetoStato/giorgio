# segmenti "vassoi e scatole" per crea_edit_v14.py (eseguito con exec: usa T, kick, sub, card, big, small, shot, S, ACC, WHITE)
# numeri da render/v14/SHOTS.md (simulazione giorgio_scatole.py, rec_scatole_v14)
def _blk(x, y, k, t, s_, t0, t1, ts=60):
    o = dict(band=False, align="left", wide_ok=True, halo=True)
    out = [T(t0, t1, k, [x, y], 26, "X", color=ACC, track=2, **o), T(t0, t1, t, [x, y + 40], ts, **o)]
    if s_:
        out.append(T(t0 + 0.6, t1, s_, [x + 3, y + 40 + int(ts * 1.22 * (t.count("\n") + 1)) + 10], 34, "N", **o))
    return out
S.append(card(2.6, big(0.2, 2.6, "Carry more."), small(0.9, 2.6, "Front tray, rear rack, or both.")))
for f, a, b, c in (("tray_front", "FRONT TRAY", "Three boxes\nup front.", "Rubber mat, three slots."),
                   ("tray_rear", "REAR RACK", "A shelf on\nits back.", "Swaps in for the coffee module."),
                   ("tray_both", "BOTH", "Front and back.", "Five boxes · 71% of\nthe base payload.")):
    S.append(dict(type="card", dur=3.0, bg=f"stills_v15/{f}.png", dim=0.0, zoom=0.04, xfade=0.4, text_maxx=640,
                  texts=[kick(0.2, 3.0, a), T(0.2, 3.0, b, size=58), sub(0.5, 3.0, c)]))
S.append(shot("v15/t_rear/f_*.jpg", *_blk(1180, 790, "REAR RACK", "Loads its back shelf.", "1.2 kg box · 7 mm from the slot centre.", 0.3, 5.0, 54), start=114))
S.append(shot("v15/t_load/f_*.jpg", *_blk(1180, 790, "FRONT TRAY", "Then the front tray.", "Arms plan around the robot's own body.", 0.3, 5.0, 54), start=90))
S.append(shot("v15/t_pick/f_*.jpg", *_blk(90, 70, "BOTH ARMS", "Lifts a 3.1 kg tote\nwith two hands.", "Pinched at the rim, ~42 N per gripper.", 0.4, 8.0, 58)))
S.append(shot("v15/t_unload/f_*.jpg", *_blk(1250, 820, "DELIVERY", "Carried 4.3 m.\nSet down within 1 mm.", "", 0.4, 7.4, 54)))
