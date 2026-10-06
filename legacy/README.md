# legacy/: one-off and superseded files

These files are kept for history. Nothing current imports them, and they are **not maintained**. Some of them may no
longer run against the current model, because the APIs of `giorgio_model.py` have changed since.

| File | What it was |
|---|---|
| `giorgio_cell.py` | first collaborative-cell demo on Newton + MuJoCo Warp (fixed torso, two scanners, people) |
| `giorgio_model_v1.py` | first MjSpec model: OpenArm 2.0 + Inspire hands + RealSense head; replaced by `giorgio_model.py` |
| `render_test.py`, `grasp_test.py` | quick render and Inspire-hand grasp tests from the first week |
| `pose_scatole_v14.py` | product poses for the v14 box-tray photos |
| `rifai_tutto.sh`, `rifai_v8b.sh`, `rifai_v11.sh` | ("redo everything") batch scripts that re-recorded and re-rendered the v8/v8b/v11 videos |
| `HANDOFF_2026-10-05.md` | Italian hand-over notes of 2026-10-05 (video v16, open items at that date) |
| `anteprima_eva.jpg` | early preview render ("eva" look) |

To run one anyway, start from the repository root with the root on the path. For example:
`PYTHONPATH=. python legacy/render_test.py`. The shell scripts expect personal paths. Read them before you run them.
