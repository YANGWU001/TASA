#!/bin/bash

# 为所有数据集生成 overall.json
# 整合所有方法的 s_tc 和 fs，以 history 为基准

echo "========================================"
echo "生成所有数据集的 overall.json"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

mkdir -p /mnt/localssd/logs/overall

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Processing $DATASET..."
    
    LOG_FILE="/mnt/localssd/logs/overall/${DATASET}.log"
    
    python3 /mnt/localssd/generate_overall_forgetting.py \
        --dataset "$DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Success"
    else
        echo "   ❌ Failed (see $LOG_FILE)"
    fi
    echo ""
done

echo "========================================"
echo "✅ All datasets processed!"
echo ""
echo "检查生成的文件:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/overall.json"
echo ""
echo "查看日志:"
echo "  cat /mnt/localssd/logs/overall/*.log"
echo "========================================"

