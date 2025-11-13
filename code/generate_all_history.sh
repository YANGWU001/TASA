#!/bin/bash

# 为所有数据集生成基于历史accuracy的Forgetting Score (history.json)
# 这是最标准的方法，所有字段都基于相同的原始数据

echo "========================================"
echo "生成所有数据集的 history.json"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")

mkdir -p /mnt/localssd/logs/history

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Processing $DATASET..."
    
    LOG_FILE="/mnt/localssd/logs/history/${DATASET}.log"
    
    python3 /mnt/localssd/generate_history_forgetting.py \
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
echo "  ls -lh /mnt/localssd/bank/forgetting/*/history.json"
echo ""
echo "查看日志:"
echo "  cat /mnt/localssd/logs/history/*.log"
echo "========================================"

