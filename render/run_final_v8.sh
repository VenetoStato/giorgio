#!/bin/bash
cd ~/giorgio_sim/render
./run_stills_v8.sh
./run_video_v8.sh
PY=~/IsaacLab/env_isaaclab/bin/python
$PY compose.py edit_v8.json ../video/giorgio_presentazione_v8.mp4
cp ../video/giorgio_presentazione_v8.mp4 ~/Videos/Giorgio/v8_attuale/
mkdir -p ~/Videos/Giorgio/v8_attuale/render; cp stills_v8/*.png ~/Videos/Giorgio/v8_attuale/render/
echo FINALE_FATTO
