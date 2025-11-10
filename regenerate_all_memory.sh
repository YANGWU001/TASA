#!/bin/bash

echo "========================================"
echo "重新生成所有数据集的Memory（全量）"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

# 创建日志目录
mkdir -p /mnt/localssd/logs/memory_regen

# Python路径
PYTHON=/home/colligo/miniconda3/envs/pykt/bin/python

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 启动 $DATASET 的Memory重新生成 (后台运行)..."
    
    # 使用nohup在后台运行
    nohup $PYTHON /mnt/localssd/regenerate_memory_full.py \
        --dataset "$DATASET" > /mnt/localssd/logs/memory_regen/"$DATASET".log 2>&1 &
    
    PID=$!
    echo "   进程ID: $PID"
    echo "   日志: /mnt/localssd/logs/memory_regen/$DATASET.log"
    echo ""
    
    # 等待2秒，避免同时启动导致资源冲突
    sleep 2
done

echo "========================================"
echo "✅ 所有任务已启动！"
echo ""
echo "查看进度:"
echo "  tail -f /mnt/localssd/logs/memory_regen/*.log"
echo ""
echo "查看进程:"
echo "  ps aux | grep regenerate_memory_full"
echo ""
echo "查看已完成的memory文件:"
echo "  ls -lh /mnt/localssd/bank/memory/*/data/*.json | wc -l"
echo "========================================"

