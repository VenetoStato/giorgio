#!/bin/bash
# attende la fine dei render v9, monta il video, lo copia in ~/Videos/Giorgio/v9 e lo apre
cd ~/giorgio_sim/render
until grep -q V9_TUTTO_FATTO run_v9_tutto.log; do sleep 30; done
cp edit_v9_bozza.json edit_v9.json
~/IsaacLab/env_isaaclab/bin/python compose.py edit_v9.json ../video/giorgio_presentazione_v9.mp4 > compose_v9.log 2>&1
mkdir -p ~/Videos/Giorgio/v9/render
cp ../video/giorgio_presentazione_v9.mp4 ~/Videos/Giorgio/v9/
cp stills_v9/*.png ~/Videos/Giorgio/v9/render/
echo V9_VIDEO_PRONTO >> compose_v9.log
DISPLAY=${DISPLAY:-:0} xdg-open ~/Videos/Giorgio/v9/giorgio_presentazione_v9.mp4 >/dev/null 2>&1 &
