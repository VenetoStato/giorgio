#!/bin/bash
# pipeline completa v8: registrazioni -> render -> montaggio
cd ~/giorgio_sim
PY=~/IsaacLab/env_isaaclab/bin/python; A="1:Giorgio, fammi un caffe e portalo a Marco"
export MUJOCO_GL=egl
$PY giorgio_v5.py --record render/rec_logistica.pkl --seconds 185 > render/rec_log.log 2>&1 &
$PY giorgio_v5.py --agent "$A" --seconds 100 --record render/rec_caffe.pkl > render/rec_caffe.log 2>&1 &
$PY giorgio_hands.py --record render/rec_mani.pkl > render/rec_mani.log 2>&1 &
$PY giorgio_sort.py --record render/rec_smista.pkl > render/rec_smista.log 2>&1 &
$PY pose_record.py render/rec_espr.pkl espressioni > render/rec_espr.log 2>&1 &
$PY pose_record.py render/rec_pose.pkl lavoro > render/rec_pose.log 2>&1 &
$PY giorgio_v5.py --video video/v8/sim_logistica.mp4 --seconds 185 > video/v8/sim_logistica.log 2>&1 &
$PY giorgio_v5.py --agent "$A" --seconds 100 --video video/v8/sim_caffe.mp4 > video/v8/sim_caffe.log 2>&1 &
$PY giorgio_hands.py --video video/v8/sim_mani_open.mp4 > video/v8/sim_mani.log 2>&1 &
$PY giorgio_sort.py --video video/v8/sim_smistamento.mp4 > video/v8/sim_smista.log 2>&1 &
wait
cp video/v8/sim_*.mp4 ~/Videos/Giorgio/v8_attuale/simulazione/
echo REGISTRAZIONI_FATTE
cd render
for n in logistica caffe mani smista espr pose; do $PY to_npz.py rec_$n.pkl $n; done
./run_stills_v8.sh
./run_video_v8.sh
$PY compose.py edit_v8.json ../video/giorgio_presentazione_v8.mp4
cp ../video/giorgio_presentazione_v8.mp4 ~/Videos/Giorgio/v8_attuale/
mkdir -p ~/Videos/Giorgio/v8_attuale/render; cp stills_v8/*.png ~/Videos/Giorgio/v8_attuale/render/
echo PIPELINE_FATTA
