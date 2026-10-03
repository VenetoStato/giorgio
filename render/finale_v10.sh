#!/bin/bash
cd ~/giorgio_sim/render
until grep -q V10_RENDER_FATTO run_v10.log; do sleep 30; done
PY=~/IsaacLab/env_isaaclab/bin/python
$PY crea_edit_v10.py > compose_v10.log 2>&1
$PY music_v10.py edit_v10.json music_v10.wav >> compose_v10.log 2>&1
$PY compose.py edit_v10.json ../video/giorgio_v10_EN.mp4 >> compose_v10.log 2>&1
mkdir -p ~/Videos/Giorgio/v10/render
cp ../video/giorgio_v10_EN.mp4 ~/Videos/Giorgio/v10/
cp stills_v10/*.png ~/Videos/Giorgio/v10/render/; cp logo/*.png ~/Videos/Giorgio/v10/
echo V10_VIDEO_PRONTO >> compose_v10.log
