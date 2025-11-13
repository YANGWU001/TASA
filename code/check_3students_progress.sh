#!/bin/bash
echo "=================================="
echo "📊 TASA 3学生测试进度"
echo "=================================="
echo ""

# 检查进程
if [ -f "logs/tasa_test_3students.pid" ]; then
    PID=$(cat logs/tasa_test_3students.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 测试运行中 (PID: $PID)"
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        echo "   运行时间: $RUNTIME"
    else
        echo "❌ 测试已停止"
    fi
else
    echo "⚠️  未找到测试PID"
fi

echo ""
echo "📝 最新日志 (最后30行):"
echo "----------------------------------"
tail -30 logs/tasa_test_3students.log | grep -E "学生|Round|评估|Post-test|Learning Gain|✅|❌|📊|🎓" | tail -20

echo ""
echo "💡 查看完整日志: tail -f logs/tasa_test_3students.log"
