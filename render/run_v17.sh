#!/bin/bash
# v17: tutte le scene in cui si vede la base, rifatte con la NOSTRA base AMR (--newbase, amr/out/stl) + sezione AMR nuova.
# Ordine per priorita': prima scene del teaser e della sezione AMR. Fotogrammi in v17/<scena>; il montaggio usa v15 se manca v17.
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 24 --fast --jpg --newbase"
r() { local out=$1; shift; rm -rf v17/$out; mkdir -p v17/$out; $B -b -P blender_render.py -- "$@" --out v17/$out/f_#### $R > v17_$out.log 2>&1; echo "fatto $out $(ls v17/$out | wc -l) $(date +%H:%M)"; }
s() { local out=$1; shift; $B -b -P blender_render.py -- "$@" --out stills_v17/$out.png --res 1920 1080 --samples 96 --fast --newbase > v17s_$out.log 2>&1; echo "fatto $out"; }
a() { local out=$1; shift; rm -rf v17/$out; mkdir -p v17/$out; $B -b -P ../amr/render_amr.py -- "$@" --out v17/$out/f_####.jpg --samples 32 > v17_$out.log 2>&1; echo "fatto $out $(ls v17/$out | wc -l) $(date +%H:%M)"; }
mkdir -p v17 stills_v17
D="--dark --no_rings --solo"
CAF="--hide cup_steam"
CAM="--still 85 --cpos 3.0 -1.6 1.0 --ctgt 0.0 0.0 0.78 --lens 38"
q1() {
  r h_hero --data pose_v11 --still 85 --explode 180 --amt 0 $D --hide tray --cpos 3.0 -1.7 1.0 --cpos2 2.0 2.5 1.15 --ctgt 0.0 0.0 0.85 --lens 38 --face_seq 1:5
  a a_turn --view turntable --frames 0 149
  a a_expl --view explode_anim --frames 0 149
  r a_waist --data pose_v11 --still 85 --explode 180 --amt 0 $D --hide tray --waist_spin 0 90 -90 0 --cpos 3.2 -1.9 1.1 --cpos2 2.6 1.9 1.2 --ctgt 0.0 0.0 0.8 --lens 36 --face_seq 1:6
  r r_close --data ricarica_v11 --frames 690 929 1 --newdock --cpos -1.6 -2.85 0.65 --ctgt -3.0 -2.8 0.3 --lens 32 --lc -3.0 -2.8
  r r_wide --data ricarica_v11 --frames 0 929 2 --newdock --cpos -0.2 -3.9 2.0 --ctgt -2.4 -1.9 0.45 --lens 30 --lc -2.6 -2.0
  r l_drive --data logistica_v11 --frames 1260 1520 2 --cam track
  r c_consegna --data caffe_v11 --frames 1850 2300 2 --cpos -0.8 -4.9 1.75 --ctgt 0.84 -2.46 1.15 --lens 34 --lc 0.8 -2.4 $CAF
  s cfg1_barista --data pose_v11 $CAM $D --hide tray --face_seq 1:5
  s cfg2_logistica --data pose_v11 $CAM $D --hide cm_,cup_,logo_back --face_seq 6:5
  s cfg3_mani_orca --data cfg_orca_v11 $CAM $D --hide tray --face_seq 8:5
  s cfg4_lowcost --data cfg_amazing_v11 $CAM $D --hide tray,cm_,cup_,logo_back --face_seq 1:5
  r h_expl --data pose_v11 --still 85 --explode 240 --amt 1 $D --cpos 4.2 -2.8 1.9 --cpos2 3.5 3.0 1.9 --ctgt 0 0 1.20 --lens 33 --labels lab_expl17.json --face_seq 1:5
  r t_pick --data scatole_v14 --frames 2460 2710 1 --cpos 4.15 -0.85 1.50 --ctgt 3.00 -1.30 1.13 --lens 38 --lc 2.6 -1.3 --no_rings
  r t_rear --data scatole_v14 --frames 560 830 1 --cpos 1.55 -2.30 1.65 --ctgt 2.38 -1.40 1.02 --lens 42 --lc 2.6 -1.3 --no_rings
  s tray_front --data cfg_front_v14 --still 50 --cpos 2.4 -1.5 1.35 --ctgt 0.05 0.0 0.88 --lens 38 $D --face_seq 1:5
  echo Q1_FATTO
}
q2() {
  r l_carico --data logistica_v11 --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45
  r l_ins --data logistica_v11 --frames 1575 1665 1 --cpos 1.00 -0.45 1.16 --ctgt 0.36 0.0 1.02 --lens 45
  r l_cross --data logistica_v11 --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8
  r s_smista --data smista_v11 --frames 30 1025 4 --cpos 4.6 0.2 1.9 --ctgt 3.5 1.2 0.95 --lens 34 --lc 3.2 1.2
  r c_bicchiere --data caffe_v11 --frames 180 345 1 --cpos -1.62 0.88 1.20 --ctgt -2.17 1.28 0.88 --lens 45 --lc -2.4 1.45 $CAF
  r c_eroga --data caffe_v11 --frames 400 800 3 --cpos -1.62 0.88 1.20 --ctgt -2.17 1.28 0.88 --lens 45 --lc -2.4 1.45 $CAF
  r c_prende --data caffe_v11 --frames 920 1080 1 --cpos -1.5 0.7 1.38 --ctgt -2.1 1.3 1.03 --lens 40 --lc -2.4 1.45 $CAF
  r l_oper --data logistica_v11 --frames 3150 4590 6 --cpos 1.6 3.4 3.0 --ctgt -1.2 0.5 0.6 --lens 26 --lc -1.2 0.7
  r t_load --data scatole_v14 --frames 1890 2165 1 --cpos 3.55 -0.35 1.55 --ctgt 2.80 -1.15 1.00 --lens 45 --lc 2.6 -1.3 --no_rings
  r t_unload --data scatole_v14 --frames 3330 3560 1 --cpos 3.95 2.30 1.50 --ctgt 3.02 1.50 1.02 --lens 42 --lc 2.6 1.5 --no_rings
  s tray_rear --data cfg_rear_v14 --still 50 --cpos -2.3 -1.6 1.55 --ctgt -0.12 0.0 0.85 --lens 38 $D --face_seq 1:5
  s tray_both --data cfg_both_v14 --still 50 --cpos -1.3 -2.7 1.7 --ctgt 0.0 0.0 0.9 --lens 36 $D --face_seq 1:5
  echo Q2_FATTO
}
q1 & q2 & wait; echo V17_RENDER_FATTO
