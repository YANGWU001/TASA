#!/bin/bash
cd /mnt/localssd
nohup /home/colligo/miniconda3/envs/pykt/bin/python recompute_embeddings.py --dataset nips_task34 --type persona > logs/recompute_persona_embeddings.log 2>&1 &
echo "任务已启动，PID: $!"
echo "查看日志: tail -f /mnt/localssd/logs/recompute_persona_embeddings.log"

