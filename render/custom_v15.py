"""Sequenza "Make it yours": per ogni combinazione faccia+cappello alterna le immagini A e B (stills_v15/face_*_a/b.png)
con una lenta spinta in avanti. Uscita v15/custom/f_####.jpg (30 fps)."""
import os
from PIL import Image
L = ["classic_bustina", "yesman", "skeleton", "binocular", "ledmask", "neon", "classic_coppola", "hearts"]
N, SW = 48, 8                                          # 1.6 s per combinazione, cambio A/B ogni 8 fotogrammi
os.makedirs("v15/custom", exist_ok=True)
k = 0
for name in L:
    A = Image.open(f"stills_v15/face_{name}_a.png").convert("RGB")
    B = Image.open(f"stills_v15/face_{name}_b.png").convert("RGB")
    W, H = A.size
    for i in range(N):
        im = A if (i // SW) % 2 == 0 else B
        z = 1.0 + 0.05 * i / (N - 1)
        cw, ch = int(W / z), int(H / z)
        x0, y0 = (W - cw) // 2, (H - ch) // 2
        im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS).save(f"v15/custom/f_{k:04d}.jpg", quality=92)
        k += 1
print("custom", k, "fotogrammi")
