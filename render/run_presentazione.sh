#!/bin/bash
# riprese del video di presentazione (Cycles, 1280x720)
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
R="--res 1280 720 --samples 32"
rm -rf p1 p2 p3 p4 p5 p6; mkdir -p p1 p2 p3 p4 p5 p6
$B -b -P blender_render.py -- --data logistica --still 480 --solo --explode 150 --amt 0 --cpos -0.9 3.6 1.5 --cpos2 -3.9 3.6 1.4 --ctgt -2.4 1.5 1.0 --lens 42 --out p1/f_#### $R > p1.log 2>&1
$B -b -P blender_render.py -- --data logistica --still 480 --solo --explode 180 --cpos -1.1 4.1 1.6 --cpos2 -1.6 4.4 1.7 --ctgt -2.4 1.45 1.1 --lens 36 --labels p2_labels.json --out p2/f_#### $R > p2.log 2>&1
$B -b -P blender_render.py -- --data logistica --frames 0 1100 3 --cam track --out p3/f_#### $R > p3.log 2>&1
$B -b -P blender_render.py -- --data logistica --frames 1010 1130 1 --cpos 1.0 -1.0 1.4 --ctgt 0.33 -0.05 1.0 --lens 50 --out p4/f_#### $R > p4.log 2>&1
$B -b -P blender_render.py -- --data caffe --frames 30 270 2 --cpos -2.05 0.45 0.72 --cpos2 -2.25 0.5 0.66 --ctgt -2.39 1.16 0.42 --lens 50 --out p5/f_#### $R > p5.log 2>&1
$B -b -P blender_render.py -- --data caffe --frames 1240 1660 2 --cpos 2.9 -0.4 1.6 --ctgt 0.8 -1.9 0.85 --lens 35 --out p6/f_#### $R > p6.log 2>&1
echo RIPRESE_FATTE
