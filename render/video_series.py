"""Serie di video brevi (~1 min) + versione lunga, dagli stessi fotogrammi.  uso:  python video_series.py [nome ...]
nomi: teaser, componenti, attivita, training, personalizza, lungo  (default: tutti) -> edit_<nome>.json
Each shot uses the v18 frames (our own AMR, rev B) when that render is finished, otherwise v15 (old base) and says so.
Poi:  python verifica_testi.py edit_<nome>.json ; python music_v12.py edit_<nome>.json music_<nome>.wav ;
      python compose.py edit_<nome>.json ../video/serie/giorgio_<nome>.mp4
"""
import glob
import json
import os
import sys

BLACK, WHITE, GREY, ACC = [6, 6, 8], [245, 245, 242], [160, 162, 168], [255, 122, 26]
FPS, XF = 30, 0.6
LOG = open("run_v19.log").read() if os.path.exists("run_v19.log") else ""
OLD = []


def T(t0, t1, text, pos="ll", size=68, w="H", **k):
    d = dict(t0=t0, t1=t1, text=text, pos=pos, size=size, weight=w, align="left" if pos in ("ll", "llsub", "kick") else "center",
             shadow=False, band=pos == "ll", color=WHITE)
    d.update(k); return d


def kick(t0, t1, text):
    return T(t0, t1, text, "kick", 26, "X", color=ACC, band=False, track=2, above=120)


def sub(t0, t1, text):
    return T(t0, t1, text, "llsub", 36, "N", band=False)


def card(dur, *texts, **k):
    d = dict(type="card", dur=dur, color=BLACK, texts=list(texts), xfade=XF); d.update(k); return d


def big(t0, t1, text, size=92, **k):
    return T(t0, t1, text, "center", size, **k)


def small(t0, t1, text, **k):
    return T(t0, t1, text, "sub", 38, "N", color=[205, 207, 212], **k)


def frames(scene):
    """v18 if finished, else v15"""
    if f"fatto {scene} " in LOG and glob.glob(f"v19/{scene}/f_*.jpg"):
        return f"v19/{scene}/f_*.jpg"
    OLD.append(scene)
    for d in ("v18", "v15"):                      # fallback: older renders (base rev B1 / Ranger)
        if glob.glob(f"{d}/{scene}/f_*.jpg"):
            return f"{d}/{scene}/f_*.jpg"
    return None


def still(name):
    p = f"stills_v19/{name}.png"
    if os.path.exists(p) and f"fatto {name}" in LOG:
        return p
    OLD.append(name)
    return f"stills_v18/{name}.png" if os.path.exists(f"stills_v18/{name}.png") else f"stills_v15/{name}.png"


def shot(scene, *texts, **k):
    for t in texts:
        if t.get("color") in (WHITE, ACC) and not t.get("wide_ok"):
            t["halo"] = True
    g = scene if "*" in scene else frames(scene)
    if g is None:
        return None
    d = dict(type="frames", glob=g, texts=list(texts), ui=False); d.update(k); return d


def photo(path, dur, *texts, dim=0.0, zoom=0.04, **k):
    d = dict(type="card", dur=dur, bg=path, dim=dim, zoom=zoom, xfade=0.4, text_maxx=700, texts=list(texts)); d.update(k)
    for t in d["texts"]:
        t["halo"] = True
    return d


def opening(S, short=False):
    S.append(card(2.6, big(0.3, 2.6, "Italy deserves its own robot.", 80)))
    if not short:
        S.append(card(1.9, big(0.2, 1.9, "Not a Ferrari.")))
        S.append(card(3.0, big(0.2, 3.0, "A Fiat Panda."), small(1.0, 3.0, "Simple. Open. Fixable.")))


def ending(S, line="Want to know more?"):
    S.append(card(3.2, big(0.3, 3.2, line), small(1.2, 3.2, "github.com/VenetoStato/giorgio")))
    if os.path.exists("marchi_v14.txt"):
        S.append(card(4.0, T(0.3, 4.0, open("marchi_v14.txt").read().strip(), "center", 26, "N", color=GREY, band=False)))
    S.append(card(4.0, images=[dict(path="logo/logo_full_chiaro.png", t0=0.3, t1=4.0, pos=[960, 500], w=1100)]))


AMR = "../amr/renders"


