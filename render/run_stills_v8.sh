#!/bin/bash
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
mkdir -p stills_v8; R="--res 1920 1080 --samples 128"
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos 3.3 -2.3 1.25 --ctgt 0.05 0.0 0.85 --lens 42 --out stills_v8/01_hero.png $R > sv8_1.log 2>&1
$B -b -P blender_render.py -- --data espr --still 90 --solo --cpos 0.62 -0.18 1.43 --ctgt 0.06 0 1.40 --lens 80 --out stills_v8/02_volto.png $R > sv8_2.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos -2.2 -2.0 1.35 --ctgt -0.15 -0.1 0.85 --lens 45 --out stills_v8/03_retro.png $R > sv8_3.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos -0.85 -0.95 1.15 --ctgt -0.21 -0.12 0.80 --lens 50 --out stills_v8/04_zaino.png $R > sv8_4.log 2>&1
$B -b -P blender_render.py -- --data pose --still 85 --solo --cpos 0.0 -3.6 1.1 --ctgt -0.1 0 0.8 --lens 40 --out stills_v8/05_fianco.png $R > sv8_5.log 2>&1
echo STILLS_FATTO
