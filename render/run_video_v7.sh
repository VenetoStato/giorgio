#!/bin/bash
# sequenze per il video di presentazione (due code in parallelo sulla GPU)
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 48 --fast"
q1() {
  mkdir -p v7/p_hero v7/p_volto v7/p_expl v7/c_caffe1 v7/c_caffe2 v7/c_caffe3 v7/c_consegna
  $B -b -P blender_render.py -- --data pose --still 85 --solo --explode 150 --amt 0 --cpos 3.6 -1.6 1.0 --cpos2 2.4 -3.1 1.6 --ctgt 0.05 0 0.95 --lens 40 --out v7/p_hero/f_#### $R > v7_p_hero.log 2>&1
  $B -b -P blender_render.py -- --data pose --still 85 --solo --explode 90 --amt 0 --cpos 0.95 -0.35 1.42 --cpos2 0.72 -0.22 1.42 --ctgt 0.06 0 1.40 --lens 70 --out v7/p_volto/f_#### $R > v7_p_volto.log 2>&1
  $B -b -P blender_render.py -- --data pose --still 85 --solo --explode 240 --amt 1 --cpos 3.6 -2.4 1.5 --cpos2 3.0 2.6 1.5 --ctgt 0 0 0.95 --lens 36 --labels lab_expl.json --out v7/p_expl/f_#### $R > v7_p_expl.log 2>&1
  $B -b -P blender_render.py -- --data caffe --frames 30 540 4 --cpos -1.5 0.55 1.25 --ctgt -2.25 1.25 0.82 --lens 45 --lc -2.4 1.45 --out v7/c_caffe1/f_#### $R > v7_c1.log 2>&1
  $B -b -P blender_render.py -- --data caffe --frames 540 830 2 --cpos -1.75 0.8 1.05 --ctgt -2.22 1.24 0.80 --lens 50 --lc -2.4 1.45 --out v7/c_caffe2/f_#### $R > v7_c2.log 2>&1
  $B -b -P blender_render.py -- --data caffe --frames 830 1010 3 --cpos -1.3 0.6 1.45 --ctgt -2.3 1.35 0.95 --lens 40 --lc -2.4 1.45 --out v7/c_caffe3/f_#### $R > v7_c3.log 2>&1
  $B -b -P blender_render.py -- --data caffe --frames 1700 2260 2 --cpos 1.05 -0.55 1.55 --ctgt 1.0 -2.3 1.0 --lens 32 --lc 1.0 -2.2 --out v7/c_consegna/f_#### $R > v7_c4.log 2>&1
  echo Q1_FATTO
}
q2() {
  mkdir -p v7/l_carico v7/l_cross v7/l_drive v7/l_ins v7/l_unload v7/l_oper v7/l_dock
  $B -b -P blender_render.py -- --data logistica --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45 --out v7/l_carico/f_#### $R > v7_l1.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8 --out v7/l_cross/f_#### $R > v7_l2.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 1260 1580 2 --cam track --out v7/l_drive/f_#### $R > v7_l3.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 1650 1740 1 --cpos 0.95 -0.55 1.35 --ctgt 0.33 0.0 0.98 --lens 50 --out v7/l_ins/f_#### $R > v7_l4.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 1740 2490 5 --cpos 1.5 -1.4 1.7 --ctgt 0.2 0.0 1.0 --lens 36 --out v7/l_unload/f_#### $R > v7_l5.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 3150 4590 6 --cpos 1.6 3.4 3.0 --ctgt -1.2 0.5 0.6 --lens 26 --lc -1.2 0.7 --out v7/l_oper/f_#### $R > v7_l6.log 2>&1
  $B -b -P blender_render.py -- --data logistica --frames 4590 4800 2 --cpos -1.3 -0.6 1.6 --ctgt -2.4 1.2 0.9 --lens 35 --lc -2.4 1.0 --out v7/l_dock/f_#### $R > v7_l7.log 2>&1
  echo Q2_FATTO
}
q1 &
q2 &
wait
echo TUTTO_FATTO
