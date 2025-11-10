#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                  📊 所有Baseline运行状态检查                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 检查TASA Llama
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  TASA Llama (PID: 74812)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ps -p 74812 > /dev/null 2>&1; then
    echo "✅ 正在运行"
else
    echo "❌ 未运行"
fi
echo ""

# 检查Qwen Baseline
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Qwen Baseline (PID: 174193)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ps -p 174193 > /dev/null 2>&1; then
    echo "✅ 正在运行"
else
    echo "❌ 未运行"
fi
qwen_ssl_errors=$(grep -c "SSL.*UNEXPECTED_EOF" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
qwen_failed=$(grep -c "❌ Dialogue生成失败" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
qwen_completed=$(grep -c "✅.*completed" /mnt/localssd/logs/qwen_baseline_now.log 2>/dev/null || echo "0")
echo "  SSL错误: $qwen_ssl_errors 次"
echo "  对话失败: $qwen_failed 次"
echo "  已完成任务: $qwen_completed 个"
echo ""

# 检查GPT Baseline
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  GPT Baseline (PID: 214674)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ps -p 214674 > /dev/null 2>&1; then
    echo "✅ 正在运行"
else
    echo "❌ 未运行"
fi
gpt_none_errors=$(grep -c "⚠️ Student回复为None" /mnt/localssd/logs/gpt_baseline_now.log 2>/dev/null || echo "0")
gpt_failed=$(grep -c "❌ Dialogue生成失败" /mnt/localssd/logs/gpt_baseline_now.log 2>/dev/null || echo "0")
gpt_completed=$(grep -c "✅.*completed" /mnt/localssd/logs/gpt_baseline_now.log 2>/dev/null || echo "0")
echo "  None回复: $gpt_none_errors 次"
echo "  对话失败: $gpt_failed 次"
echo "  已完成任务: $gpt_completed 个"
echo ""

# 总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 总体评估："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total_errors=$((qwen_ssl_errors + qwen_failed + gpt_failed))
if [ $total_errors -gt 20 ]; then
    echo "  ⚠️  错误较多，建议停止部分任务"
elif [ $total_errors -gt 10 ]; then
    echo "  ⚠️  有一些错误，继续观察"
else
    echo "  ✅ 运行良好，继续执行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
