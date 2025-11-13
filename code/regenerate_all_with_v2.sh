#!/bin/bash

echo "========================================"
echo "重新生成所有Forgetting Score数据 (V2)"
echo "1. 自动计算合理的tau（基于中位数）"
echo "2. 为每个方法独立计算level"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

# 映射bridge2006到实际数据集名称
declare -A DATASET_MAP
DATASET_MAP["assist2017"]="assist2017"
DATASET_MAP["nips_task34"]="nips_task34"
DATASET_MAP["algebra2005"]="algebra2005"
DATASET_MAP["bridge2006"]="bridge2algebra2006"

mkdir -p /mnt/localssd/logs/forgetting_v2

echo "步骤 1/2: 重新生成 history.json (自动tau)"
echo "========================================"

for DATASET in "${DATASETS[@]}"; do
    echo ""
    echo "🚀 生成 ${DATASET} history.json..."
    
    REAL_DATASET="${DATASET_MAP[$DATASET]}"
    LOG_FILE="/mnt/localssd/logs/forgetting_v2/${DATASET}_history.log"
    
    python3 /mnt/localssd/generate_history_v2.py \
        --dataset "$REAL_DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ History完成"
        # 显示关键统计
        tail -n 15 "$LOG_FILE" | grep -E "(Median|FS range|Level|Saved)"
    else
        echo "   ❌ 失败 (see $LOG_FILE)"
    fi
done

echo ""
echo "========================================"
echo "步骤 2/2: 重新生成 overall.json (独立level)"
echo "========================================"

for DATASET in "${DATASETS[@]}"; do
    echo ""
    echo "🚀 生成 ${DATASET} overall.json..."
    
    LOG_FILE="/mnt/localssd/logs/forgetting_v2/${DATASET}_overall.log"
    
    python3 /mnt/localssd/generate_overall_forgetting_v2.py \
        --dataset "$DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Overall完成"
        # 显示关键统计
        tail -n 10 "$LOG_FILE" | grep -E "(level=|文件大小)"
    else
        echo "   ❌ 失败 (see $LOG_FILE)"
    fi
done

echo ""
echo "========================================"
echo "✅ 所有数据集处理完成！"
echo ""
echo "查看生成的文件:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/history.json"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/overall.json"
echo ""
echo "查看详细日志:"
echo "  ls /mnt/localssd/logs/forgetting_v2/"
echo "========================================"

