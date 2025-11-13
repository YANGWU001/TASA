#!/bin/bash
# 监控所有并行运行的FS计算任务

echo "======================================================================================================"
echo "📊 Forgetting Score计算任务监控"
echo "======================================================================================================"

# 检查运行中的进程
echo ""
echo "🔄 运行中的任务:"
ps aux | grep "calculate_all_fs_all_models.py" | grep -v grep | wc -l | xargs echo "   进程数:"

# 显示GPU使用情况
echo ""
echo "💻 GPU使用情况:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
    awk -F', ' '{printf "   GPU %s: %s%% GPU, %sMB/%sMB Memory\n", $1, $3, $4, $5}'

# 检查输出文件
echo ""
echo "📁 输出文件:"
if [ -d "/mnt/localssd/bank/forgetting" ]; then
    echo "   已完成的数据集:"
    for dataset in assist2017 nips_task34 algebra2005 bridge2algebra2006; do
        if [ -d "/mnt/localssd/bank/forgetting/$dataset" ]; then
            count=$(ls /mnt/localssd/bank/forgetting/$dataset/*.json 2>/dev/null | wc -l)
            echo "     - $dataset: $count/4 模型完成"
        fi
    done
else
    echo "   bank/forgetting/ 目录尚未创建"
fi

# 检查日志文件
echo ""
echo "📝 最近的日志更新:"
cd /mnt/localssd/pykt-toolkit/examples
for log in log_fs_all_*.txt; do
    if [ -f "$log" ]; then
        last_line=$(tail -1 "$log" 2>/dev/null)
        mod_time=$(stat -c '%y' "$log" 2>/dev/null | cut -d'.' -f1)
        echo "   $log"
        echo "      最后更新: $mod_time"
        echo "      最后一行: ${last_line:0:100}..."
    fi
done | head -40

echo ""
echo "======================================================================================================"
echo "💡 有用的命令:"
echo "======================================================================================================"
echo "  查看特定日志: tail -f /mnt/localssd/pykt-toolkit/examples/log_fs_all_assist2017_lpkt_gpu0.txt"
echo "  查看所有进程: ps aux | grep calculate_all_fs_all_models.py"
echo "  停止所有任务: pkill -f calculate_all_fs_all_models.py"
echo "  实时监控: watch -n 5 /mnt/localssd/monitor_fs_parallel.sh"
echo ""

