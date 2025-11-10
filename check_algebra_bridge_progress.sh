#!/bin/bash

LOG_FILE="logs/tasa_algebra_bridge.log"

echo "=================================="
echo "📊 algebra2005 & bridge2006 评估进度"
echo "=================================="
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    exit 1
fi

# 检查进程是否运行
if ps -p 2249759 > /dev/null 2>&1; then
    echo "✅ 评估进程正在运行 (PID: 2249759)"
else
    echo "❌ 评估已完成或停止"
fi

echo ""
echo "📈 当前处理的数据集:"
echo "----------------------------------"
tail -20 "$LOG_FILE" | grep -E "处理数据集|TASA评估|数据集" | tail -3

echo ""
echo "✅ 最近完成的学生:"
echo "----------------------------------"
grep "评估完成" "$LOG_FILE" | tail -10

echo ""
echo "📊 进度统计:"
echo "----------------------------------"
grep "进度:" "$LOG_FILE" | tail -3

echo ""
echo "❌ 错误信息 (如有):"
echo "----------------------------------"
grep -i "error\|failed\|失败\|错误" "$LOG_FILE" | tail -5 || echo "   无错误"

echo ""
echo "💡 查看完整日志: tail -f $LOG_FILE"

