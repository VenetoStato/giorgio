"""Montaggio v15 (inglese): emozionale ma con i dati tecnici dei componenti e delle capacita' (niente cablaggi, niente prezzi).
Titolo grande + occhiello arancio + una riga tecnica. Le sezioni di training OpenArm si leggono da rl_v13.json (se c'e').
Genera edit_v13.json."""
import glob, json, os
BLACK, WHITE, GREY, ACC = [6, 6, 8], [245, 245, 242], [160, 162, 168], [255, 122, 26]
FPS, XF = 30, 0.6


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


def shot(path, *texts, **k):
    for t in texts:                                   # alone scuro: leggibile anche sulle scene chiare
        if t.get("color") in (WHITE, ACC) and not t.get("wide_ok"):
            t["halo"] = True
    d = dict(type="frames", glob=path if "*" in path else f"v15/{path}/f_*.jpg", texts=list(texts), ui=False); d.update(k); return d


S = []
# --- apertura
S.append(card(2.6, big(0.3, 2.6, "Italy deserves its own robot.", 80)))
S.append(card(1.9, big(0.2, 1.9, "Not a Ferrari.")))
S.append(card(3.0, big(0.2, 3.0, "A Fiat Panda."), small(1.0, 3.0, "Simple. Open. Fixable.")))
S.append(shot("h_hero", kick(0.8, 5.6, "MOBILE BIMANUAL SERVICE ROBOT"), T(0.8, 5.6, "Giorgio.", size=120),
              sub(1.8, 5.6, "Two arms, a 3D-vision torso\nand a self-charging base."), text_maxx=680))
S.append(shot("h_face", kick(0.6, 5.6, "FACE"), T(0.6, 5.6, "The moustache is\nnon-negotiable."),
              sub(1.5, 5.6, "32×16 LED face · round display eyes\n180° fisheye cameras, front and back.")))
# --- di cosa e' fatto: esploso con cartellini (il titolo esce prima che arrivino i cartellini)
S.append(shot("h_expl", kick(0.4, 2.9, "WHAT IT'S MADE OF"), T(0.4, 2.9, "Every part, off the shelf."),
              labels="lab_expl15.json", label_style="colonne", lab_t0=3.1,
              names={"testa": ["HEAD", "LED face · 2× 180° fisheye"], "braccio_sx": ["ARMS", "Enactic OpenArm 2.0 · 7+7 DOF"],
                     "braccio_dx": ["HANDS", "grippers · ORCA · AmazingHand"], "busto": ["TORSO + VISION", "Orbbec Gemini 336L stereo depth"],
                     "vassoio": ["KITTING TRAY", "swappable chest module"], "caffe": ["COFFEE MODULE", "24 V capsule machine"],
                     "scanner": ["SAFETY", "2× SICK nanoScan3 · PL d"], "base": ["BASE", "Slamtec Poseidon · omnidirectional"]}))
# --- anatomia leggibile: un gruppo alla volta con i dati del componente
ANAT = {"base": ("MOBILE BASE", "Slamtec Poseidon", "4-wheel steering · 150 kg rated payload\ndocks and charges itself"),
        "power": ("BATTERY", "48 V LiFePO4, 1.44 kWh", "6–7 h of work\ncharged from the base's 48 V output"),
        "electronics": ("BRAIN", "NVIDIA Jetson\nOrin NX 16 GB", "vision, planning and learned\nskills, all on board"),
        "scanners": ("SAFETY", "2× SICK nanoScan3", "laser scanners · 360° protective\nfields · certified PL d stop"),
        "structure": ("STRUCTURE", "Aluminium column and frame", "laser-cut sheet + 80×80 profile"),
        "arms": ("ARMS", "Enactic OpenArm 2.0", "7+7 DOF · quasi-direct-drive\n3 kg per arm · open hardware"),
        "head": ("EYES", "Orbbec Gemini 336L", "stereo depth for the hands\n+ 2× 180° fisheye: 360° awareness"),
        "coffee": ("COFFEE MODULE", "24 V capsule machine", "with a cup shuttle\nbrews on the move"),
        "tray": ("KITTING TRAY", "Swappable chest module", "carries parts between stations"),
        "shells": ("SHELLS", "3D-printed PA12", "the only part we actually designed")}
if os.path.exists("v11/anat/gruppi.json"):          # un segmento per gruppo, rallentato 2x: il tempo di leggere
    G = json.load(open("v11/anat/gruppi.json"))
    for k_, g_ in enumerate(G["groups"]):
        if g_ in ("structure", "tray", "shells"):
            continue
        a_, b_, c_ = ANAT[g_]
        d_ = 2 * G["hold"] / 30
        S.append(dict(type="frames", glob="v11/anat/f_*.jpg", start=G["start"] + k_ * G["hold"], count=G["hold"], slow=2, ui=False, xfade=0.35, text_maxx=700,
                      texts=[kick(0.5, d_, a_), T(0.5, d_, b_, size=50), dict(sub(0.7, d_, c_), size=32)]))
