import json, pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
arrs, meta = {}, []
for i, g in enumerate(D["geoms"]):
    e = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in g.items() if k not in ("vert", "face")}
    if "vert" in g:
        arrs[f"v{i}"] = g["vert"].astype(np.float32); arrs[f"f{i}"] = g["face"].astype(np.int32); e["mesh"] = True
    meta.append(e)
import os
pre = sys.argv[2] if len(sys.argv) > 2 else "anim"
np.savez_compressed(pre + ".npz", xpos=D["xpos"].astype(np.float32), xquat=D["xquat"].astype(np.float32), zone=D["zone"],
                    hum_sizes=D["hum_sizes"].astype(np.float32), hum_rgba=np.asarray(D.get("hum_rgba", np.zeros((len(D["xpos"]), 0, 4))), np.float32),
                    face=np.asarray(D.get("face", np.zeros((len(D["xpos"]), 5))), np.float32), anim=np.asarray(D.get("anim", np.zeros((len(D["xpos"]), 0, 14))), np.float32), **arrs)
json.dump(dict(geoms=meta, hum=D["hum"], body_names=D["body_names"], r_prot=D["r_prot"], r_warn=D["r_warn"],
               anim_names=D.get("anim_names", []), states=D.get("states", []), n_seg=D.get("n_seg", 7)), open(pre + ".json", "w"))
print("ok", len(meta), D["xpos"].shape)
