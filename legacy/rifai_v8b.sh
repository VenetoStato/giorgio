#!/bin/bash
# v8b: ri-registra smistamento e caffe' (pianificatore anti-urto, contenitori a due posti, passaggio della tazzina), ri-renderizza i loro piani, rimonta
cd ~/giorgio_sim
PY=~/IsaacLab/env_isaaclab/bin/python; A="1:Giorgio, fammi un caffe e portalo a Marco"
export MUJOCO_GL=egl
$PY giorgio_v5.py --agent "$A" --seconds 100 --record render/rec_caffe.pkl > render/rec_caffe.log 2>&1 &
$PY giorgio_sort.py --record render/rec_smista.pkl > render/rec_smista.log 2>&1 &
$PY giorgio_v5.py --agent "$A" --seconds 100 --video video/v8/sim_caffe.mp4 > video/v8/sim_caffe.log 2>&1 &
$PY giorgio_sort.py --video video/v8/sim_smistamento.mp4 > video/v8/sim_smista.log 2>&1 &
wait
cp video/v8/sim_caffe.mp4 video/v8/sim_smistamento.mp4 ~/Videos/Giorgio/v8_attuale/simulazione/
echo REGISTRAZIONI_FATTE
cd render
for n in caffe smista; do $PY to_npz.py rec_$n.pkl $n; done
B=~/tools/blender-4.5.9-linux-x64/blender
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v8/$out; mkdir -p v8/$out; $B -b -P blender_render.py -- "$@" --out v8/$out/f_#### $R > v8_$out.log 2>&1; echo "fatto $out"; }
NS=$($PY -c "import numpy as np; print(len(np.load('smista.npz')['xpos']) - 1)" 2>/dev/null || echo 1200)
(
  r c_caffe2 --data caffe --frames 430 720 2 --cpos -1.75 0.8 1.05 --ctgt -2.22 1.24 0.80 --lens 50 --lc -2.4 1.45
  r c_consegna --data caffe --frames 1850 2300 2 --cpos -0.8 -4.9 1.75 --ctgt 0.84 -2.46 1.15 --lens 34 --lc 0.8 -2.4
) &
(
  r s_smista --data smista --frames 30 $NS 4 --cpos 4.6 0.2 1.9 --ctgt 3.5 1.2 0.95 --lens 34 --lc 3.2 1.2
  r c_xray --data caffe --frames 30 1000 3 --xray --cpos -1.45 0.45 1.30 --ctgt -2.25 1.25 0.80 --lens 40 --lc -2.4 1.45 --labels lab_caffe.json --objlabels cm_body,cm_head,cm_btn1,cm_plate,cup_stack2,cm_tank
) &
wait
$PY compose.py edit_v8.json ../video/giorgio_presentazione_v8.mp4
cp ../video/giorgio_presentazione_v8.mp4 ~/Videos/Giorgio/v8_attuale/
echo V8B_FATTO
