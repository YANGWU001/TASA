#!/bin/bash
echo "=================================="
echo "📊 TASA并行评估进度"
echo "=================================="
echo ""

# 检查进程
if [ -f "logs/tasa_parallel_9students.pid" ]; then
    PID=$(cat logs/tasa_parallel_9students.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 评估运行中 (PID: $PID)"
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        echo "   运行时间: $RUNTIME"
    else
        echo "❌ 评估已停止"
    fi
else
    echo "⚠️  未找到PID"
fi

echo ""
echo "📈 进度统计:"
echo "----------------------------------"
# 从日志中提取进度
grep "进度:" logs/tasa_parallel_9students.log | tail -1

echo ""
echo "✅ 已完成的学生:"
echo "----------------------------------"
grep "评估完成" logs/tasa_parallel_9students.log | tail -5

echo ""
echo "🔧 线程初始化:"
echo "----------------------------------"
grep "Thread.*初始化" logs/tasa_parallel_9students.log | wc -l | xargs echo "   总计初始化次数:"

echo ""
echo "💡 查看完整日志: tail -f logs/tasa_parallel_9students.log"
