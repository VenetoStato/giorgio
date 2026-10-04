"""Volto di Giorgio su matrice LED RGB 64 x 32 (pannello flessibile P2.5, 160 x 80 mm, dietro la visiera fume').
Disegno vettoriale campionato sui LED (bordi morbidi), poi immagine "a punti" per il render.
Codici espressione: 0 neutro, 1 contento, 2 caffe', 3 stop, 4 pensa, 5 cuori, 6 attento.
"""
import math

import numpy as np

NX, NY = 64, 32
COL = {11: (235, 240, 255), 12: (235, 228, 205), 13: (225, 245, 255), 14: (255, 60, 200), 10: (150, 225, 255), 8: (255, 205, 50), 9: (140, 235, 255), 7: (90, 255, 140), 0: (110, 205, 255), 1: (140, 235, 255), 2: (255, 165, 55), 3: (255, 45, 35), 4: (175, 150, 255), 5: (255, 85, 160), 6: (255, 205, 50)}
YY, XX = np.mgrid[0:NY, 0:NX].astype(np.float32) + 0.5


def _cov(sdf, w=0.55):
    """copertura di un LED da una distanza con segno (negativa = dentro)"""
    return np.clip(0.5 - sdf / (2 * w), 0.0, 1.0)


def ellipse(cx, cy, rx, ry):
    k = np.sqrt(((XX - cx) / max(rx, 1e-3)) ** 2 + ((YY - cy) / max(ry, 1e-3)) ** 2)
    return _cov((k - 1.0) * min(rx, ry))


