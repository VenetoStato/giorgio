#!/bin/bash
# v10: studio scuro (eroi, esploso, configurazioni) + tutte le sequenze con logo e tricolore nuovi
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v10/$out; mkdir -p v10/$out; $B -b -P blender_render.py -- "$@" --out v10/$out/f_#### $R > v10_$out.log 2>&1; echo "fatto $out"; }
s() { local out=$1; shift; $B -b -P blender_render.py -- "$@" --out stills_v10/$out.png --res 1920 1080 --samples 96 --fast > v10s_$out.log 2>&1; echo "fatto $out"; }
mkdir -p v10 stills_v10
D="--dark --no_rings --solo"
CAM="--still 85 --cpos 3.0 -1.6 1.0 --ctgt 0.0 0.0 0.78 --lens 38"
q1() {
  r h_hero --data pose --still 85 --explode 180 --amt 0 $D --hide tray --cpos 3.0 -1.7 1.0 --cpos2 2.0 2.5 1.15 --ctgt 0.0 0.0 0.85 --lens 38
  s cfg1_barista --data pose $CAM $D --hide tray
  s cfg2_logistica --data pose $CAM $D --hide cm_,cup_,logo_back
  s cfg3_mani_orca --data cfg_orca $CAM $D --hide tray
  s cfg4_lowcost --data cfg_amazing $CAM $D --hide tray,cm_,cup_,logo_back
  r h_expl --data pose --still 85 --explode 240 --amt 1 $D --cpos 3.6 -2.4 1.5 --cpos2 3.0 2.6 1.5 --ctgt 0 0 0.95 --lens 36 --labels lab_expl10.json
  r h_face --data espr_v9 --frames 30 390 2 $D --cpos 0.70 -0.22 1.44 --cpos2 0.60 -0.16 1.43 --ctgt 0.06 0 1.40 --lens 80
  r h_back --data pose --still 85 --explode 150 --amt 0 $D --hide tray --cpos -1.3 -1.7 1.15 --cpos2 -1.9 -0.5 1.05 --ctgt -0.25 -0.05 0.72 --lens 40
  r b_xray --data pose --still 85 --solo --explode 180 --amt 0 --xray_base --hide tray --cpos 1.5 -1.2 0.85 --cpos2 1.1 1.3 0.95 --ctgt 0.0 0.0 0.22 --lens 38 --labels lab_base.json --objlabels pw_battery,pw_dcdc0,pw_contactor,pw_pnoz,pw_charger,pw_jetson,charge_pad1,pw_tracer
  r c_bicchiere --data caffe --frames 170 330 1 --cpos -1.62 0.88 1.12 --ctgt -2.17 1.28 0.80 --lens 45 --lc -2.4 1.45
  r c_consegna --data caffe --frames 1850 2300 2 --cpos -0.8 -4.9 1.75 --ctgt 0.84 -2.46 1.15 --lens 34 --lc 0.8 -2.4
  r l_ins --data logistica_v9 --frames 1650 1740 1 --cpos 0.95 -0.55 1.35 --ctgt 0.33 0.0 0.98 --lens 50
  r s_smista --data smista_v9 --frames 30 1024 4 --cpos 4.6 0.2 1.9 --ctgt 3.5 1.2 0.95 --lens 34 --lc 3.2 1.2
  r r_wide --data ricarica --frames 0 841 2 --cpos -0.2 -3.9 2.0 --ctgt -2.4 -1.9 0.45 --lens 30 --lc -2.6 -2.0
  r r_close --data ricarica --frames 600 841 1 --cpos -2.35 -3.45 0.55 --ctgt -3.0 -2.95 0.18 --lens 45 --lc -3.0 -2.8
  echo Q1_FATTO
}
q2() {
  r c_eroga --data caffe --frames 380 780 3 --cpos -1.62 0.88 1.12 --ctgt -2.17 1.28 0.80 --lens 45 --lc -2.4 1.45
  r c_prende --data caffe --frames 900 1070 1 --cpos -1.5 0.7 1.3 --ctgt -2.1 1.3 0.95 --lens 40 --lc -2.4 1.45
  r l_carico --data logistica_v9 --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45
  r l_cross --data logistica_v9 --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8
  r l_drive --data logistica_v9 --frames 1260 1580 2 --cam track
  r l_oper --data logistica_v9 --frames 3150 4590 6 --cpos 1.6 3.4 3.0 --ctgt -1.2 0.5 0.6 --lens 26 --lc -1.2 0.7
  echo Q2_FATTO
}
q1 & q2 & wait; echo V10_RENDER_FATTO