def amr_section(S, full=True):
    S.append(card(2.8, big(0.3, 2.8, "So we designed our own base.", 80), small(1.1, 2.8, "None we could buy did all three:\npayload, self-charging, power for the arms.")))
    S.append(shot("a_turn", kick(0.4, 5.0, "OWN MOBILE BASE"), T(0.4, 5.0, "Turns on the spot."),
                  sub(1.0, 5.0, "780 × 560 mm · two safety wheel drives\nwith certified safe stop and speed limits"), text_maxx=760))
    S.append(shot("a_expl", kick(0.4, 5.0, "WHAT'S INSIDE"), T(0.4, 5.0, "Every part,\noff the shelf."),
                  sub(1.0, 5.0, "laser-cut, bent, bolted\ncertified safety modules"), text_maxx=760))
    if full:
        S.append(photo(f"{AMR}/amr_open.png", 3.6, kick(0.2, 3.6, "POWER"), T(0.2, 3.6, "Two 1.54 kWh\nLFP packs.", size=58),
                       sub(0.6, 3.6, "IEC 62619 · one battery system\nfor the whole robot")))
        S.append(photo(f"{AMR}/amr_cables.png", 3.6, kick(0.2, 3.6, "WIRING"), T(0.2, 3.6, "Power on the left.\nSafety on the right.", size=58),
                       sub(0.6, 3.6, "DIN-rail modules with\ntheir own certificates")))
        S.append(photo(f"{AMR}/giorgio_on_amr.png", 3.6, kick(0.2, 3.6, "SAME GIORGIO"), T(0.2, 3.6, "Bolts straight on.", size=58),
                       sub(0.6, 3.6, "The deck is the torso flange.\nNothing above it changed.")))
    S.append(shot("r_close", kick(0.4, 7.5, "AUTO-DOCKING"), T(0.4, 7.5, "Backs onto its own dock."),
                  sub(1.0, 7.5, "The contacts stay dead\nuntil it is docked.")))
    S.append(card(3.6, big(0.3, 3.6, "Designed for CE marking.", 80),
                  small(1.1, 3.6, "Certified laser scanners, drives and safety controller.\nNo AI in the safety loop.")))
    if full:
        S.append(card(3.2, big(0.3, 3.2, "Made to be built in Italy.", 80), small(1.1, 3.2, "Laser-cut, bent, bolted.")))


def exploded(S):
    S.append(shot("h_expl", kick(0.4, 2.9, "WHAT IT'S MADE OF"), T(0.4, 2.9, "Every part, off the shelf."),
                  labels="lab_expl19.json", label_style="colonne", lab_t0=3.1,
                  names={"testa": ["HEAD", "LED face · 2× 180° fisheye"], "braccio_sx": ["ARMS", "Enactic OpenArm 2.0 · 7+7 DOF"],
                         "braccio_dx": ["HANDS", "grippers · ORCA · AmazingHand"], "busto": ["TORSO + VISION", "Orbbec Gemini 336L stereo depth"],
                         "vassoio": ["KITTING TRAY", "swappable chest module"], "caffe": ["COFFEE MODULE", "24 V capsule machine"],
                         "scanner": ["SAFETY", "2× SICK nanoScan3 · PL d"], "base": ["BASE", "own AMR · 2 safety wheel drives"]}))


def activities(S):
    S.append(card(2.2, big(0.2, 2.2, "What it does.")))
    S.append(shot("l_carico", kick(0.4, 7.0, "KITTING"), T(0.4, 7.0, "Loads its own tray."), sub(1.0, 7.0, "8 parts in 32 s · 3D vision, 3.6 mm mean error.")))
    S.append(shot("l_drive", kick(0.3, 4.0, "TRANSPORT"), T(0.3, 4.0, "Drives to the next station."), sub(0.9, 4.0, "Lines up with the bench within 2 cm.")))
    S.append(shot("l_ins", kick(0.3, 5.8, "ASSEMBLY"), T(0.3, 5.8, "Vision-guided insertion."), sub(0.9, 5.8, "8 of 8 inserted, within 4 mm of the hole centre."), slow=2))
    S.append(shot("l_cross", kick(0.3, 6.5, "SAFETY"), T(0.3, 6.5, "Slows down for you."), sub(0.9, 6.5, "Stops if you get too close. Certified laser fields, not software.")))
    S.append(shot("s_smista", kick(0.4, 7.5, "SORTING"), T(0.4, 7.5, "Sorts by colour."), sub(1.0, 7.5, "6 of 6, without disturbing what's already sorted.")))
    S.append(shot("r_wide", kick(0.5, 7.0, "AUTONOMY"), T(0.5, 3.6, "Battery low?"), T(4.0, 7.0, "It goes home on its own."), step=2))


