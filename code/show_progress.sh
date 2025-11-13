#!/bin/bash
# 实时显示训练进度的简单脚本

echo "📊 实时训练进度监控"
echo "================================"
echo ""
echo "💡 使用方法："
echo "  选项1: 实时查看EdNet日志"
echo "    tail -f /tmp/lpkt_ednet_live.log"
echo ""
echo "  选项2: 实时查看ASSISTments2017日志"
echo "    tail -f /tmp/lpkt_assist2017_live.log"
echo ""
echo "  选项3: 交互式查看"
echo "    bash /mnt/localssd/watch_training_live.sh"
echo ""
echo "  选项4: 同时查看两个日志"
echo "    tail -f /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log"
echo ""
echo "================================"
echo ""
echo "🔍 当前训练状态："
echo ""

# 显示进程
echo "训练进程:"
ps aux | grep "python.*wandb_lpkt_train" | grep -v grep | awk '{
    if ($15 ~ /ednet/) dataset="EdNet"
    else if ($15 ~ /assist2017/) dataset="ASSISTments2017"
    else dataset="Unknown"
    printf "  %s (PID: %s) - CPU: %s%%, 运行时长: %s\n", dataset, $2, $3, $10
}'
echo ""

# 显示GPU
echo "GPU使用:"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader,nounits | head -2 | awk -F', ' '{
    printf "  GPU %s: 使用率=%s%%, 显存=%sMB\n", $1, $2, $3
}'
echo ""

# 显示日志行数
echo "日志文件行数:"
wc -l /tmp/lpkt_ednet_live.log /tmp/lpkt_assist2017_live.log | head -2
echo ""

# 显示最新几行
echo "📝 EdNet最新5行:"
tail -5 /tmp/lpkt_ednet_live.log | sed 's/^/  /'
echo ""

echo "📝 ASSISTments2017最新5行:"
tail -5 /tmp/lpkt_assist2017_live.log | sed 's/^/  /'
echo ""

echo "================================"
echo "🌐 如果WandB初始化成功，日志中会显示WandB链接"
echo "   查找包含 'wandb' 或 'Run' 的行即可找到链接"
echo ""
echo "📈 查看完整实时日志请运行："
echo "   tail -f /tmp/lpkt_ednet_live.log"
echo "   tail -f /tmp/lpkt_assist2017_live.log"

