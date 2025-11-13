#!/bin/bash

# 检查主评估脚本进度

PID=2395280

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║            主评估脚本进度 (17个任务)                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 进程状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ps -p $PID > /dev/null 2>&1; then
    echo "  进程PID: $PID"
    echo "  状态: ✅ 运行中"
    
    # 获取运行时长
    ELAPSED=$(ps -p $PID -o etimes= | tr -d ' ')
    HOURS=$((ELAPSED / 3600))
    MINS=$(((ELAPSED % 3600) / 60))
    echo "  运行时长: ${HOURS}小时${MINS}分钟"
else
    echo "  进程PID: $PID"
    echo "  状态: ❌ 已停止"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 任务进度 (17个任务)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 任务1: TASA on nips_task34
echo ""
echo "  1. TASA-best-of-2 × nips_task34"

TASA_DIR="/mnt/localssd/bank/evaluation_results/TASA-best-of-2/nips_task34"
if [ -d "$TASA_DIR" ]; then
    COMPLETED=$(find "$TASA_DIR" -name "student_*.json" 2>/dev/null | wc -l)
    
    if [ -f "$TASA_DIR/overall.json" ]; then
        GAIN=$(python3 << EOF
import json
try:
    with open("$TASA_DIR/overall.json") as f:
        data = json.load(f)
    print(f"{data['overall']['avg_best_learning_gain']*100:.1f}%")
except:
    print("N/A")
EOF
        )
        echo "     状态: ✅ 完成 ($COMPLETED学生, Gain=$GAIN)"
    else
        PERCENT=$(python3 -c "print(f'{$COMPLETED/487*100:.1f}')" 2>/dev/null || echo "0.0")
        echo "     状态: 🔄 进行中 ($COMPLETED/487, ${PERCENT}%)"
    fi
else
    echo "     状态: ⏳ 未开始"
fi

# 任务2-17: Baselines
METHODS=("Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV")
DATASETS=("assist2017" "algebra2005" "bridge2006" "nips_task34")
TOTALS=(189 29 46 487)

TASK_NUM=2

for METHOD in "${METHODS[@]}"; do
    echo ""
    echo "  $METHOD:"
    
    for j in "${!DATASETS[@]}"; do
        DATASET="${DATASETS[$j]}"
        TOTAL="${TOTALS[$j]}"
        
        DIR="/mnt/localssd/bank/evaluation_results/${METHOD}-conservative/${DATASET}"
        
        if [ -d "$DIR" ]; then
            COMPLETED=$(find "$DIR" -name "student_*.json" 2>/dev/null | wc -l)
            
            if [ -f "$DIR/overall.json" ]; then
                GAIN_AVG=$(python3 << EOF
import json
try:
    with open("$DIR/overall.json") as f:
        data = json.load(f)
    print(f"{data['strategy_avg']['avg_learning_gain']*100:.1f}%")
except:
    print("N/A")
EOF
                )
                echo "     ${TASK_NUM}. $DATASET: ✅ 完成 ($COMPLETED学生, Gain=$GAIN_AVG)"
            else
                PERCENT=$(python3 -c "print(f'{$COMPLETED/$TOTAL*100:.1f}')" 2>/dev/null || echo "0.0")
                echo "     ${TASK_NUM}. $DATASET: 🔄 进行中 ($COMPLETED/$TOTAL, ${PERCENT}%)"
            fi
        else
            echo "     ${TASK_NUM}. $DATASET: ⏳ 未开始"
        fi
        
        TASK_NUM=$((TASK_NUM + 1))
    done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后20行)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/all_evaluations_master.log" ]; then
    tail -20 logs/all_evaluations_master.log
else
    echo "  ⚠️  日志文件不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 监控命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  快速查看: ./check_master_progress.sh"
echo "  实时日志: tail -f logs/all_evaluations_master.log"
echo "  TASA日志: tail -f logs/TASA_nips_task34.log"
echo ""

