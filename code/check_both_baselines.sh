#!/bin/bash
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║          🔥 Llama & Qwen Baseline 并行运行状态 - $(date +"%H:%M:%S")          ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 统计完成任务
llama_done=$(ls /mnt/localssd/bank/evaluation_results/*-llama/*/overall.json 2>/dev/null | wc -l)
qwen_done=$(ls /mnt/localssd/bank/evaluation_results/*-qwen/*/overall.json 2>/dev/null | wc -l)

echo "📊 总体进度:"
echo "  Llama: $llama_done/16 任务完成 ($(echo "scale=1; $llama_done*100/16" | bc)%)"
echo "  Qwen:  $qwen_done/16 任务完成 ($(echo "scale=1; $qwen_done*100/16" | bc)%)"
echo "  总计:  $((llama_done + qwen_done))/32 任务完成 ($(echo "scale=1; ($llama_done+$qwen_done)*100/32" | bc)%)"
echo ""

echo "🔄 当前运行进程:"
ps aux | grep "baseline_evaluation_conservative" | grep -v grep | while read line; do
    pid=$(echo $line | awk '{print $2}')
    method=$(echo $line | grep -oP "(?<=--method )[^ ]+")
    dataset=$(echo $line | grep -oP "(?<=--dataset )[^ ]+")
    backbone=$(echo $line | grep -oP "(?<=--backbone-suffix=)[^ ]+")
    echo "  • PID $pid: $method on $dataset [$backbone]"
done
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Llama Baseline 详细状态:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for method in Vanilla-ICL MathChat TutorLLM PSS-MV; do
    echo ""
    echo "【$method】"
    for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
        result_file="/mnt/localssd/bank/evaluation_results/${method}-conservative-llama/${dataset}/overall.json"
        if [ -f "$result_file" ]; then
            echo "  ✅ $dataset: 已完成"
        else
            log_file="/mnt/localssd/logs/baseline_${method}_-llama_${dataset}.log"
            if [ -f "$log_file" ] && [ $(stat -c%s "$log_file") -gt 1000 ]; then
                # 提取进度
                progress=$(tail -50 "$log_file" | grep "进度:" | tail -1 | grep -oP "\d+/\d+" || echo "运行中")
                echo "  🔄 $dataset: $progress"
            else
                echo "  ⏳ $dataset: 等待中"
            fi
        fi
    done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Qwen Baseline 详细状态:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for method in Vanilla-ICL MathChat TutorLLM PSS-MV; do
    echo ""
    echo "【$method】"
    for dataset in assist2017 nips_task34 algebra2005 bridge2006; do
        result_file="/mnt/localssd/bank/evaluation_results/${method}-conservative-qwen/${dataset}/overall.json"
        if [ -f "$result_file" ]; then
            echo "  ✅ $dataset: 已完成"
        else
            log_file="/mnt/localssd/logs/baseline_${method}_-qwen_${dataset}.log"
            if [ -f "$log_file" ] && [ $(stat -c%s "$log_file") -gt 1000 ]; then
                # 提取进度
                progress=$(tail -50 "$log_file" | grep "进度:" | tail -1 | grep -oP "\d+/\d+" || echo "运行中")
                echo "  🔄 $dataset: $progress"
            else
                echo "  ⏳ $dataset: 等待中"
            fi
        fi
    done
done

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
