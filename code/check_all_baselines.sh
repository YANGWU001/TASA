#!/bin/bash

# 检查所有Baselines评估进度

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          所有Baselines评估进度 - 简化版 (单次post-test)          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 进程状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PID=$(ps aux | grep "run_all_baselines_simple.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$PID" ]; then
    echo "  进程PID: $PID"
    echo "  状态: ✅ 运行中"
    
    # 获取运行时长
    ELAPSED=$(ps -p $PID -o etimes= | tr -d ' ')
    HOURS=$((ELAPSED / 3600))
    MINS=$(((ELAPSED % 3600) / 60))
    echo "  运行时长: ${HOURS}小时${MINS}分钟"
else
    echo "  状态: ❌ 已停止"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 各方法×数据集进度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

METHODS=("Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV")
DATASETS=("assist2017" "algebra2005" "bridge2006")

for METHOD in "${METHODS[@]}"; do
    echo ""
    echo "  ▸ $METHOD"
    
    for DATASET in "${DATASETS[@]}"; do
        DIR="/mnt/localssd/bank/evaluation_results/$METHOD/$DATASET"
        
        if [ "$DATASET" == "assist2017" ]; then
            TOTAL=189
        elif [ "$DATASET" == "algebra2005" ]; then
            TOTAL=29
        else
            TOTAL=46
        fi
        
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
                echo "    $DATASET: ✅ 完成 ($COMPLETED/$TOTAL) - Gain: $GAIN"
            else
                if [ $COMPLETED -gt 0 ]; then
                    PERCENT=$(python3 -c "print(f'{$COMPLETED/$TOTAL*100:.1f}')")
                    echo "    $DATASET: 🔄 运行中 ($COMPLETED/$TOTAL, ${PERCENT}%)"
                else
                    echo "    $DATASET: ⏳ 未开始"
                fi
            fi
        else
            echo "    $DATASET: ⏳ 未开始"
        fi
    done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后30行)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/all_baselines_simple.log" ]; then
    tail -30 logs/all_baselines_simple.log
else
    echo "  ⚠️  日志文件不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 监控命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  实时日志: tail -f logs/all_baselines_simple.log"
echo "  查看进度: ./check_all_baselines.sh"
echo ""

