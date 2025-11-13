#!/bin/bash
cd /mnt/localssd
echo "启动 Persona 修复任务..."
nohup /home/colligo/miniconda3/envs/pykt/bin/python fix_persona_concepts.py > logs/fix_persona_concepts.log 2>&1 &
PID=$!
echo "任务已启动！"
echo "  PID: $PID"
echo "  日志: tail -f /mnt/localssd/logs/fix_persona_concepts.log"
echo ""
echo "预计完成时间: 15-20 分钟"
