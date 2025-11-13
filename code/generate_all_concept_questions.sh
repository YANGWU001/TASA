#!/bin/bash

echo "========================================"
echo "为所有数据集生成Concept问题集"
echo "使用GPT-4o，30线程并行"
echo "========================================"
echo ""

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2006")

mkdir -p /mnt/localssd/logs/concept_questions

for DATASET in "${DATASETS[@]}"; do
    echo "🚀 Processing $DATASET..."
    echo ""
    
    LOG_FILE="/mnt/localssd/logs/concept_questions/${DATASET}.log"
    
    python3 /mnt/localssd/generate_concept_questions.py \
        --dataset "$DATASET" \
        --workers 30 \
        > "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Success"
        # 显示简要统计
        tail -n 15 "$LOG_FILE" | grep -E "(Concepts总数|问题总数|文件:|大小:)"
    else
        echo "   ❌ Failed (see $LOG_FILE)"
    fi
    
    echo ""
    echo "========================================"
    echo ""
done

echo ""
echo "✅ 所有数据集处理完成！"
echo ""
echo "查看生成的文件:"
echo "  ls -lh /mnt/localssd/bank/test_data/*/concept_questions.json"
echo ""
echo "查看日志:"
echo "  ls /mnt/localssd/logs/concept_questions/"
echo "========================================"

