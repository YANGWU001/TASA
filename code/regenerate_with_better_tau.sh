#!/bin/bash

echo "========================================"
echo "🔄 重新生成History和Overall (使用更合理的tau)"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")

mkdir -p /mnt/localssd/logs/regenerate_v2

echo "第一步: 重新生成所有history.json (使用中位数tau)"
echo "========================================"
echo ""

for DATASET in "${DATASETS[@]}"; do
    echo "📊 Processing $DATASET..."
    
    # 备份旧文件
    if [ -f "/mnt/localssd/bank/forgetting/$DATASET/history.json" ]; then
        cp "/mnt/localssd/bank/forgetting/$DATASET/history.json" \
           "/mnt/localssd/bank/forgetting/$DATASET/history.json.old"
        echo "  ✅ Backed up old history.json"
    fi
    
    # 生成新的history.json
    LOG_FILE="/mnt/localssd/logs/regenerate_v2/${DATASET}_history.log"
    
    python3 /mnt/localssd/generate_history_v2.py \
        --dataset "$DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✅ History成功"
    else
        echo "  ❌ History失败 (see $LOG_FILE)"
    fi
    echo ""
done

echo ""
echo "第二步: 重新生成所有overall.json (每个方法独立level)"
echo "========================================"
echo ""

for DATASET in "${DATASETS[@]}"; do
    # 映射dataset名称
    if [ "$DATASET" == "bridge2algebra2006" ]; then
        OUTPUT_DATASET="bridge2006"
    else
        OUTPUT_DATASET="$DATASET"
    fi
    
    echo "📊 Processing $OUTPUT_DATASET..."
    
    # 备份旧文件
    if [ -f "/mnt/localssd/bank/forgetting/$OUTPUT_DATASET/overall.json" ]; then
        cp "/mnt/localssd/bank/forgetting/$OUTPUT_DATASET/overall.json" \
           "/mnt/localssd/bank/forgetting/$OUTPUT_DATASET/overall.json.old"
        echo "  ✅ Backed up old overall.json"
    fi
    
    # 生成新的overall.json
    LOG_FILE="/mnt/localssd/logs/regenerate_v2/${OUTPUT_DATASET}_overall.log"
    
    python3 /mnt/localssd/generate_overall_v2.py \
        --dataset "$OUTPUT_DATASET" \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Overall成功"
    else
        echo "  ❌ Overall失败 (see $LOG_FILE)"
    fi
    echo ""
done

echo ""
echo "========================================"
echo "✅ 完成！检查结果:"
echo "========================================"
echo ""
echo "History文件:"
ls -lh /mnt/localssd/bank/forgetting/*/history.json
echo ""
echo "Overall文件:"
ls -lh /mnt/localssd/bank/forgetting/*/overall.json
echo ""
echo "查看日志:"
echo "  cat /mnt/localssd/logs/regenerate_v2/*.log"
echo "========================================"