# --- configurazioni: cosa cambia e a cosa serve
S.append(card(2.6, big(0.2, 2.6, "One robot. Four setups."), small(0.9, 2.6, "Same base, torso and arms. Swap hands and modules.")))
for f, a, b, c in (("cfg1_barista", "BARISTA", "Grippers +\ncoffee module", "Brews, carries and serves\non the move."),
                   ("cfg2_logistica", "LOGISTICS", "Grippers +\nkitting tray", "Picks, carries and places\nparts between stations."),
                   ("cfg3_mani_orca", "DEXTEROUS", "2× ORCA Hand\ntendon-driven", "16 DOF per hand, for tools\nand in-hand work."),
                   ("cfg4_lowcost", "BUDGET", "2× Pollen\nAmazingHand", "8 DOF per hand,\nopen and low-cost.")):
    S.append(dict(type="card", dur=3.2, bg=f"stills_v15/{f}.png", dim=0.0, zoom=0.04, xfade=0.4, text_maxx=700,
                  texts=[kick(0.2, 3.2, a), T(0.2, 3.2, b, size=58), sub(0.5, 3.2, c)]))
# --- cosa fa (numeri dalle simulazioni)
S.append(card(2.2, big(0.2, 2.2, "What it does.")))
S.append(shot("l_carico", kick(0.4, 7.0, "KITTING"), T(0.4, 7.0, "Loads its own tray."), sub(1.0, 7.0, "8 parts in 32 s · 3D vision, 3.6 mm mean error.")))
S.append(shot("l_drive", kick(0.3, 4.0, "TRANSPORT"), T(0.3, 4.0, "Drives to the next station."), sub(0.9, 4.0, "Lines up with the bench within 2 cm.")))
S.append(shot("v15/l_ins/f_*.jpg", kick(0.3, 5.8, "ASSEMBLY"), T(0.3, 5.8, "Vision-guided insertion."), sub(0.9, 5.8, "8 of 8 inserted, within 4 mm of the hole centre."), slow=2))
S.append(shot("l_cross", kick(0.3, 6.5, "SAFETY"), T(0.3, 6.5, "Slows down for you."), sub(0.9, 6.5, "Stops if you get too close. Certified laser fields, not software.")))
S.append(shot("l_oper", kick(0.4, 7.5, "COLLABORATION"), T(0.4, 7.5, "Next to people.\nNot instead of them.")))
S.append(shot("s_smista", kick(0.4, 7.5, "SORTING"), T(0.4, 7.5, "Sorts by colour."), sub(1.0, 7.5, "6 of 6, without disturbing what's already sorted.")))
S.append(shot("r_wide", kick(0.5, 7.0, "AUTONOMY"), T(0.5, 3.6, "Battery low?"), T(4.0, 7.0, "It goes home on its own."), step=2))
S.append(shot("r_close", kick(0.4, 7.5, "AUTO-DOCKING"), T(0.4, 7.5, "Backs onto its charging dock."), sub(1.0, 7.5, "10 of 10 simulated dockings · within 2 mm and 0.3°.")))
if os.path.exists("tray_v15.py"):                    # vassoi davanti/dietro, scatole: segmenti definiti in tray_v15.py
    exec(open("tray_v15.py").read())
# --- impara: solo abilita' dove l'apprendimento serve davvero
S.append(card(2.6, big(0.2, 2.6, "Some skills can't be scripted."), small(0.9, 2.6, "So it learns them in simulation.")))
# la mano occupa la sinistra: testi scuri a destra, sul fondo bianco
def R(t0, t1, text, y, size, w="H", col=(28, 28, 32), **k):
    return T(t0, t1, text, [1180, y], size, w, color=list(col), band=False, align="left", wide_ok=True, **k)
S.append(shot("v10/rlp2/f_*.jpg", R(0.3, 4.2, "ORCA HAND · UNTRAINED", 770, 26, "X", ACC, track=2), R(0.3, 4.2, "First, it fumbles.", 810, 64)))
S.append(shot("v10/rld2/f_*.jpg", R(0.3, 9.6, "ORCA HAND · TRAINED", 690, 26, "X", ACC, track=2), R(0.3, 9.6, "Then it learns to\nturn the cube.", 730, 64),
              R(1.0, 9.6, "236 million attempts\n81 minutes on one GPU", 900, 34, "N", (70, 72, 78))))
