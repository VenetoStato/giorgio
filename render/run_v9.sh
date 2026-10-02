#!/bin/bash
# nuove sequenze v9: configurazioni, base in trasparenza, ricarica automatica, caffe' passo per passo
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v9/$out; mkdir -p v9/$out; $B -b -P blender_render.py -- "$@" --out v9/$out/f_#### $R > v9_$out.log 2>&1; echo "fatto $out"; }
s() { local out=$1; shift; $B -b -P blender_render.py -- "$@" --out stills_v9/$out.png --res 1920 1080 --samples 64 --fast > v9s_$out.log 2>&1; echo "fatto $out"; }
mkdir -p v9 stills_v9
CAM="--still 85 --solo --cpos 3.1 -1.5 1.35 --ctgt 0.0 0.0 0.82 --lens 40"
q1() {
  s cfg1_barista --data pose $CAM --hide tray
  s cfg2_logistica --data pose $CAM --hide cm_,cup_,logo_back
  s cfg3_mani_orca --data cfg_orca $CAM --hide tray
  s cfg4_lowcost --data cfg_amazing $CAM --hide tray,cm_,cup_,logo_back
  r p_logo --data pose --still 85 --solo --explode 120 --amt 0 --hide tray --cpos 1.9 -0.5 1.25 --cpos2 1.6 0.4 1.15 --ctgt 0.05 0.0 1.05 --lens 50
  r b_xray --data pose --still 85 --solo --explode 180 --amt 0 --xray_base --hide tray --cpos 1.5 -1.2 0.85 --cpos2 1.1 1.3 0.95 --ctgt 0.0 0.0 0.22 --lens 38 --labels lab_base.json --objlabels pw_battery,pw_dcdc0,pw_contactor,pw_pnoz,pw_charger,pw_jetson,charge_pad1,pw_tracer
  r c_bicchiere --data caffe --frames 170 330 1 --cpos -1.62 0.88 1.12 --ctgt -2.17 1.28 0.80 --lens 45 --lc -2.4 1.45
  echo Q1_FATTO
}
q2() {
  r r_wide --data ricarica --frames 0 841 2 --cpos -0.2 -3.9 2.0 --ctgt -2.4 -1.9 0.45 --lens 30 --lc -2.6 -2.0
  r r_close --data ricarica --frames 600 841 1 --cpos -2.35 -3.45 0.55 --ctgt -3.0 -2.95 0.18 --lens 45 --lc -3.0 -2.8
  r c_eroga --data caffe --frames 380 780 3 --cpos -1.62 0.88 1.12 --ctgt -2.17 1.28 0.80 --lens 45 --lc -2.4 1.45
  r c_prende --data caffe --frames 900 1070 1 --cpos -1.5 0.7 1.3 --ctgt -2.1 1.3 0.95 --lens 40 --lc -2.4 1.45
  echo Q2_FATTO
}
q1 & q2 &
wait
echo V9_RENDER_FATTO