def training(S):
    S.append(card(2.6, big(0.2, 2.6, "Some skills can't be scripted."), small(0.9, 2.6, "So it learns them in simulation.")))

    def R(t0, t1, text, y, size, w="H", col=(28, 28, 32), **k):
        return T(t0, t1, text, [1180, y], size, w, color=list(col), band=False, align="left", wide_ok=True, **k)
    S.append(shot("v10/rlp2/f_*.jpg", R(0.3, 4.2, "ORCA HAND · UNTRAINED", 770, 26, "X", ACC, track=2), R(0.3, 4.2, "First, it fumbles.", 810, 64)))
    S.append(shot("v10/rld2/f_*.jpg", R(0.3, 9.6, "ORCA HAND · TRAINED", 690, 26, "X", ACC, track=2), R(0.3, 9.6, "Then it learns to\nturn the cube.", 730, 64),
                  R(1.0, 9.6, "236 million attempts\n81 minutes on one GPU", 900, 34, "N", (70, 72, 78))))
    S.append(card(3.0, big(0.3, 3.0, "Opening a cabinet looks easy."), small(1.0, 3.0, "Drawer or door? The arm isn't told which.")))
    S.append(shot("v13/cabinet_baseline_fail/f_*.jpg", kick(0.3, 8.4, "HAND-WRITTEN CONTROLLER"), T(0.3, 8.4, "The door slips away."),
                  sub(1.0, 8.4, "Scripted IK: 36–71% success.\nDoors: 56% at best."), text_maxx=900))
    S.append(shot("v13/cabinet_early_training/f_*.jpg", kick(0.3, 4.6, "LEARNING · EARLY"), T(0.3, 4.6, "First attempts: 1%."), count=150, text_maxx=900))
    S.append(dict(type="card", dur=4.6, bg="stills_v11/cab_curve.png", dim=0.0, xfade=XF,
                  texts=[T(0.3, 4.6, "236 M SIMULATED STEPS · 95 MIN · ONE GPU", [960, 120], 28, "X", color=GREY, band=False, align="center", track=2),
                         T(0.6, 4.6, "Dashed lines: the best hand-written controllers.", [960, 960], 34, "N", color=[205, 207, 212], band=False, align="center")]))
    S.append(shot("v13/cabinet_standalone/f_*.jpg", kick(0.3, 9.6, "OPENARM 2.0 · TRAINED"), T(0.3, 9.6, "Drawers and doors.\nAny handle."),
                  sub(1.0, 9.6, "96–99% success on the plain arm."), text_maxx=900))
    cg = next((f"{d}/cabinet_giorgio/f_*.jpg" for d in ("v19", "v18") if len(glob.glob(f"{d}/cabinet_giorgio/f_*.jpg")) >= 290), None)
    if cg is None:
        OLD.append("cabinet_giorgio")
    W_ = dict(band=False, align="left", wide_ok=True, halo=True)
    S.append(shot(cg or "v13/cabinet_giorgio/f_*.jpg", T(0.3, 9.6, "SAME WEIGHTS · NO RETRAINING", [1180, 858], 26, "X", color=ACC, track=2, **W_),
                  T(0.3, 9.6, "Runs on Giorgio.", [1180, 898], 68, **W_), T(1.0, 9.6, "90–95% success.", [1184, 992], 36, "N", **W_)))


