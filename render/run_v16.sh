#!/bin/bash
# v16 = v15 rifatto con le aperture delle spalle pulite (guscio del busto) e guarnizione in gomma; stesse cartelle v15/
cd ~/giorgio_sim/render
bash run_v15.sh
B=~/tools/blender-4.5.9-linux-x64/blender
for combo in "classic_bustina 1:5 8:5 bustina" "classic_coppola 8:5 1:5 coppola" "yesman 10:5:0:0 10:5:1:0.8 none" "skeleton 11:5:0:0 11:5:1:0 coppola" "binocular 12:5:0:0 12:5:1:0 none" "ledmask 13:5:0:0 13:5:1:0 snapback" "neon 14:5:0:0 14:5:1:0 snapback" "hearts 5:5 1:5 bustina"; do
  set -- $combo
  for ab in a b; do fs=$2; [ $ab = b ] && fs=$3
    $B -b -P blender_render.py -- --data espr_v11 --still 100 --dark --no_rings --solo --hat $4 --face_seq $fs --cpos 0.74 -0.44 1.52 --ctgt 0.0 0.0 1.43 --lens 70 --out stills_v15/face_${1}_$ab.png --res 1920 1080 --samples 64 --fast > stills_v15/face_${1}_$ab.log 2>&1
  done
done
~/IsaacLab/env_isaaclab/bin/python custom_v15.py
echo V16_RENDER_FATTO
