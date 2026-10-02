#!/bin/bash
B=~/tools/blender-4.5.9-linux-x64/blender
cd ~/giorgio_sim/render
$B -b -P blender_render.py -- --look gb --frames 0 830 2 --cam track --out fr_drive/f_#### --samples 40 --res 1600 900 > v3_drive.log 2>&1
$B -b -P blender_render.py -- --look gb --frames 1380 1740 1 --cam orbit --out fr_work/f_#### --samples 40 --res 1600 900 > v3_work.log 2>&1
FF=$(~/IsaacLab/env_isaaclab/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null | tail -1)
$FF -loglevel error -y -framerate 30 -i fr_drive/f_%04d.png -c:v libx264 -crf 20 -pix_fmt yuv420p v3_drive.mp4
$FF -loglevel error -y -framerate 30 -i fr_work/f_%04d.png -c:v libx264 -crf 20 -pix_fmt yuv420p v3_work.mp4
printf "file 'v3_drive.mp4'\nfile 'v3_work.mp4'\n" > v3_list.txt
$FF -loglevel error -y -f concat -safe 0 -i v3_list.txt -c copy giorgio_v3_missione.mp4
cp giorgio_v3_missione.mp4 v3_volto.png v3_hero.png ~/Videos/
echo FATTO
