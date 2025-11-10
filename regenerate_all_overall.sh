#!/bin/bash

source ~/.bashrc
conda activate pykt

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

echo "========================================"
echo "重新生成所有overall.json (优化tau)"
echo "========================================"
echo ""

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Processing $DATASET..."
    python generate_overall_with_optimal_tau.py --dataset "$DATASET"
    echo ""
done

echo "========================================"
echo "✅ 全部完成！"
echo "========================================"
