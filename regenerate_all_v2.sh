#!/bin/bash

echo "========================================"
echo "重新生成所有Forgetting Score数据 V2"
echo "1. 使用中位数作为tau"
echo "2. 为每个方法独立计算level"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

# 激活pykt环境
source /root/miniconda3/bin/activate pykt

# Step 1: 重新生成history.json（使用自动计算的tau）
echo "========== Step 1: 重新生成 history.json =========="
echo ""

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Generating history.json for $DATASET..."
    
    python /mnt/localssd/generate_history_forgetting_v2.py \
        --dataset "$DATASET"
    
    echo ""
done

echo ""
echo "========== Step 2: 重新生成 overall.json =========="
echo ""

# Step 2: 重新生成overall.json（为每个方法独立计算level）
for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Generating overall.json for $DATASET..."
    
    python /mnt/localssd/generate_overall_v2.py \
        --dataset "$DATASET"
    
    echo ""
done

echo ""
echo "========================================"
echo "✅ 全部完成！"
echo ""
echo "查看生成的文件:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/history.json"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/overall.json"
echo "========================================"

