"""Montaggio v12 (inglese, stile prodotto/emozionale): niente parti tecniche, prezzi o cablaggi (stanno su GitHub).
Testi brevi, un solo titolo alla volta, niente cornice HUD. Genera edit_v12.json."""
import glob, json
BLACK, WHITE, GREY, ACC = [6, 6, 8], [245, 245, 242], [160, 162, 168], [255, 122, 26]
FPS, XF = 30, 0.6


def n_frames(g, slow=1):
    return len(glob.glob(g)) * slow / FPS


def T(t0, t1, text, pos="ll", size=72, w="H", **k):
    d = dict(t0=t0, t1=t1, text=text, pos=pos, size=size, weight=w, align="left" if pos in ("ll", "llsub") else "center",
             shadow=False, band=pos == "ll", color=WHITE)
    d.update(k); return d


def sub(t0, t1, text, **k):
    return T(t0, t1, text, "llsub", 40, "N", color=WHITE, band=False, **k)


def card(dur, *texts, **k):
    d = dict(type="card", dur=dur, color=BLACK, texts=list(texts), xfade=XF); d.update(k); return d


def big(t0, t1, text, size=92, **k):
    return T(t0, t1, text, "center", size, **k)


def small(t0, t1, text, **k):
    return T(t0, t1, text, "sub", 40, "N", color=[205, 207, 212], **k)


def shot(name, *texts, root="v11", **k):
    g = f"{root}/{name}/f_*.jpg"
    for t in texts:                                  # ombra scura sui titoli bianchi: leggibili anche sulle scene chiare
        if t.get("color") == WHITE:
            t["halo"] = True
    d = dict(type="frames", glob=g, texts=list(texts), ui=False); d.update(k); return d


S = []
# --- apertura
S.append(card(2.8, big(0.3, 2.8, "Italy deserves its own robot.", 80)))
S.append(card(2.0, big(0.2, 2.0, "Not a Ferrari.")))
S.append(card(3.2, big(0.2, 3.2, "A Fiat Panda."), small(1.1, 3.2, "Simple. Open. Fixable.")))
S.append(shot("h_hero", T(0.8, 5.6, "Giorgio.", size=120), sub(1.8, 5.6, "A robot that works next to you.")))
S.append(shot("h_face", T(0.6, 5.6, "It looks you in the eye."), sub(1.6, 5.6, "And it has a moustache.")))
S.append(shot("h_expl", T(1.0, 7.5, "Every part,\noff the shelf."), sub(2.0, 7.5, "Put together with care.")))
for f, a in (("cfg1_barista", "Barista."), ("cfg2_logistica", "Logistics."), ("cfg3_mani_orca", "Dexterous."), ("cfg4_lowcost", "Simple.")):
    S.append(dict(type="card", dur=2.4, bg=f"stills_v11/{f}.png", dim=0.0, zoom=0.04, xfade=0.4,
                  texts=[T(0.2, 2.4, a, size=84)]))
S.append(card(2.2, big(0.2, 2.2, "Give it a job.")))
S.append(shot("l_carico", T(0.4, 7.0, "It loads itself.")))
S.append(shot("l_drive", T(0.3, 4.0, "Goes where it's needed.")))
S.append(shot("l_ins", T(0.3, 5.6, "Down to the millimetre."), slow=2))
S.append(shot("l_cross", T(0.3, 6.5, "Slows down for you.")))
S.append(shot("l_oper", T(0.4, 7.5, "Next to people.\nNot instead of them.")))
S.append(shot("s_smista", T(0.4, 7.5, "Sorts by colour.")))
S.append(shot("r_wide", T(0.5, 4.5, "Tired?"), T(5.0, 14.5, "It goes home on its own."), step=2))
S.append(shot("r_close", T(0.4, 7.5, "And plugs itself in.")))
# --- impara
S.append(card(2.4, big(0.2, 2.4, "It learns.")))
DARK = dict(pos=[1240, 860], color=[28, 28, 32], band=False, align="left")   # scritta scura a destra, sul fondo bianco (a sinistra c'e' la mano)
S.append(shot("rlp2", T(0.3, 4.2, "First, it fumbles.", **DARK), root="v10"))
S.append(shot("rld2", T(0.3, 9.6, "Then it gets it.", **DARK), root="v10"))
S.append(shot("oa_std", T(0.4, 9.8, "Taught on an OpenArm."), sub(1.2, 9.8, "Grasp and lift, learned from scratch.")))
S.append(shot("oa_gio", T(0.4, 9.8, "Same brain. Inside Giorgio."), sub(1.2, 9.8, "No retraining.")))
# --- caffe'
S.append(card(2.8, big(0.3, 2.8, "And most importantly…", 84)))
S.append(shot("c_bicchiere", T(0.4, 5.3, "A cup.")))
S.append(shot("c_eroga", T(0.3, 2.0, "A capsule."), T(2.3, 4.4, "Espresso.", size=96)))
S.append(shot("c_prende", T(0.4, 5.3, "Carefully.")))
S.append(shot("c_consegna", T(0.3, 3.4, "Here you go."), T(3.7, 7.5, "Enjoy, Marco.")))
S.append(dict(type="card", dur=4.6, bg="stills_v11/cfg1_barista.png", dim=0.15, zoom=0.05,
              texts=[T(0.5, 4.6, "Worst case,\nit's a very nice coffee machine.", size=64)]))
# --- finale
S.append(card(3.2, big(0.3, 3.2, "Open. All of it."), small(1.2, 3.2, "CAD · code · training · parts list")))
S.append(card(3.6, big(0.3, 3.6, "Want to know more?"), small(1.2, 3.6, "github.com/VenetoStato/giorgio")))
S.append(card(5.0, images=[dict(path="logo/logo_full_chiaro.png", t0=0.3, t1=5.0, pos=[960, 500], w=1100)]))
json.dump(dict(fps=FPS, size=[1920, 1080], music="music_v12.wav", xfade=XF, segments=S),
          open("edit_v12.json", "w"), ensure_ascii=False, indent=1)
print(len(S), "segmenti")
