"""Cartello 'programmabile': la base si comanda con ROS 2 standard, le abilita' di Giorgio sono funzioni Python -> stills_v9/codice.png"""
from PIL import Image, ImageDraw, ImageFont
K = 2; W, H = 1920 * K, 1080 * K
im = Image.new("RGB", (W, H), (244, 244, 242)); dr = ImageDraw.Draw(im)
U = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/truetype/ubuntu/Ubuntu-{w}.ttf", s * K)
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24 * K)
INK, GREY = (30, 32, 36), (115, 118, 125)
dr.text((90 * K, 70 * K), "Programmabile come qualsiasi robot ROS 2", font=U("M", 54), fill=INK)
dr.text((92 * K, 145 * K), "la base è un prodotto commerciale; software di navigazione e abilità sono aperti", font=U("L", 30), fill=GREY)
# colonna sinistra: chi fa cosa
rows = [("Base", "AgileX Tracer 2.0 · commerciale", "driver ROS 2 open-source del produttore (CAN)"),
        ("Navigazione", "Nav2 · open-source (Apache 2.0)", "mappa, percorsi, aggancio alla stazione"),
        ("Bracci", "OpenArm 2.0 · hardware aperto", "CERN-OHL-S + software Apache 2.0"),
        ("Abilità", "Python · aperte", "caricare, portare, smistare, caffè, ricarica")]
y = 250
for t1, t2, t3 in rows:
    dr.rounded_rectangle((90 * K, y * K, 760 * K, (y + 150) * K), radius=18 * K, fill=(255, 255, 255), outline=(215, 215, 215), width=2 * K)
    dr.text((115 * K, (y + 18) * K), t1, font=U("M", 30), fill=(255, 140, 56))
    dr.text((115 * K, (y + 60) * K), t2, font=U("R", 28), fill=INK)
    dr.text((115 * K, (y + 100) * K), t3, font=U("L", 24), fill=GREY)
    y += 170
# editor
x0, y0, x1, y1 = 830, 250, 1830, 910
dr.rounded_rectangle((x0 * K, y0 * K, x1 * K, y1 * K), radius=22 * K, fill=(28, 30, 34))
for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
    dr.ellipse(((x0 + 30 + 30 * i) * K, (y0 + 24) * K, (x0 + 46 + 30 * i) * K, (y0 + 40) * K), fill=c)
CODE = [("# 1) la base si muove con ROS 2 standard (Nav2)", "c"),
        ("from nav2_simple_commander.robot_navigator import BasicNavigator", "k"),
        ("nav = BasicNavigator()", "n"),
        ("nav.goToPose(posa(\"banco_B\"))  # Tracer 2.0 via CAN", "n"),
        ("", "n"),
        ("# 2) le abilità di Giorgio sono funzioni Python", "c"),
        ("giorgio.carica_flaconi(da=\"A\")", "n"),
        ("giorgio.porta(a=\"B\")", "n"),
        ("giorgio.smista(per=\"colore\")", "n"),
        ("giorgio.fai_caffe(per=\"Marco\")", "n"),
        ("giorgio.ricarica_se_sotto(0.30)  # aggancio automatico", "n"),
        ("", "n"),
        ("# oppure a voce: \"Giorgio, portami un caffè\"", "c")]
COL = {"c": (120, 160, 120), "k": (200, 140, 255), "n": (225, 225, 225)}
yy = y0 + 75
for line, kind in CODE:
    if "#" in line and kind == "n":
        a, b = line.split("#", 1)
        dr.text(((x0 + 40) * K, yy * K), a, font=MONO, fill=COL["n"])
        dr.text(((x0 + 40) * K + dr.textlength(a, font=MONO), yy * K), "#" + b, font=MONO, fill=COL["c"])
    else:
        dr.text(((x0 + 40) * K, yy * K), line, font=MONO, fill=COL[kind])
    yy += 40
dr.text((x0 * K, (y1 + 25) * K), "esempio: i nomi delle abilità sono quelli della simulazione", font=U("L", 24), fill=GREY)
im.resize((1920, 1080), Image.LANCZOS).save("stills_v9/codice.png")
print("ok")
