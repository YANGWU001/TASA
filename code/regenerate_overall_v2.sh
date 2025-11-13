#!/bin/bash

# 使用V2脚本重新生成overall.json
# 特点：自动计算合理的tau，为每个方法独立计算level

echo "========================================"
echo "重新生成 Overall.json V2"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

mkdir -p /mnt/localssd/logs/overall_v2

for DATASET in "${DATASETS[@]}"; do
    echo "Processing $DATASET..."
    
    LOG_FILE="/mnt/localssd/logs/overall_v2/${DATASET}.log"
    
    python3 /mnt/localssd/generate_overall_v2.py \
        --dataset "$DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   Success"
    else
        echo "   Failed (see $LOG_FILE)"
    fi
    echo ""
done

echo "========================================"
echo "All datasets processed!"
echo ""
echo "Check generated files:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/overall.json"
echo ""
echo "View logs:"
echo "  cat /mnt/localssd/logs/overall_v2/*.log"
echo "========================================"
