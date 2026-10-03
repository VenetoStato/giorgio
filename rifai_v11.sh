#!/bin/bash
# v11: ri-registrazione di tutte le scene col modello allineato al CAD
cd ~/giorgio_sim
PY=~/IsaacLab/env_isaaclab/bin/python; A="1:Giorgio, fammi un caffe e portalo a Marco"
export MUJOCO_GL=egl PYTHONPATH=.
$PY giorgio_v5.py --agent "$A" --seconds 100 --record render/rec_caffe_v11.pkl > render/rec_caffe_v11.log 2>&1 &
$PY giorgio_v5.py --record render/rec_logistica_v11.pkl --seconds 185 > render/rec_log_v11.log 2>&1 &
$PY giorgio_sort.py --record render/rec_smista_v11.pkl > render/rec_smista_v11.log 2>&1 &
$PY rec_ricarica.py --record render/rec_ricarica_v11.pkl > render/rec_ricarica_v11.log 2>&1 &
wait
$PY pose_record.py render/rec_pose_v11.pkl lavoro > /dev/null 2>&1 &
$PY pose_record.py render/rec_cfg_orca_v11.pkl lavoro orca > /dev/null 2>&1 &
$PY pose_record.py render/rec_cfg_amazing_v11.pkl lavoro amazing > /dev/null 2>&1 &
$PY pose_record.py render/rec_espr_v11.pkl espressioni > /dev/null 2>&1 &
wait
cd render
for n in caffe logistica smista ricarica pose cfg_orca cfg_amazing espr; do $PY to_npz.py rec_${n}_v11.pkl ${n}_v11; done
$PY -c "
import pickle,json
D=pickle.load(open('rec_ricarica_v11.pkl','rb')); E=D['energy']
json.dump([[round(float(a),4),int(b),round(float(c),1)] for a,b,c in E], open('ricarica_energia_v11.json','w'))
print('agganciato al fotogramma', [i for i in range(len(E)) if E[i][1]][:1], 'di', len(E))"
echo REGISTRAZIONI_V11_FATTE
