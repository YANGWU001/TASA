#!/bin/bash

echo "========================================"
echo "为所有数据集生成Student Sessions"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

mkdir -p /mnt/localssd/logs/sessions

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 启动 $DATASET session生成 (后台)..."
    
    LOG_FILE="/mnt/localssd/logs/sessions/${DATASET}.log"
    
    nohup /home/colligo/miniconda3/envs/pykt/bin/python \
        /mnt/localssd/generate_student_sessions.py \
        --dataset "$DATASET" \
        > "$LOG_FILE" 2>&1 &
    
    echo "   进程ID: $!"
    echo "   日志: $LOG_FILE"
    echo ""
done

echo ""
echo "✅ 所有任务已启动！"
echo ""
echo "查看进度:"
echo "  tail -f /mnt/localssd/logs/sessions/*.log"
echo ""
echo "查看已完成的sessions:"
echo "  ls -lh /mnt/localssd/bank/session/*/"

