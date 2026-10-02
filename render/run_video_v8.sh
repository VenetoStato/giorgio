#!/bin/bash
# sequenze del video v8 (due code in parallelo sulla GPU)
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; mkdir -p v8/$out; $B -b -P blender_render.py -- "$@" --out v8/$out/f_#### $R > v8_$out.log 2>&1; }
q1() {
  r p_hero --data pose --still 85 --solo --explode 150 --amt 0 --cpos 3.6 -1.6 1.0 --cpos2 2.4 -3.1 1.6 --ctgt 0.05 0 0.95 --lens 40
  r p_espr --data espr --frames 30 390 2 --solo --cpos 0.70 -0.22 1.44 --cpos2 0.60 -0.16 1.43 --ctgt 0.06 0 1.40 --lens 80
  r p_expl --data pose --still 85 --solo --explode 240 --amt 1 --cpos 3.6 -2.4 1.5 --cpos2 3.0 2.6 1.5 --ctgt 0 0 0.95 --lens 36 --labels lab_expl.json
  r m_mani --data mani --frames 20 595 2 --cpos 5.0 0.1 1.5 --ctgt 3.4 1.2 1.15 --lens 38 --lc 3.2 1.2
  r c_xray --data caffe --frames 30 1000 3 --xray --cpos -1.45 0.45 1.30 --ctgt -2.25 1.25 0.80 --lens 40 --lc -2.4 1.45 --labels lab_caffe.json --objlabels cm_body,cm_head,cm_btn1,cm_plate,cup_stack2,cm_tank
  r c_caffe2 --data caffe --frames 430 720 2 --cpos -1.75 0.8 1.05 --ctgt -2.22 1.24 0.80 --lens 50 --lc -2.4 1.45
  r c_consegna --data caffe --frames 1850 2300 2 --cpos -0.8 -4.9 1.75 --ctgt 0.84 -2.46 1.15 --lens 34 --lc 0.8 -2.4
  echo Q1_FATTO
}
q2() {
  r l_carico --data logistica --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45
  r l_cross --data logistica --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8
  r l_drive --data logistica --frames 1260 1580 2 --cam track
  r l_ins --data logistica --frames 1650 1740 1 --cpos 0.95 -0.55 1.35 --ctgt 0.33 0.0 0.98 --lens 50
  r l_unload --data logistica --frames 1740 2490 5 --cpos 1.5 -1.4 1.7 --ctgt 0.2 0.0 1.0 --lens 36
  r l_oper --data logistica --frames 3150 4590 6 --cpos 1.6 3.4 3.0 --ctgt -1.2 0.5 0.6 --lens 26 --lc -1.2 0.7
  r l_dock --data logistica --frames 4590 4800 2 --cpos -1.3 -0.6 1.6 --ctgt -2.4 1.2 0.9 --lens 35 --lc -2.4 1.0
  r s_smista --data smista --frames 30 1281 4 --cpos 4.6 0.2 1.9 --ctgt 3.5 1.2 0.95 --lens 34 --lc 3.2 1.2
  echo Q2_FATTO
}
q1 & q2 &
wait
echo TUTTO_FATTO
