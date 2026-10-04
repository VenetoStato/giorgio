#!/bin/bash
# attende il render v15, poi montaggio + musica + video in ~/Videos/Giorgio/v16
cd ~/giorgio_sim/render
until grep -q V16_RENDER_FATTO run_v16.log; do sleep 60; done
PY=~/IsaacLab/env_isaaclab/bin/python
$PY crea_edit_v15.py > compose_v16.log 2>&1
$PY verifica_testi.py edit_v15.json >> compose_v16.log 2>&1
$PY music_v12.py edit_v15.json music_v15.wav >> compose_v16.log 2>&1
$PY compose.py edit_v15.json ../video/giorgio_v16_EN.mp4 >> compose_v16.log 2>&1
mkdir -p ~/Videos/Giorgio/v16 && cp ../video/giorgio_v16_EN.mp4 ~/Videos/Giorgio/v16/
echo V16_VIDEO_PRONTO >> compose_v16.log
