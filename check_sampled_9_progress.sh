#!/bin/bash

LOG_FILE="logs/tasa_sampled_9_from_189.log"

echo "=================================="
echo "📊 9个抽样学生TASA评估进度"
echo "=================================="
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    exit 1
fi

# 检查进程是否运行
if ps -p 2115357 > /dev/null 2>&1; then
    echo "✅ 评估进程正在运行 (PID: 2115357)"
else
    echo "❌ 评估已完成或停止"
fi

echo ""
echo "📈 进度统计:"
echo "----------------------------------"
grep "进度:" "$LOG_FILE" | tail -1

echo ""
echo "✅ 已完成的学生:"
echo "----------------------------------"
grep "评估完成" "$LOG_FILE" | tail -10

echo ""
echo "❌ 错误信息:"
echo "----------------------------------"
grep -i "error\|failed\|失败\|错误" "$LOG_FILE" | tail -5 || echo "   无错误"

echo ""
echo "💡 查看完整日志: tail -f $LOG_FILE"

