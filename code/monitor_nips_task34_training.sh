#!/bin/bash
# 监控NIPS Task 3&4的训练进度

echo "🔍 NIPS Task 3&4 训练监控"
echo "=" | head -c 80; echo
echo ""

# 检查进程状态
echo "📊 训练进程状态:"
echo "-" | head -c 80; echo
ps aux | grep -E "(lpkt|simplekt|dkt|akt).*nips_task34" | grep -v grep | awk '{printf "  %-15s PID: %-8s CPU: %5s%% MEM: %5s%% Status: %s\n", $11, $2, $3, $4, $8}' || echo "  ⚠️  没有找到运行中的训练进程"

echo ""
echo "🖥️  GPU使用情况:"
echo "-" | head -c 80; echo
nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader | while IFS=',' read -r idx name mem util; do
    if [ "$idx" -ge 2 ] && [ "$idx" -le 5 ]; then
        model=""
        case "$idx" in
            2) model="LPKT" ;;
            3) model="simpleKT" ;;
            4) model="DKT" ;;
            5) model="AKT" ;;
        esac
        printf "  GPU %s (%s): %s, GPU利用率: %s\n" "$idx" "$model" "$mem" "$util"
    fi
done

echo ""
echo "📝 训练日志文件大小:"
echo "-" | head -c 80; echo
for model in lpkt simplekt dkt akt; do
    logfile="/tmp/nips_task34_training_logs/${model}.log"
    if [ -f "$logfile" ]; then
        size=$(ls -lh "$logfile" | awk '{print $5}')
        lines=$(wc -l < "$logfile")
        printf "  %-12s: %s (%s 行)\n" "$model" "$size" "$lines"
    fi
done

echo ""
echo "🎯 最新训练进度 (最后5行):"
echo "-" | head -c 80; echo
for model in lpkt simplekt dkt akt; do
    echo "  【$model】"
    tail -5 /tmp/nips_task34_training_logs/${model}.log 2>/dev/null | grep -E "(Epoch|validauc|best)" | tail -2 | sed 's/^/    /'
    echo ""
done

echo ""
echo "💾 Checkpoint文件:"
echo "-" | head -c 80; echo
for model in lpkt simplekt dkt akt; do
    ckpt_dir="/mnt/localssd/pykt-toolkit/examples/saved_model"
    ckpt_count=$(find "$ckpt_dir" -name "*nips_task34_${model}*.ckpt" 2>/dev/null | wc -l)
    if [ "$ckpt_count" -gt 0 ]; then
        latest=$(find "$ckpt_dir" -name "*nips_task34_${model}*.ckpt" -printf '%T+ %p\n' 2>/dev/null | sort -r | head -1 | cut -d' ' -f2)
        printf "  %-12s: %s 个checkpoint, 最新: %s\n" "$model" "$ckpt_count" "$(basename "$latest")"
    else
        printf "  %-12s: 暂无checkpoint\n" "$model"
    fi
done

echo ""
echo "=" | head -c 80; echo
echo ""
echo "🔄 持续监控命令:"
echo "  watch -n 5 /mnt/localssd/monitor_nips_task34_training.sh"
echo ""
echo "📊 查看实时日志:"
echo "  tail -f /tmp/nips_task34_training_logs/lpkt.log"
echo "  tail -f /tmp/nips_task34_training_logs/simplekt.log"
echo "  tail -f /tmp/nips_task34_training_logs/dkt.log"
echo "  tail -f /tmp/nips_task34_training_logs/akt.log"
echo ""

