#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Qwen Baseline运行状态检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查进程是否运行
if ps -p 174193 > /dev/null 2>&1; then
    echo "✅ Qwen Baseline正在运行 (PID: 174193)"
else
    echo "❌ Qwen Baseline未运行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最新日志 (最后50行):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -50 /mnt/localssd/logs/qwen_baseline_now.log

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 错误统计:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 统计SSL错误
ssl_errors=$(grep -c "SSL.*UNEXPECTED_EOF" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
echo "  SSL错误: $ssl_errors 次"

# 统计失败的对话生成
failed_dialogues=$(grep -c "❌ Dialogue生成失败" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
echo "  对话生成失败: $failed_dialogues 次"

# 统计成功完成的任务
completed_tasks=$(grep -c "✅.*completed" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
echo "  已完成任务: $completed_tasks 个"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 建议:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ssl_errors -gt 10 ]; then
    echo "  ⚠️  SSL错误较多，建议停止Qwen，等TASA完成后再运行"
    echo "  命令: kill -9 174193"
elif [ $failed_dialogues -gt 5 ]; then
    echo "  ⚠️  对话生成失败较多，可能有API问题"
else
    echo "  ✅ 运行正常，继续执行"
fi

echo ""
