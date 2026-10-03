#!/bin/bash
# attende render v11 + anatomia, estrae i video OpenArm aggiornati, monta il video finale in ~/Videos/Giorgio/v11
cd ~/giorgio_sim/render
until grep -q V11_RENDER_FATTO run_v11.log && grep -q FATTO anat.log; do sleep 30; done
mkdir -p v11/oa_std v11/oa_gio      # ffmpeg -y sovrascrive i fotogrammi
ffmpeg -loglevel error -y -i ../rl_openarm/openarm_standalone.mp4 -q:v 3 v11/oa_std/f_%04d.jpg
ffmpeg -loglevel error -y -i ../rl_openarm/giorgio_transfer.mp4 -q:v 3 v11/oa_gio/f_%04d.jpg
PY=~/IsaacLab/env_isaaclab/bin/python
$PY crea_edit_v11.py > compose_v11.log 2>&1
$PY music_v10.py edit_v11.json music_v11.wav >> compose_v11.log 2>&1
$PY compose.py edit_v11.json ../video/giorgio_v11_EN.mp4 >> compose_v11.log 2>&1
mkdir -p ~/Videos/Giorgio/v11/render
cp ../video/giorgio_v11_EN.mp4 ~/Videos/Giorgio/v11/ && cp stills_v11/*.png ~/Videos/Giorgio/v11/render/
echo V11_VIDEO_PRONTO >> compose_v11.log
