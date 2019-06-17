#!/bin/bash
source /home/puhl/project/minas-py/venv/bin/activate
python ./didatic/prod.py &
pids[${i}]=$!
python ./didatic/clas.py --classifiers $1 &
pids[${i}]=$!
python ./didatic/detc.py &
pids[${i}]=$!
python ./didatic/fina.py &
pids[${i}]=$!

# wait for all pids
for pid in ${pids[*]}; do
    sleep 10
    wait $pid
done
jobs -p
for job in `jobs -p`
do
    echo $job
    wait $job || echo "FAIL $job"
done