def custom(S):
    S.append(card(2.4, big(0.2, 2.4, "Make it yours."), small(0.8, 2.4, "Swap the face. Swap the hat.")))
    if os.path.exists("v15/custom"):
        S.append(dict(type="frames", glob="v15/custom/f_*.jpg", texts=[], ui=False))
    S.append(card(2.6, big(0.2, 2.6, "One robot. Four setups."), small(0.9, 2.6, "Same base, torso and arms. Swap hands and modules.")))
    for f, a, b, c in (("cfg1_barista", "BARISTA", "Grippers +\ncoffee module", "Brews, carries and serves\non the move."),
                       ("cfg2_logistica", "LOGISTICS", "Grippers +\nkitting tray", "Picks, carries and places\nparts between stations."),
                       ("cfg3_mani_orca", "DEXTEROUS", "2× ORCA Hand\ntendon-driven", "16 DOF per hand, for tools\nand in-hand work."),
                       ("cfg4_lowcost", "BUDGET", "2× Pollen\nAmazingHand", "8 DOF per hand,\nopen and low-cost.")):
        S.append(photo(still(f), 3.2, kick(0.2, 3.2, a), T(0.2, 3.2, b, size=58), sub(0.5, 3.2, c)))


def coffee(S):
    S.append(card(2.6, big(0.3, 2.6, "And most importantly…", 84)))
    S.append(shot("c_bicchiere", kick(0.4, 5.3, "STEP 1"), T(0.4, 5.3, "A cup, from the stack.")))
    S.append(shot("c_eroga", kick(0.3, 4.4, "STEPS 2–4"), T(0.3, 2.0, "A capsule."), T(2.3, 4.4, "Espresso.", size=96)))
    S.append(shot("c_prende", kick(0.4, 5.3, "STEP 5"), T(0.4, 5.3, "Carefully.")))
    S.append(shot("c_consegna", kick(0.3, 7.5, "STEP 6"), T(0.3, 3.4, "Here you go."), T(3.7, 7.5, "Enjoy, Marco.")))
    S.append(photo(still("cfg1_barista"), 4.6, T(0.5, 4.6, "Worst case,\nit's a very expensive\ncoffee machine.", size=56), dim=0.15, zoom=0.05, text_maxx=680))


def hero(S, dur_cut=None):
    k = dict(count=int(dur_cut * FPS)) if dur_cut else {}
    S.append(shot("h_hero", kick(0.8, (dur_cut or 6) - 0.4, "MOBILE BIMANUAL SERVICE ROBOT"), T(0.8, (dur_cut or 6) - 0.4, "Giorgio.", size=120),
                  sub(1.8, (dur_cut or 6) - 0.4, "Two arms, a 3D-vision torso\nand a self-charging base."), text_maxx=680, **k))