# OpenArm 2.0: aprire un mobile (cassetto o anta, il robot non sa quale) - qui lo script a mano non basta. Numeri: rl_openarm/README.md sez. 8
S.append(card(3.0, big(0.3, 3.0, "Opening a cabinet looks easy."), small(1.0, 3.0, "Drawer or door? The arm isn't told which.")))
S.append(shot("v13/cabinet_baseline_fail/f_*.jpg", kick(0.3, 8.4, "HAND-WRITTEN CONTROLLER"), T(0.3, 8.4, "The door slips away."),
              sub(1.0, 8.4, "Scripted IK: 36–71% success.\nDoors: 56% at best."), text_maxx=900))
S.append(shot("v13/cabinet_early_training/f_*.jpg", kick(0.3, 4.6, "LEARNING · EARLY"), T(0.3, 4.6, "First attempts: 1%."), count=150, text_maxx=900))
S.append(dict(type="card", dur=4.6, bg="stills_v11/cab_curve.png", dim=0.0, xfade=XF,
              texts=[T(0.3, 4.6, "236 M SIMULATED STEPS · 95 MIN · ONE GPU", [960, 120], 28, "X", color=GREY, band=False, align="center", track=2),
                     T(0.6, 4.6, "Dashed lines: the best hand-written controllers.", [960, 960], 34, "N", color=[205, 207, 212], band=False, align="center")]))
S.append(shot("v13/cabinet_standalone/f_*.jpg", kick(0.3, 9.6, "OPENARM 2.0 · TRAINED"), T(0.3, 9.6, "Drawers and doors.\nAny handle."),
              sub(1.0, 9.6, "96–99% success on the plain arm."), text_maxx=900))
W_ = dict(band=False, align="left", wide_ok=True, halo=True)      # su Giorgio la base e' in basso a sinistra: testi a destra
S.append(shot("v13/cabinet_giorgio/f_*.jpg", T(0.3, 9.6, "SAME WEIGHTS · NO RETRAINING", [1180, 858], 26, "X", color=ACC, track=2, **W_),
              T(0.3, 9.6, "Runs on Giorgio.", [1180, 898], 68, **W_), T(1.0, 9.6, "90–95% success.", [1184, 992], 36, "N", **W_)))
# --- personalizzazione: facce e cappelli (immagini A/B alternate, v15/custom creato da custom_v15.py)
if os.path.exists("v15/custom"):
    S.append(card(2.4, big(0.2, 2.4, "Make it yours."), small(0.8, 2.4, "Swap the face. Swap the hat.")))
    S.append(dict(type="frames", glob="v15/custom/f_*.jpg", texts=[], ui=False))
# --- caffe'
S.append(card(2.6, big(0.3, 2.6, "And most importantly…", 84)))
S.append(shot("c_bicchiere", kick(0.4, 5.3, "STEP 1"), T(0.4, 5.3, "A cup, from the stack.")))
S.append(shot("c_eroga", kick(0.3, 4.4, "STEPS 2–4"), T(0.3, 2.0, "A capsule."), T(2.3, 4.4, "Espresso.", size=96)))
S.append(shot("c_prende", kick(0.4, 5.3, "STEP 5"), T(0.4, 5.3, "Carefully.")))
S.append(shot("c_consegna", kick(0.3, 7.5, "STEP 6"), T(0.3, 3.4, "Here you go."), T(3.7, 7.5, "Enjoy, Marco.")))
S.append(dict(type="card", dur=4.6, bg="stills_v15/cfg1_barista.png", dim=0.15, zoom=0.05,
              texts=[T(0.5, 4.6, "Worst case,\nit's a very expensive\ncoffee machine.", size=56)], text_maxx=680))
# --- finale
S.append(card(3.2, big(0.3, 3.2, "Open. All of it."), small(1.2, 3.2, "CAD · code · training · parts list")))
S.append(card(3.6, big(0.3, 3.6, "Want to know more?"), small(1.2, 3.6, "github.com/VenetoStato/giorgio")))
if os.path.exists("marchi_v14.txt"):                  # nota sui marchi di terzi (testo dalla verifica legale)
    S.append(card(4.0, T(0.3, 4.0, open("marchi_v14.txt").read().strip(), "center", 26, "N", color=GREY, band=False)))
S.append(card(5.0, images=[dict(path="logo/logo_full_chiaro.png", t0=0.3, t1=5.0, pos=[960, 500], w=1100)]))
for sg in S:                                          # ombreggiatura anche sui testi dei cartelli con foto
    if sg["type"] == "card" and sg.get("bg"):
        for t in sg["texts"]:
            t["halo"] = True
json.dump(dict(fps=FPS, size=[1920, 1080], music="music_v15.wav", xfade=XF, segments=S),
          open("edit_v15.json", "w"), ensure_ascii=False, indent=1)
print(len(S), "segmenti")
