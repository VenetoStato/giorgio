"""Logo di Giorgio: tazzina da caffe' con il vapore che disegna una G. Uscite: logo.png (emblema), logo_full.png (emblema + scritta)."""
import math
from PIL import Image, ImageDraw, ImageFont

GRAF, ACC = (38, 40, 44, 255), (255, 140, 56, 255)
S = 4096


def emblem(S=S, col=GRAF, acc=ACC):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    u = S / 100.0
    # piattino
    dr.ellipse([12 * u, 83 * u, 88 * u, 91 * u], fill=col)
    # tazzina: corpo che si stringe verso il basso
    top, bot = 55 * u, 83 * u
    dr.polygon([(22 * u, top), (72 * u, top), (66 * u, bot - 4 * u), (28 * u, bot - 4 * u)], fill=col)
    dr.ellipse([28 * u, bot - 8 * u, 66 * u, bot], fill=col)
    dr.rounded_rectangle([20 * u, top - 1.5 * u, 74 * u, top + 3.5 * u], radius=2.5 * u, fill=col)
    # manico
    dr.ellipse([64 * u, 59 * u, 84 * u, 75 * u], fill=col)
    dr.ellipse([69 * u, 63.5 * u, 79 * u, 70.5 * u], fill=(0, 0, 0, 0))
    dr.polygon([(66 * u, 60 * u), (72 * u, 60 * u), (70 * u, 74 * u), (64 * u, 74 * u)], fill=col)
    # caffe' (crema) visto appena dal bordo
    dr.rounded_rectangle([24 * u, top - 0.2 * u, 70 * u, top + 1.6 * u], radius=0.8 * u, fill=acc)
    # vapore a forma di G sopra la tazzina
    cx, cy, R, w = 47 * u, 27 * u, 20 * u, 6.5 * u
    dr.arc([cx - R, cy - R, cx + R, cy + R], start=35, end=330, fill=acc, width=int(w))
    a = math.radians(35)
    ex, ey = cx + (R - w / 2) * math.cos(a), cy + (R - w / 2) * math.sin(a)
    dr.rectangle([cx + 1 * u, ey - w / 2, ex + w / 2, ey + w / 2], fill=acc)          # barra della G
    dr.rectangle([ex - w / 2, cy - 1 * u, ex + w / 2, ey + w / 2], fill=acc)
    return im


em = emblem()
em.resize((1024, 1024), Image.LANCZOS).save("logo.png")
# versione chiara (per sfondi scuri)
emblem(col=(240, 240, 238, 255)).resize((1024, 1024), Image.LANCZOS).save("logo_chiaro.png")
# logo completo: emblema + GIORGIO
W, H = 2400, 900
full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
full.paste(em.resize((860, 860), Image.LANCZOS), (20, 20), em.resize((860, 860), Image.LANCZOS))
dr = ImageDraw.Draw(full)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 300)
f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 92)
dr.text((930, 230), "GIORGIO", font=f, fill=GRAF)
dr.text((945, 580), "il robot che fa anche il caffè", font=f2, fill=(110, 112, 118, 255))
full.save("logo_full.png")
print("ok")