def build(name):
    S = []
    if name == "teaser":
        opening(S)
        hero(S, 5.0)
        S.append(shot("l_carico", kick(0.4, 4.6, "KITTING"), T(0.4, 4.6, "Picks the parts\nby itself."), count=150))
        S.append(shot("s_smista", kick(0.4, 4.6, "SORTING"), T(0.4, 4.6, "Sorts by colour."), count=150, start=60))
        S.append(shot("l_drive", kick(0.3, 3.8, "TRANSPORT"), T(0.3, 3.8, "Drives to the next station."), count=120))
        S.append(shot("c_consegna", kick(0.3, 4.6, "BARISTA"), T(0.3, 4.6, "Here you go."), count=150))
        # training: come impara (prima, dopo, curva, sul robot) + invito a imparare
        def R_(t0, t1, text, y, size, w="H", col=(28, 28, 32), **k):
            return T(t0, t1, text, [1180, y], size, w, color=list(col), band=False, align="left", wide_ok=True, **k)
        S.append(shot("v10/rlp2/f_*.jpg", R_(0.2, 2.4, "TRAINING · START", 770, 26, "X", ACC, track=2),
                      R_(0.2, 2.4, "First, it fumbles.", 810, 64), count=75))
        S.append(shot("v10/rld2/f_*.jpg", R_(0.2, 3.4, "TRAINING · 81 MIN LATER", 770, 26, "X", ACC, track=2),
                      R_(0.2, 3.4, "Then it learns.", 810, 64), count=105))
        S.append(dict(type="card", dur=3.0, bg="stills_v11/cab_curve.png", dim=0.0, xfade=0.4,
                      texts=[T(0.2, 3.0, "236 M SIMULATED STEPS · 95 MIN · ONE GPU", [960, 120], 28, "X", color=GREY, band=False, align="center", track=2)]))
        cg_ = next((f"{d}/cabinet_giorgio/f_*.jpg" for d in ("v19", "v18") if len(glob.glob(f"{d}/cabinet_giorgio/f_*.jpg")) >= 290), "v13/cabinet_giorgio/f_*.jpg")
        W2 = dict(band=False, align="left", wide_ok=True, halo=True)
        S.append(shot(cg_, T(0.3, 4.3, "SAME SKILL · ON GIORGIO", [1180, 780], 26, "X", color=ACC, track=2, **W2),
                      T(0.3, 4.3, "Drawers. Doors.\nAny handle.", [1180, 820], 60, **W2), count=135))
        S.append(card(3.0, big(0.2, 3.0, "Learn to train robots."), small(0.9, 3.0, "Same simulations, same training code.\nOne GPU is enough.")))
        S.append(shot("a_turn", kick(0.4, 3.8, "OWN BASE"), T(0.4, 3.8, "Turns. Docks.\nCharges."), count=120, text_maxx=760))
        S.append(shot("r_close", kick(0.3, 2.9, "AUTO-DOCKING"), T(0.3, 2.9, "Goes home on its own."), count=90))
        # personalizzazione 4x (senza zoom), configurazioni 2x
        S.append(card(1.4, big(0.1, 1.4, "Make it yours.")))
        S.append(dict(type="frames", glob="v19/custom_fast/f_*.jpg", texts=[], ui=False, xfade=0.25))
        for f, a_, b_ in (("cfg1_barista", "BARISTA", "Coffee module"), ("cfg2_logistica", "LOGISTICS", "Kitting tray"),
                          ("cfg3_mani_orca", "DEXTEROUS", "2× ORCA Hand"), ("cfg4_lowcost", "BUDGET", "2× AmazingHand")):
            S.append(photo(still(f), 1.6, kick(0.1, 1.6, a_), T(0.1, 1.6, b_, size=58), zoom=0.0, xfade=0.25))
        S.append(card(3.4, big(0.3, 3.4, "Open. All of it."), small(1.0, 3.4, "CAD · code · training · parts list\nFork it. Improve it. Send a pull request.")))
        ending(S, "Coming soon.")
    elif name == "componenti":
        opening(S, short=True)
        hero(S, 4.5)
        exploded(S)
        amr_section(S, full=True)
        ending(S)
    elif name == "attivita":
        opening(S, short=True)
        activities(S)
        ending(S)
    elif name == "training":
        opening(S, short=True)
        training(S)
        S.append(card(3.0, big(0.3, 3.0, "Same skills. Same robot."), small(1.0, 3.0, "Trained once, runs on every Giorgio.")))
        ending(S)
    elif name == "personalizza":
        opening(S, short=True)
        custom(S)
        coffee(S)
        ending(S)
    elif name == "lungo":
        opening(S)
        hero(S)
        exploded(S)
        amr_section(S, full=True)
        activities(S)
        if os.path.exists("tray_v15.py"):
            src = open("tray_v15.py").read().replace('stills_v15/{f}.png', '{still(f)}').replace('shot("v15/t_rear/f_*.jpg"', 'shot("t_rear"') \
                .replace('shot("v15/t_load/f_*.jpg"', 'shot("t_load"').replace('shot("v15/t_pick/f_*.jpg"', 'shot("t_pick"') \
                .replace('shot("v15/t_unload/f_*.jpg"', 'shot("t_unload"')
            exec(src, dict(globals(), S=S))
        training(S)
        custom(S)
        coffee(S)
        S.append(card(3.2, big(0.3, 3.2, "Open. All of it."), small(1.2, 3.2, "CAD · code · training · parts list")))
        ending(S)
    S = [s for s in S if s is not None]
    for sg in S:
        if sg["type"] == "card" and sg.get("bg"):
            for t in sg["texts"]:
                t["halo"] = True
    json.dump(dict(fps=FPS, size=[1920, 1080], music=f"music_{name}.wav", xfade=XF, segments=S),
              open(f"edit_{name}.json", "w"), ensure_ascii=False, indent=1)
    return S


if __name__ == "__main__":
    names = sys.argv[1:] or ["teaser", "componenti", "attivita", "training", "personalizza", "lungo"]
    for n in names:
        OLD.clear()
        S = build(n)
        print(f"{n}: {len(S)} segments" + (f"  (still old base: {', '.join(sorted(set(OLD)))})" if OLD else ""))
