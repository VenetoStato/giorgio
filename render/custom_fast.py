"""Fast "Make it yours" sequence for the teaser: every face+hat combination, A/B images alternating, NO zoom (static frame).
Output v19/custom_fast/f_####.jpg (30 fps): 12 frames (0.4 s) per combination, A/B swap every 6 frames."""
import os
from PIL import Image
L = ["classic_bustina", "yesman", "skeleton", "binocular", "ledmask", "neon", "classic_coppola", "hearts"]
N, SW = 12, 6
os.makedirs("v19/custom_fast", exist_ok=True)
k = 0
for name in L:
    A = Image.open(f"stills_v15/face_{name}_a.png").convert("RGB")
    B = Image.open(f"stills_v15/face_{name}_b.png").convert("RGB")
    for i in range(N):
        (A if (i // SW) % 2 == 0 else B).save(f"v19/custom_fast/f_{k:04d}.jpg", quality=92)
        k += 1
print("custom_fast", k, "frames")
