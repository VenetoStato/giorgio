#!/bin/bash
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
mkdir -p stills; R="--res 1920 1080 --samples 96"
$B -b -P blender_render.py -- --data logistica --still 490 --solo --cpos -2.05 2.2 1.43 --ctgt -2.4 1.54 1.38 --lens 85 --out stills/01_volto.png $R > s1.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 490 --solo --cpos -1.1 4.1 1.55 --ctgt -2.4 1.5 0.98 --lens 40 --out stills/02_prodotto.png $R > s2.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 490 --solo --explode 2 --cpos -1.1 4.1 1.6 --ctgt -2.4 1.45 1.1 --lens 36 --out stills/03_esploso_ $R > s3.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 285 --solo --cpos -1.75 0.1 1.0 --ctgt -2.4 1.2 0.6 --lens 40 --out stills/04_retro_caffe.png $R > s4.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 200 --cpos -0.7 3.4 2.3 --ctgt -2.2 1.3 0.9 --lens 32 --out stills/05_carico_sicurezza.png $R > s5.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 1200 --cpos 1.4 -1.3 1.6 --ctgt 0.25 0.0 1.0 --lens 38 --out stills/06_lavoro_banco.png $R > s6.log 2>&1
$B -b -P blender_render.py -- --data caffe --still 210 --cpos -2.05 0.45 0.72 --ctgt -2.39 1.16 0.42 --lens 50 --out stills/07_caffe_erogazione.png $R > s7.log 2>&1
$B -b -P blender_render.py -- --data caffe --still 1490 --cpos 1.4 -0.5 1.55 --ctgt 0.75 -2.2 0.9 --lens 35 --out stills/08_caffe_consegna.png $R > s8.log 2>&1
echo STILLS_FATTI
