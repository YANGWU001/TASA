#!/bin/bash
# 检查评估进度

echo "=================================="
echo "📊 Pre-test 评估进度"
echo "=================================="
echo ""

# 检查进程
PID_FILE="logs/evaluate_all_students.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 进程运行中 (PID: $PID)"
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        echo "   运行时间: $RUNTIME"
    else
        echo "❌ 进程已停止"
    fi
else
    echo "⚠️  未找到PID文件"
fi

echo ""

# 统计完成数量
TOTAL=1708
COMPLETED=$(ls bank/evaluation_results/pre-test/assist2017/student_*.json 2>/dev/null | wc -l)
REMAINING=$((TOTAL - COMPLETED))
PERCENTAGE=$(echo "scale=1; $COMPLETED * 100 / $TOTAL" | bc)

echo "📈 评估进度:"
echo "   总数: $TOTAL"
echo "   已完成: $COMPLETED ($PERCENTAGE%)"
echo "   剩余: $REMAINING"
echo ""

# 进度条
PROGRESS=$((COMPLETED * 50 / TOTAL))
printf "   ["
for i in $(seq 1 50); do
    if [ $i -le $PROGRESS ]; then
        printf "="
    else
        printf " "
    fi
done
printf "] $PERCENTAGE%%\n"

echo ""

# 显示最新日志
echo "📝 最新日志 (最后10行):"
echo "----------------------------------"
tail -10 logs/evaluate_all_students.log 2>/dev/null || echo "未找到日志文件"

echo ""
echo "💡 提示:"
echo "   - 实时监控: tail -f logs/evaluate_all_students.log"
echo "   - 查看统计: cat bank/evaluation_results/pre-test/assist2017/overall.json"

