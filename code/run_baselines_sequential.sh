#!/bin/bash

# 依次运行所有baseline方法

DATASET="assist2017"
MAX_WORKERS=10

echo "================================================================================"
echo "🚀 开始运行所有Baselines on $DATASET"
echo "================================================================================"
echo "  并行度: $MAX_WORKERS workers per method"
echo "  方法: Vanilla-ICL → MathChat → TutorLLM → PSS-MV"
echo ""

# 方法列表
METHODS=("Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV")

for METHOD in "${METHODS[@]}"; do
    echo ""
    echo "################################################################################"
    echo "# 开始: $METHOD"
    echo "################################################################################"
    
    LOG_FILE="logs/${METHOD}_${DATASET}.log"
    
    echo "  日志: $LOG_FILE"
    echo "  开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # 运行评估
    /opt/venv/bin/python3 -u evaluate_baselines.py \
        --method "$METHOD" \
        --dataset "$DATASET" \
        --max-workers "$MAX_WORKERS" \
        > "$LOG_FILE" 2>&1
    
    EXIT_CODE=$?
    
    echo "  结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "  ✅ $METHOD 完成"
        
        # 读取结果
        OVERALL_FILE="/mnt/localssd/bank/evaluation_results/$METHOD/$DATASET/overall.json"
        if [ -f "$OVERALL_FILE" ]; then
            GAIN=$(python3 << EOF
import json
with open("$OVERALL_FILE") as f:
    data = json.load(f)
print(f"{data['overall']['avg_learning_gain']*100:.1f}%")
EOF
            )
            echo "  平均Learning Gain: $GAIN"
        fi
    else
        echo "  ❌ $METHOD 失败 (Exit code: $EXIT_CODE)"
        echo "  查看日志: $LOG_FILE"
    fi
done

echo ""
echo "================================================================================"
echo "✅ 所有Baselines运行完成！"
echo "================================================================================"
echo ""

# 生成总结
echo "📊 结果总结:"
echo ""
printf "%-15s %-15s %-15s\n" "方法" "学生数" "平均Gain"
echo "────────────────────────────────────────────────────────────"

for METHOD in "${METHODS[@]}"; do
    OVERALL_FILE="/mnt/localssd/bank/evaluation_results/$METHOD/$DATASET/overall.json"
    if [ -f "$OVERALL_FILE" ]; then
        python3 << EOF
import json
with open("$OVERALL_FILE") as f:
    data = json.load(f)
print(f"{'$METHOD':<15s} {data['num_students']:<15d} {data['overall']['avg_learning_gain']*100:.1f}%")
EOF
    else
        printf "%-15s %-15s %-15s\n" "$METHOD" "N/A" "N/A"
    fi
done

echo ""
echo "================================================================================"

