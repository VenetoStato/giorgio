#!/bin/bash
# stills di prodotto (posa da studio) per la validazione
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
mkdir -p stills_v7; R="--res 1920 1080 --samples 128"
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos 3.3 -2.3 1.25 --ctgt 0.05 0.0 0.85 --lens 42 --out stills_v7/01_hero.png $R > sv1.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cam face --out stills_v7/02_volto.png $R > sv2.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos -2.2 -2.0 1.35 --ctgt -0.15 -0.1 0.85 --lens 45 --out stills_v7/03_retro_caffe.png $R > sv3.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos -0.75 -0.75 1.05 --ctgt -0.21 -0.17 0.78 --lens 55 --out stills_v7/04_zaino_dettaglio.png $R > sv4.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --explode 2 --cpos 3.6 -2.6 1.45 --ctgt 0.0 0.0 0.95 --lens 38 --out stills_v7/05_esploso_ $R > sv5.log 2>&1
echo PRODOTTO_FATTO
