"""Logo di Giorgio: tazzina di espresso vista dall'alto che E' la G (bordo = corpo della G, manico = barra della G),
crema con cuore di latte. Uscite: logo.png (emblema), logo_chiaro.png (per sfondi scuri), logo_full.png (emblema + scritta)."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

GRAF = (35, 38, 43, 255)
CREMA, CREMA2, LATTE = (196, 128, 62, 255), (168, 98, 44, 255), (246, 232, 212, 255)
S = 4096


def emblem(col=GRAF, S=S):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    u = S / 100.0; cx, cy = 46 * u, 50 * u
    R_out, R_in = 36 * u, 27 * u
    # piattino: anello sottile, appena accennato
    dr.ellipse([cx - 44 * u, cy - 44 * u, cx + 44 * u, cy + 44 * u], outline=col[:3] + (60,), width=int(2.2 * u))
    # crema con sfumatura (cerchi concentrici) e cuore di latte
    for k in range(40):
        r = R_in + 0.6 * u - k * (R_in / 40)
        t = k / 39
        c = tuple(int(CREMA2[i] + (CREMA[i] - CREMA2[i]) * t) for i in range(3)) + (255,)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    hx, hy, hs = cx - 2.0 * u, cy + 0.5 * u, 0.62 * u              # cuore di latte (curva parametrica)
    pts = []
    for k in range(200):
        t = 2 * math.pi * k / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((hx + x * hs, hy - y * hs))
    dr.polygon(pts, fill=LATTE)
    # bordo della tazzina = corpo della G (aperto in alto a destra)
    a0, a1 = 0, 318                                                 # gradi, in senso orario da ore 3
    dr.arc([cx - R_out, cy - R_out, cx + R_out, cy + R_out], start=a0, end=a1, fill=col, width=int(R_out - R_in))
    rm = (R_out + R_in) / 2; w = R_out - R_in
    for a in (a1,):                                                 # estremita' arrotondata in alto
        x, y = cx + rm * math.cos(math.radians(a)), cy + rm * math.sin(math.radians(a))
        dr.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)
    # manico = barra della G: parte dal bordo a ore 3 ed esce a destra
    hb = w * 0.92; yb = cy - hb * 0.5 + 0.2 * u
    dr.rounded_rectangle([cx + R_in - 9 * u, yb - hb / 2, cx + R_out + 15 * u, yb + hb / 2], radius=hb / 2, fill=col)
    dr.ellipse([cx + R_in - 9 * u - hb * 0.1, yb - hb / 2, cx + R_in - 9 * u + hb * 0.9, yb + hb / 2], fill=col)
    return im


em = emblem()
em.resize((1024, 1024), Image.LANCZOS).save("logo.png")
emblem(col=(240, 240, 238, 255)).resize((1024, 1024), Image.LANCZOS).save("logo_chiaro.png")
W, H = 2600, 900
full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
e = em.resize((820, 820), Image.LANCZOS); full.alpha_composite(e, (30, 40))
dr = ImageDraw.Draw(full)
f = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 330)
f2 = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf", 84)
dr.text((900, 170), "giorgio", font=f, fill=GRAF)
dr.text((915, 600), "robot di servizio  ·  fa anche il caffè", font=f2, fill=(120, 122, 128, 255))
full.save("logo_full.png")
print("ok")
