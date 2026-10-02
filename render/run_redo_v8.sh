#!/bin/bash
# rifa le riprese renderizzate prima del tricolore, poi immagini, montaggio e copia
cd ~/giorgio_sim
until grep -q PIPELINE_FATTA rifai_tutto.log; do sleep 30; done
cd render
B=~/tools/blender-4.5.9-linux-x64/blender
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v8/$out; mkdir -p v8/$out; $B -b -P blender_render.py -- "$@" --out v8/$out/f_#### $R > v8_$out.log 2>&1; }
qa() {
r p_hero --data pose --still 85 --solo --explode 150 --amt 0 --cpos 3.6 -1.6 1.0 --cpos2 2.4 -3.1 1.6 --ctgt 0.05 0 0.95 --lens 40
  r p_expl --data pose --still 85 --solo --explode 240 --amt 1 --cpos 3.6 -2.4 1.5 --cpos2 3.0 2.6 1.5 --ctgt 0 0 0.95 --lens 36 --labels lab_expl.json
  r m_mani --data mani --frames 20 595 2 --cpos 5.0 0.1 1.5 --ctgt 3.4 1.2 1.15 --lens 38 --lc 3.2 1.2
  r l_carico --data logistica --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45
}
qb() {
  r l_cross --data logistica --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8
  r l_drive --data logistica --frames 1260 1580 2 --cam track
  r l_ins --data logistica --frames 1650 1740 1 --cpos 0.95 -0.55 1.35 --ctgt 0.33 0.0 0.98 --lens 50
  r l_unload --data logistica --frames 1740 2490 5 --cpos 1.5 -1.4 1.7 --ctgt 0.2 0.0 1.0 --lens 36
}
qa & qb &
wait
./run_stills_v8.sh
PY=~/IsaacLab/env_isaaclab/bin/python
$PY compose.py edit_v8.json ../video/giorgio_presentazione_v8.mp4
cp ../video/giorgio_presentazione_v8.mp4 ~/Videos/Giorgio/v8_attuale/
cp stills_v8/*.png ~/Videos/Giorgio/v8_attuale/render/
echo REDO_FATTO
