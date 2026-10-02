#!/bin/bash
# v9b: sequenze delle attivita' ri-renderizzate col modello nuovo (logo, macchina generica)
cd ~/giorgio_sim/render
until grep -q V9_RENDER_FATTO run_v9.log; do sleep 30; done
B=~/tools/blender-4.5.9-linux-x64/blender; R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v9/$out; mkdir -p v9/$out; $B -b -P blender_render.py -- "$@" --out v9/$out/f_#### $R > v9_$out.log 2>&1; echo "fatto $out"; }
q1() {
  r p_espr --data espr_v9 --frames 30 390 2 --solo --cpos 0.70 -0.22 1.44 --cpos2 0.60 -0.16 1.43 --ctgt 0.06 0 1.40 --lens 80
  r p_expl --data pose --still 85 --solo --explode 240 --amt 1 --cpos 3.6 -2.4 1.5 --cpos2 3.0 2.6 1.5 --ctgt 0 0 0.95 --lens 36 --labels lab_expl.json
  r c_consegna --data caffe --frames 1850 2300 2 --cpos -0.8 -4.9 1.75 --ctgt 0.84 -2.46 1.15 --lens 34 --lc 0.8 -2.4
  r l_ins --data logistica_v9 --frames 1650 1740 1 --cpos 0.95 -0.55 1.35 --ctgt 0.33 0.0 0.98 --lens 50
  r s_smista --data smista_v9 --frames 30 1024 4 --cpos 4.6 0.2 1.9 --ctgt 3.5 1.2 0.95 --lens 34 --lc 3.2 1.2
}
q2() {
  r l_carico --data logistica_v9 --frames 60 960 4 --cpos -1.0 2.9 1.75 --ctgt -2.4 1.75 1.05 --lens 35 --lc -2.4 1.45
  r l_cross --data logistica_v9 --frames 990 1200 1 --cpos 0.4 2.4 2.3 --ctgt -2.1 0.6 0.7 --lens 30 --lc -2.0 0.8
  r l_drive --data logistica_v9 --frames 1260 1580 2 --cam track
  r l_oper --data logistica_v9 --frames 3150 4590 6 --cpos 1.6 3.4 3.0 --ctgt -1.2 0.5 0.6 --lens 26 --lc -1.2 0.7
}
q1 & q2 & wait; echo V9B_FATTO
