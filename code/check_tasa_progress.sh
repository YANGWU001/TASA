#!/bin/bash
echo "=================================="
echo "📊 TASA测试进度监控"
echo "=================================="
echo ""

# 检查TASA测试进程
if [ -f "logs/test_tasa_student1.pid" ]; then
    PID=$(cat logs/test_tasa_student1.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ TASA测试运行中 (PID: $PID)"
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        echo "   运行时间: $RUNTIME"
    else
        echo "❌ TASA测试已停止"
    fi
else
    echo "⚠️  未找到TASA测试PID"
fi

echo ""
echo "📝 最新日志 (最后20行):"
echo "----------------------------------"
tail -20 logs/test_tasa_student1.log | grep -v "it/s\]$" | tail -20

echo ""
echo "=================================="
echo "📊 Pre-test进度"
echo "=================================="
/mnt/localssd/check_progress.sh | grep -A 20 "评估进度"
