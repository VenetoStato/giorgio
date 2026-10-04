"""v14: come to_npz.py, poi i colori delle scatole (geom senza materiale) da sRGB a lineare per Cycles
(cartone e cassetta altrimenti escono slavati). uso: python to_npz_v14.py rec_X.pkl prefisso"""
import json
import subprocess
import sys

pkl, pre = sys.argv[1], sys.argv[2]
subprocess.run([sys.executable, __file__.replace("to_npz_v14.py", "to_npz.py"), pkl, pre], check=True)
J = json.load(open(pre + ".json"))
n = 0
for g in J["geoms"]:
    nm = g.get("name") or ""
    if nm.startswith("box_") and not g.get("mat") and "label" not in nm:
        g["rgba"] = [float(c) ** 2.2 for c in g["rgba"][:3]] + [g["rgba"][3]]
        n += 1
json.dump(J, open(pre + ".json", "w"))
print("colori scatole convertiti:", n)
