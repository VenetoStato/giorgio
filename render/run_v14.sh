#!/bin/bash
# v14: scatole - vassoio frontale, rastrelliera posteriore, cassetta bimanuale (giorgio_scatole.py -> rec_scatole_v14.pkl)
# stesso stile dei colpi logistica v11 (studio chiaro), foto prodotto nello studio scuro come stills_v11/cfg*
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1920 1080 --samples 48 --fast --jpg"
r() { local out=$1; shift; rm -rf v14/$out; mkdir -p v14/$out; $B -b -P blender_render.py -- "$@" --out v14/$out/f_#### $R > v14_$out.log 2>&1; echo "fatto $out"; }
s() { local out=$1; shift; $B -b -P blender_render.py -- "$@" --out stills_v14/$out.png --res 1920 1080 --samples 96 --fast > v14s_$out.log 2>&1; echo "fatto $out"; }
mkdir -p v14 stills_v14
D="--dark --no_rings --solo"
q1() {
  r t_pick --data scatole_v14 --frames 2460 2710 1 --cpos 4.15 -0.85 1.50 --ctgt 3.00 -1.30 1.13 --lens 38 --lc 2.6 -1.3 --no_rings
  r t_rear --data scatole_v14 --frames 560 830 1 --cpos 1.55 -2.30 1.65 --ctgt 2.38 -1.40 1.02 --lens 42 --lc 2.6 -1.3 --no_rings
  s tray_front --data cfg_front_v14 --still 50 --cpos 2.4 -1.5 1.35 --ctgt 0.05 0.0 0.88 --lens 38 $D
  s tray_rear --data cfg_rear_v14 --still 50 --cpos -2.3 -1.6 1.55 --ctgt -0.12 0.0 0.85 --lens 38 $D
  echo Q1_FATTO
}
q2() {
  r t_load --data scatole_v14 --frames 1890 2165 1 --cpos 3.55 -0.35 1.55 --ctgt 2.80 -1.15 1.00 --lens 45 --lc 2.6 -1.3 --no_rings
  r t_unload --data scatole_v14 --frames 3330 3560 1 --cpos 3.95 2.30 1.50 --ctgt 3.02 1.50 1.02 --lens 42 --lc 2.6 1.5 --no_rings
  s tray_both --data cfg_both_v14 --still 50 --cpos -1.3 -2.7 1.7 --ctgt 0.0 0.0 0.9 --lens 36 $D
  echo Q2_FATTO
}
q1 & q2 & wait; echo V14_RENDER_FATTO
