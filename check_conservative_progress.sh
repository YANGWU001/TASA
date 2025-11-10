#!/bin/bash

# 检查保守版本Baselines评估进度

PID=2389737

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         保守版本Baselines评估进度 (3数据集 × 4方法)               ║"
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
echo "📈 各方法 × 数据集进度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

METHODS=("Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV")
DATASETS=("assist2017" "algebra2005" "bridge2006")
TOTALS=(189 29 46)

for i in "${!METHODS[@]}"; do
    METHOD="${METHODS[$i]}"
    echo ""
    echo "  ▸ $METHOD"
    
    for j in "${!DATASETS[@]}"; do
        DATASET="${DATASETS[$j]}"
        TOTAL="${TOTALS[$j]}"
        
        DIR="/mnt/localssd/bank/evaluation_results/${METHOD}-conservative/${DATASET}"
        
        if [ -d "$DIR" ]; then
            COMPLETED=$(find "$DIR" -name "student_*.json" 2>/dev/null | wc -l)
            
            if [ -f "$DIR/overall.json" ]; then
                GAIN=$(python3 << EOF
import json
try:
    with open("$DIR/overall.json") as f:
        data = json.load(f)
    print(f"{data['overall']['avg_learning_gain']*100:.1f}%")
except:
    print("N/A")
EOF
                )
                echo "    $DATASET: ✅ 完成 ($COMPLETED学生, Gain=$GAIN)"
            else
                PERCENT=$(python3 -c "print(f'{$COMPLETED/$TOTAL*100:.1f}')" 2>/dev/null || echo "0.0")
                echo "    $DATASET: 🔄 进行中 ($COMPLETED/$TOTAL, ${PERCENT}%)"
            fi
        else
            echo "    $DATASET: ⏳ 未开始"
        fi
    done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后20行)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/all_baselines_conservative.log" ]; then
    tail -20 logs/all_baselines_conservative.log
else
    echo "  ⚠️  日志文件不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 监控命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  快速查看: ./check_conservative_progress.sh"
echo "  实时日志: tail -f logs/all_baselines_conservative.log"
echo ""

