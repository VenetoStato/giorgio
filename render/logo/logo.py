"""Logo di Giorgio (minimal): tazzina vista dall'alto che e' una G. Anello = corpo della G, manico = barra, disco pieno = caffe'.
Due colori, niente sfumature. Uscite: logo.png, logo_chiaro.png (su scuro), logo_full.png, logo_full_chiaro.png."""
import math
from PIL import Image, ImageDraw, ImageFont

INK = (28, 30, 34, 255); PAPER = (240, 240, 237, 255); ACC = (255, 122, 26, 255)
S = 4096


def mark(col, acc=ACC, S=S):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    u = S / 100.0; cx, cy = 45 * u, 50 * u
    R_out, w = 38 * u, 10 * u; R_in = R_out - w
    dr.ellipse([cx - R_in + 5 * u, cy - R_in + 5 * u, cx + R_in - 5 * u, cy + R_in - 5 * u], fill=acc)    # caffe'
    a1 = 312
    dr.arc([cx - R_out, cy - R_out, cx + R_out, cy + R_out], start=0, end=a1, fill=col, width=int(w))
    rm = R_out - w / 2
    x, y = cx + rm * math.cos(math.radians(a1)), cy + rm * math.sin(math.radians(a1))
    dr.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)                                  # estremita' tonda
    dr.rectangle([cx + R_in - 6 * u, cy - w, cx + R_out + 12 * u, cy], fill=col)                       # barra = manico
    dr.ellipse([cx + R_out + 12 * u - w / 2, cy - w, cx + R_out + 12 * u + w / 2, cy], fill=col)
    return im


def wordmark(col, sub_col):
    W, H = 3000, 900
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = mark(col).resize((780, 780), Image.LANCZOS); im.alpha_composite(m, (20, 60))
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf", 300)
    f2 = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf", 78)
    x = 900
    for ch in "GIORGIO":                                  # spaziatura larga
        dr.text((x, 230), ch, font=f, fill=col); x += dr.textlength(ch, font=f) + 46
    x2 = 906
    for ch in "SERVICE ROBOT  /  ALSO MAKES COFFEE":
        dr.text((x2, 600), ch, font=f2, fill=sub_col); x2 += dr.textlength(ch, font=f2) + 9
    return im.crop((0, 0, max(x, x2) + 40, H))


mark(INK).resize((1024, 1024), Image.LANCZOS).save("logo.png")
mark(PAPER).resize((1024, 1024), Image.LANCZOS).save("logo_chiaro.png")
wordmark(INK, (110, 113, 120, 255)).save("logo_full.png")
wordmark(PAPER, (170, 172, 178, 255)).save("logo_full_chiaro.png")
print("ok")