def segment(ax, ay, bx, by, r):
    px, py = XX - ax, YY - ay; dx, dy = bx - ax, by - ay
    h = np.clip((px * dx + py * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return _cov(np.hypot(px - dx * h, py - dy * h) - r)


def polyline(pts, r):
    m = np.zeros((NY, NX), np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        m = np.maximum(m, segment(ax, ay, bx, by, r))
    return m


def heart(cx, cy, s):
    """cuore pixel-art: due cerchi + triangolo verso il basso"""
    k = s / 5.5
    m = np.maximum(ellipse(cx - 2.5 * k, cy - 1.4 * k, 2.9 * k, 2.9 * k), ellipse(cx + 2.5 * k, cy - 1.4 * k, 2.9 * k, 2.9 * k))
    ax, ay, bx, by, qx, qy = cx - 5.3 * k, cy - 0.6 * k, cx + 5.3 * k, cy - 0.6 * k, cx, cy + 5.6 * k
    gx_, gy_ = (ax + bx + qx) / 3, (ay + by + qy) / 3

    def edge(x0, y0, x1, y1):                            # distanza con segno dal lato, interno negativo
        nx, ny = y1 - y0, -(x1 - x0); n = math.hypot(nx, ny)
        sgn = 1.0 if ((gx_ - x0) * nx + (gy_ - y0) * ny) < 0 else -1.0
        return sgn * ((XX - x0) * nx + (YY - y0) * ny) / n
    sd = np.maximum(np.maximum(edge(ax, ay, qx, qy), edge(qx, qy, bx, by)), edge(bx, by, ax, ay))
    return np.maximum(m, _cov(sd))


def moustache(lift=0.0, droop=0.0, wig=0.0):
    """baffo a manubrio: tubo spesso al centro, assottigliato, punte arricciate verso l'alto"""
    m = np.zeros((NY, NX), np.float32)
    for sd in (1, -1):
        prev = None
        for s in np.linspace(0, 1, 26):
            x = 32 + sd * (1.2 + 15.5 * s)
            y = 24.2 - 1.6 * math.sin(math.pi * min(s / 0.7, 1.0)) - (4.5 + 2.5 * lift) * max(0.0, (s - 0.68) / 0.32) ** 2
            y += droop * 5.0 * s ** 2 + wig * math.sin(s * 6.0) * s
            x -= sd * 2.0 * max(0.0, (s - 0.85) / 0.15) ** 2         # ricciolo
            r = (0.55 + 2.0 * (1 - s) ** 0.8) * BOLD
            if prev is not None:
                m = np.maximum(m, segment(prev[0], prev[1], x, y, r))
            prev = (x, y)
    return m


BOLD = 1.0


def draw(code, gx=0.0, gy=0.0, blink=0.0, t=0.0):
    """matrice 32 x 64 x 3 (0..1) per lo stato del volto"""
    code = int(code)
    ex, ey = 3.0 * gx, -2.0 * gy
    eyes = np.zeros((NY, NX), np.float32)
    extra = np.zeros((NY, NX), np.float32)
    lift = droop = wig = 0.0
    for cx in (20.5, 43.5):
        cx += ex; cy = 11.0 + ey
        if code == 1:                                        # contento: ^ ^
            eyes = np.maximum(eyes, polyline([(cx - 5.5, cy + 2.5), (cx, cy - 2.5), (cx + 5.5, cy + 2.5)], 1.15 * BOLD))
        elif code == 5:                                      # cuori
            eyes = np.maximum(eyes, heart(cx, cy, 5.8 + 0.5 * math.sin(t * 9)))
        else:
            ry = {2: 4.2, 3: 4.6, 6: 4.0}.get(code, 6.2) * (1 - 0.88 * blink)
            rx = {3: 4.4}.get(code, 5.2)
            e = ellipse(cx, cy + (1.5 if code == 3 else 0.0), rx, max(ry, 0.6))
            if code == 2:                                    # caffe': palpebra rilassata (occhio a mezzaluna)
                e *= (YY > cy - 1.2).astype(np.float32)
            eyes = np.maximum(eyes, e)
            if code in (0, 4, 6) and blink < 0.5:            # riflesso: due LED spenti
                eyes *= 1 - ellipse(cx - 1.8, cy - 2.4, 1.0, 1.0) * 0.85
        if code == 3:                                        # sopracciglia preoccupate
            sd = 1 if cx < 32 else -1
            extra = np.maximum(extra, segment(cx - 5 * sd, cy - 5.4, cx + 3.5 * sd, cy - 7.9, 0.6))   # dispiaciuto: interno in alto
    if code == 1:
        lift = 1.0
    elif code == 3:
        droop = 1.0
    elif code == 2:
        wig = 0.9 * math.sin(t * 7)
    elif code == 4:                                          # pensa: tre puntini che si accendono in sequenza
        for k in range(3):
            on = 0.35 + 0.65 * (int(t * 3) % 3 == k)
            extra = np.maximum(extra, ellipse(27 + 5 * k, 3.2, 1.2, 1.2) * on)
    elif code == 5:
        lift = 0.6
    must = moustache(lift, droop, wig)
    c = np.array(COL.get(code, COL[0]), np.float32) / 255.0
    cm = c * 0.92 + 0.08                                     # baffi un filo piu' chiari
    img = eyes[..., None] * c + extra[..., None] * c * 0.9
    img = np.maximum(img, must[..., None] * cm)
    return np.clip(img, 0, 1)


def big(img):
    """matrice a LED grandi: 32 x 16 (passo 5 mm): un LED si accende se il disegno 64 x 32 lo copre (forme piene, nette)"""
    b = img.reshape(NY // 2, 2, NX // 2, 2, 3)
    mx, mn = b.max((1, 3)), b.mean((1, 3))
    return np.clip(0.75 * mx + 0.6 * mn, 0, 1)


def draw_big(code, gx=0.0, gy=0.0, blink=0.0, t=0.0):
    global BOLD
    BOLD = 1.25
    try:
        return big(draw(code, gx, gy, blink, t))
    finally:
        BOLD = 1.0


def led_image_big(led, S=16, off=0.05):
    """LED grandi a cupola: disco pieno, alone, riflesso speculare; i LED spenti si vedono (griglia del pannello)"""
    ny, nx = led.shape[:2]
    u = (np.arange(S) + 0.5) / S - 0.5
    d = np.hypot(u[None, :], u[:, None])
    dot = np.clip((0.40 - d) / 0.05, 0, 1)
    core = np.exp(-(d / 0.22) ** 2)                           # centro piu' brillante (cupola)
    halo = np.exp(-(d / 0.42) ** 2) * 0.45
    spec = np.exp(-(np.hypot(u[None, :] + 0.12, u[:, None] + 0.14) / 0.07) ** 2)   # riflesso della cupola
    lit = np.maximum(dot * (0.65 + 0.35 * core), halo)
    big_ = np.kron(led, np.ones((S, S, 1), np.float32))
    t = np.tile(lit, (ny, nx))[..., None]
    rgb = big_ * t * 1.15
    rgb += off * np.tile(dot, (ny, nx))[..., None] * np.array([0.55, 0.6, 0.65], np.float32)    # LED spenti
    rgb += 0.10 * np.tile(spec * dot, (ny, nx))[..., None]                                       # cupole lucide
    out = np.ones((ny * S, nx * S, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    return out


def led_image(led, S=8, off=0.035):
    """immagine (NY*S, NX*S, 4) float: ogni LED e' un punto rotondo; i LED spenti restano appena visibili (si capisce che e' una matrice)"""
    u = (np.arange(S) + 0.5) / S - 0.5
    d = np.hypot(u[None, :], u[:, None])
    dot = np.clip((0.40 - d) / 0.06, 0, 1)                   # disco del LED
    halo = np.exp(-(d / 0.36) ** 2) * 0.35                   # alone
    tile = np.maximum(dot, halo)
    big = np.kron(led, np.ones((S, S, 1), np.float32))       # (NY*S, NX*S, 3)
    t = np.tile(tile, (NY, NX))[..., None]
    rgb = big * t + off * np.tile(dot, (NY, NX))[..., None] * np.array([0.6, 0.65, 0.7], np.float32)
    out = np.ones((NY * S, NX * S, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    return out


if __name__ == "__main__":                                   # anteprima delle espressioni
    from PIL import Image
    tiles = []
    for code in range(7):
        im = led_image_big(draw_big(code, 0.2, 0.0, 0.0, 0.4))
        tiles.append((im[..., :3] * 255).astype(np.uint8))
    tiles.append((led_image_big(draw_big(0, -0.6, 0.3, 0.7, 0.0))[..., :3] * 255).astype(np.uint8))
    rows = [np.concatenate(tiles[i:i + 4], 1) for i in (0, 4)]
    Image.fromarray(np.concatenate(rows, 0)).save("/tmp/claude-1000/-home-gpitton/73890d0e-b4dc-4184-b008-e491487358ce/scratchpad/led_preview.png")
    print("ok")


# ---------------------------------------------------------------- pixel-art disegnata a mano per la matrice 32 x 16 (LED grandi)
def _bm(rows):
    return np.array([[1.0 if c == "#" else 0.45 if c == "+" else 0.0 for c in r] for r in rows], np.float32)


EYE = {"open": _bm([".####.", "######", "######", "######", "######", "######", ".####."]),
       "happy": _bm(["..##..", ".####.", "##..##", "#....#"]),
       "relax": _bm(["######", "######", ".####."]),
       "small": _bm([".###.", "#####", "#####", "#####", ".###."]),
       "squint": _bm([".####.", "######", ".####."]),
       "heart": _bm([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]),
       "shut": _bm(["######"])}
MARIO = _bm(["...######....######...", ".#########..#########.", "######################", "######################",
             "###.####.####.####.###", "..##..##..##..##..##.."])     # baffoni folti con i riccioli in basso
MUST = {"neutral": _bm(["#......................#", "##....................##", ".####......##......####.", "..######..####..######..",
                        "....################...."]),
        "up": _bm(["#......................#", "##....................##", ".##..................##.", ".####......##......####.",
                   "..######..####..######..", "....################...."]),
        "down": _bm(["....################....", "..######..####..######..", ".####..............####.", "##....................##",
                     "#......................#"])}


# baffi a manubrio, sottili con le punte arricciate (NON i baffoni folti alla Mario: stile "mario" tenuto solo per i render vecchi)
# baffi a manubrio: spessi sotto il naso, sottili verso l'esterno, punte arricciate all'insu'
MANUBRIO = {
    "neutral": _bm(['#........##..##........#', '#....######..######....#', '.#.########..########.#.', '..#####..........#####..']),
    "up": _bm(['#......................#', '#........##..##........#', '.#..#######..#######..#.', '..#######......#######..']),
    "down": _bm(['.........##..##.........', '.....######..######.....', '...########..########...', '.####..............####.', '##....................##']),
}
STYLE = "mario"          # volto di default: baffoni pixel (piace al proprietario); "manubrio" = variante sottile



def _fx(code, t):
    """facce speciali (omaggi in pixel art) 16 x 32 x 3; None se il codice non e' speciale"""
    yy, xx = np.mgrid[0:16, 0:32] + 0.5
    if code == 11:                                            # scheletro sorridente (stile Undertale)
        m = np.ones((16, 32), np.float32) * 0.9
        for ex in (10.0, 22.0):
            m[((xx - ex) / 3.2) ** 2 + ((yy - 5.5) / 3.0) ** 2 <= 1.0] = 0.0
            if int(t * 1.5) % 4 != 3:                          # pupille bianche piccole (ogni tanto spariscono)
                m[5, int(ex)] = 1.0
        g = (((xx - 16) / 11.5) ** 2 + ((yy - 8.5) / 4.6) ** 2 <= 1.0) & (yy > 10.5) & (yy < 13.5)
        m[g] = 0.0
        m[11:13, 6:27] = np.where(m[11:13, 6:27] == 0.0, 0.0, m[11:13, 6:27])
        m[12, 6:27] = 0.0
        for x in range(8, 26, 3):                              # denti: separatori verticali
            m[11:13, x] = 0.0
        m[11, 7:26] = np.where((np.arange(7, 26) % 3) == 2, 0.0, 0.9)
        m[14:16, :] = 0.0; m[:, :2] = 0.0; m[:, 30:] = 0.0    # contorno arrotondato del cranio
        m[0, :5] = m[0, 27:] = 0.0; m[1, :3] = m[1, 29:] = 0.0; m[13, :4] = m[13, 28:] = 0.0
        return np.clip(m[..., None] * np.array(COL[11], np.float32) / 255.0, 0, 1)
    if code == 12:                                            # occhi a binocolo (stile WALL-E)
        m = np.zeros((16, 32), np.float32)
        tilt = 0.6 * math.sin(t * 1.3)
        for k, ex in enumerate((9.0, 23.0)):
            sgn = 1 if k == 0 else -1
            yc = 7.5 + sgn * 0.0
            outer = (np.abs(xx - ex) / 6.2) ** 4 + (np.abs(yy - yc) / 6.0) ** 4 <= 1.0
            inner = (np.abs(xx - ex) / 5.0) ** 4 + (np.abs(yy - yc) / 4.8) ** 4 <= 1.0
            droop = (yy < 3.2 + sgn * (xx - ex) * 0.35 + tilt)   # palpebra inclinata verso l'interno
            m[outer & ~inner & ~droop] = 0.75
            lens = ((xx - ex) ** 2 + (yy - yc - 0.5) ** 2) <= 2.6 ** 2
            ring = lens & (((xx - ex) ** 2 + (yy - yc - 0.5) ** 2) >= 1.4 ** 2)
            m[ring & ~droop] = 1.0
            m[int(yc - 1), int(ex + 1)] = 1.0                  # riflesso
        return np.clip(m[..., None] * np.array(COL[12], np.float32) / 255.0, 0, 1)
    if code == 13:                                            # maschera a LED (stile Watch Dogs): occhi > < e bocca a zig-zag
        m = np.zeros((16, 32), np.float32)
        for i in range(4):
            m[2 + i, 6 + i] = m[8 - i, 6 + i] = 1.0           # >
            m[2 + i, 25 - i] = m[8 - i, 25 - i] = 1.0         # <
            m[2 + i, 7 + i] = m[8 - i, 7 + i] = 1.0
            m[2 + i, 24 - i] = m[8 - i, 24 - i] = 1.0
        ph = int(t * 6) % 2
        for x in range(5, 27):
            y = 11 + ((x + ph) % 4 if (x + ph) % 4 < 2 else 3 - (x + ph) % 4)
            m[y, x] = 1.0; m[min(15, y + 1), x] = 0.5
        return np.clip(m[..., None] * np.array(COL[13], np.float32) / 255.0, 0, 1)
    if code == 14:                                            # neon glitch (stile cyberpunk): occhi a taglio, scansione, aberrazione
        m = np.zeros((16, 32), np.float32)
        for k, ex in enumerate((10, 22)):
            sgn = 1 if k == 0 else -1
            for i in range(7):
                x = ex - 3 + i
                y = 5 + int(round(sgn * (i - 3) * 0.35))
                m[y, x] = 1.0; m[y + 1, x] = 0.8
        m[11, 9:23] = 1.0; m[12, 12:20] = 0.6
        sh = np.zeros_like(m)
        gl = int(t * 8) % 16                                   # riga che "salta"
        m[gl] = np.roll(m[gl], 2)
        m[1::2] *= 0.75                                        # righe di scansione
        rgb = np.zeros((16, 32, 3), np.float32)
        rgb += m[..., None] * np.array(COL[14], np.float32) / 255.0
        rgb[..., 1:] += 0.6 * np.roll(m, -1, axis=1)[..., None] * np.array([0.9, 1.0], np.float32)   # fantasma ciano
        return np.clip(rgb, 0, 1)
    return None

def draw_px(code, gx=0.0, gy=0.0, blink=0.0, t=0.0):
    """volto 16 x 32 x 3 (0..1) in pixel-art"""
    code = int(code)
    fx = _fx(code, t)
    if fx is not None:
        return fx
    img = np.zeros((16, 32), np.float32)
    if code == 10:                                            # "retro": schermo acceso, lineamenti scuri, sorriso enorme (omaggio di stile)
        img[:] = 0.85
        yy, xx = np.mgrid[0:16, 0:32] + 0.5
        for ex in (10.0, 22.0):                               # occhi tondi con il riflesso acceso + sopracciglia ad arco
            if blink > 0.5:                                # occhi chiusi: arco sorridente
                for dx_ in range(-2, 3):
                    img[6 + (1 if abs(dx_) == 2 else 0) - (1 if dx_ == 0 else 0) + 1, int(ex) + dx_] = 0.0
            else:
                e = ((xx - ex) / 2.2) ** 2 + ((yy - 6.0) / 2.4) ** 2 <= 1.0
                img[e] = 0.0
                img[5, int(ex - 1)] = 0.85
            xi = int(ex)
            for x_, y_ in ((xi - 3, 2), (xi - 2, 1), (xi - 1, 1), (xi, 1), (xi + 1, 1), (xi + 2, 2)):
                img[y_, x_] = 0.0
        lift = 0.6 * math.sin(t * 2.0)
        outer = ((xx - 16) / 12.5) ** 2 + ((yy - 7.6 - lift * 0.2) / 6.6) ** 2 <= 1.0
        inner = ((xx - 16) / 11.0) ** 2 + ((yy - 6.2 - lift * 0.2) / 6.0) ** 2 <= 1.0
        grin = outer & ~inner & (yy > 8.6)
        img[grin] = 0.0
        mouth = outer & (yy > 9.6) & (yy < 13.2) & (((xx - 16) / 9.5) ** 2 + ((yy - 9.6) / 3.4) ** 2 <= 1.0)
        img[mouth] = 0.0                                       # bocca aperta (scura)
        teeth = mouth & (yy > 9.6) & (yy < 11.0) & (np.abs(xx - 16) < 8.5)
        img[teeth] = 0.85                                      # fila di denti in alto
        for xc in (3, 29):                                     # fossette agli angoli
            if 0 <= xc < 32:
                img[8, xc] = 0.0
        c = np.array(COL[10], np.float32) / 255.0
        return np.clip(img[..., None] * c, 0, 1)

    def put(bm, x0, y0, v=1.0):
        h, w = bm.shape
        for yy in range(h):
            for xx in range(w):
                X, Y = x0 + xx, y0 + yy
                if 0 <= X < 32 and 0 <= Y < 16 and bm[yy, xx] > 0:
                    img[Y, X] = max(img[Y, X], bm[yy, xx] * v)
    dx, dy = int(round(1.4 * gx)), int(round(-1.0 * gy))
    kind = {1: "happy", 2: "relax", 3: "small", 5: "heart", 6: "squint", 9: "small"}.get(code, "open")
    if kind == "open" and blink > 0.5:
        kind = "shut"
    for ex in (5, 21):
        bm = EYE["happy" if (code == 8 and ex == 5) else ("shut" if code == 8 else kind)] if code == 8 else EYE[kind]
        h, w = bm.shape
        x0 = ex + (6 - w) // 2 + dx
        k_ = ("happy" if ex == 5 else "shut") if code == 8 else kind
        y0 = {"open": 1, "happy": 3, "relax": 4, "small": 3, "squint": 3, "heart": 1, "shut": 4}[k_] + dy
        put(bm, x0, y0)
        if kind == "open":                                    # riflesso: un LED piu' tenue
            img[y0 + 1, x0 + 1] *= 0.35
    if code == 3:                                             # sopracciglia dispiaciute
        for (x, y) in ((5, 2), (6, 2), (7, 1), (8, 1), (9, 0), (25, 2), (24, 2), (23, 1), (22, 1), (21, 0)):
            img[y, x] = 1.0
    if code == 4:                                             # pensa: puntini sopra, che si accendono in sequenza
        for k in range(3):
            img[0, 14 + 2 * k] = 1.0 if int(t * 3) % 3 == k else 0.35
    if code == 7:                                             # in carica: occhi socchiusi + icona batteria che si riempie
        img[:] = 0
        put(EYE["relax"], 5, 2); put(EYE["relax"], 21, 2)
        lvl = int((t * 2) % 5)
        bx = 10
        for x in range(bx, bx + 11):
            img[7, x] = img[13, x] = 1.0
        for y in range(7, 14):
            img[y, bx] = img[y, bx + 10] = 1.0
        img[9:12, bx + 11] = 1.0
        for k in range(lvl):
            img[9:12, bx + 2 + 2 * k:bx + 3 + 2 * k] = 1.0
        c = np.array(COL[7], np.float32) / 255.0
        return np.clip(img[..., None] * c, 0, 1)
    mk = {1: "up", 3: "down", 5: "up"}.get(code, "neutral")
    if code == 2 and int(t * 4) % 2:                          # caffe': i baffi "ballano"
        mk = "up"
    if code == 9:                                             # sorpreso: sopracciglia alte
        for x in (5, 6, 7, 8, 9, 10, 21, 22, 23, 24, 25, 26):
            img[0, x] = 1.0
    if code == 8:
        mk = "up"
    if STYLE == "manubrio":
        mb = MANUBRIO[mk]
        put(mb, 4, {"up": 11, "down": 11}.get(mk, 11))
    elif STYLE == "mario":
        y0 = {"up": 8, "down": 10}.get(mk, 9)
        put(MARIO, 5, y0)
    else:
        mb = MUST[mk]
        put(mb, 4, 16 - mb.shape[0] - 1)
    c = np.array(COL.get(code, COL[0]), np.float32) / 255.0
    return np.clip(img[..., None] * c, 0, 1)


if __name__ == "__main__":
    from PIL import Image
    tiles = [(led_image_big(draw_px(code, 0.0, 0.0, 0.0, 0.4))[..., :3] * 255).astype(np.uint8) for code in range(7)]
    tiles.append((led_image_big(draw_px(0, -0.8, 0.0, 0.8, 0.0))[..., :3] * 255).astype(np.uint8))
    rows = [np.concatenate(tiles[i:i + 4], 1) for i in (0, 4)]
    Image.fromarray(np.concatenate(rows, 0)).save("/tmp/claude-1000/-home-gpitton/73890d0e-b4dc-4184-b008-e491487358ce/scratchpad/led_preview.png")
    print("ok pixel-art")
