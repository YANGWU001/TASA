#!/bin/bash

echo "========================================"
echo "NIPS_TASK34 Concept Text 修复进度"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 检查进程是否运行
PID=$(ps aux | grep "fix_nips_concept_text.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✅ 任务正在运行 (PID: $PID)"
else
    echo "⚠️  任务已完成或未运行"
fi
echo ""

# 显示日志最后20行
if [ -f "/mnt/localssd/logs/fix_nips_concept_text.log" ]; then
    echo "📋 最新日志:"
    echo "----------------------------------------"
    tail -20 /mnt/localssd/logs/fix_nips_concept_text.log
    echo "----------------------------------------"
else
    echo "⚠️  日志文件不存在"
fi
echo ""

echo "💡 使用提示:"
echo "  查看完整日志: tail -f /mnt/localssd/logs/fix_nips_concept_text.log"
echo "  停止任务: kill $PID"
echo ""

