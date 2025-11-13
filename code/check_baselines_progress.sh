#!/bin/bash

# 检查Baselines评估进度

PID=2381620

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║              Baselines评估进度 - assist2017                         ║"
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
echo "📈 各方法进度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for method in "Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV"; do
    echo ""
    echo "  ▸ $method"
    
    DIR="/mnt/localssd/bank/evaluation_results/$method/assist2017"
    
    if [ -d "$DIR" ]; then
        COMPLETED=$(find "$DIR" -name "student_*.json" | wc -l)
        
        if [ -f "$DIR/overall.json" ]; then
            GAIN=$(python3 << EOF
import json
with open("$DIR/overall.json") as f:
    data = json.load(f)
print(f"{data['overall']['avg_learning_gain']*100:.1f}%")
EOF
            )
            echo "    状态: ✅ 完成"
            echo "    学生数: $COMPLETED"
            echo "    平均Gain: $GAIN"
        else
            echo "    状态: 🔄 运行中"
            echo "    已完成: $COMPLETED/189"
            PERCENT=$(python3 -c "print(f'{$COMPLETED/189*100:.1f}')")
            echo "    进度: ${PERCENT}%"
        fi
    else
        echo "    状态: ⏳ 未开始"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后20行)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/baselines_assist2017.log" ]; then
    tail -20 logs/baselines_assist2017.log
else
    echo "  ⚠️  日志文件不存在"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 监控命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  实时日志: tail -f logs/baselines_assist2017.log"
echo "  查看进度: ./check_baselines_progress.sh"
echo ""

