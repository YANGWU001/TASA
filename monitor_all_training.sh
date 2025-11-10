#!/bin/bash
# 监控所有8个GPU上的训练任务

echo "🔍 所有训练任务监控"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo ""

# 显示当前时间
echo "⏰ 当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查训练进程
echo "📋 训练进程状态:"
echo "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-"

# LPKT训练（已存在）
LPKT_EDNET=$(ps aux | grep "wandb_lpkt_train.py --dataset_name=ednet" | grep -v grep | wc -l)
LPKT_ASSIST=$(ps aux | grep "wandb_lpkt_train.py --dataset_name=assist2017" | grep -v grep | wc -l)

# 新训练
SIMPLEKT_EDNET=$(ps aux | grep "wandb_train.py --dataset_name=ednet --model_name=simplekt" | grep -v grep | wc -l)
SIMPLEKT_ASSIST=$(ps aux | grep "wandb_train.py --dataset_name=assist2017 --model_name=simplekt" | grep -v grep | wc -l)
QIKT_EDNET=$(ps aux | grep "wandb_train.py --dataset_name=ednet --model_name=qikt" | grep -v grep | wc -l)
QIKT_ASSIST=$(ps aux | grep "wandb_train.py --dataset_name=assist2017 --model_name=qikt" | grep -v grep | wc -l)
IEKT_EDNET=$(ps aux | grep "wandb_train.py --dataset_name=ednet --model_name=iekt" | grep -v grep | wc -l)
IEKT_ASSIST=$(ps aux | grep "wandb_train.py --dataset_name=assist2017 --model_name=iekt" | grep -v grep | wc -l)

# 显示状态
echo "GPU 0: EdNet + LPKT              [$([ $LPKT_EDNET -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 1: ASSISTments2017 + LPKT    [$([ $LPKT_ASSIST -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 2: EdNet + simpleKT          [$([ $SIMPLEKT_EDNET -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 3: ASSISTments2017 + simpleKT [$([ $SIMPLEKT_ASSIST -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 4: EdNet + qikt              [$([ $QIKT_EDNET -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 5: ASSISTments2017 + qikt     [$([ $QIKT_ASSIST -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 6: EdNet + iekt              [$([ $IEKT_EDNET -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"
echo "GPU 7: ASSISTments2017 + iekt     [$([ $IEKT_ASSIST -gt 0 ] && echo "✓ 运行中" || echo "✗ 未运行")]"

echo ""

# GPU使用情况
echo "🖥️  GPU使用情况:"
echo "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
while IFS=, read -r gpu name util mem_used mem_total; do
    printf "GPU %s: %-20s | 使用率: %3s%% | 显存: %5s/%5s MB\n" \
        "$gpu" "$name" "$util" "$mem_used" "$mem_total"
done

echo ""

# 日志文件更新时间
echo "📄 日志文件最后更新:"
echo "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-"

for log_file in /tmp/lpkt_ednet_safe.log /tmp/lpkt_assist2017_safe.log \
                /tmp/kt_training_logs/ednet_simplekt.log \
                /tmp/kt_training_logs/assist2017_simplekt.log \
                /tmp/kt_training_logs/ednet_qikt.log \
                /tmp/kt_training_logs/assist2017_qikt.log \
                /tmp/kt_training_logs/ednet_iekt.log \
                /tmp/kt_training_logs/assist2017_iekt.log; do
    if [ -f "$log_file" ]; then
        log_name=$(basename "$log_file" .log)
        log_size=$(ls -lh "$log_file" | awk '{print $5}')
        log_lines=$(wc -l < "$log_file")
        log_time=$(stat -c %y "$log_file" | cut -d. -f1)
        printf "%-30s: %6s | %6s行 | %s\n" "$log_name" "$log_size" "$log_lines" "$log_time"
    fi
done

echo ""

# Checkpoint文件
echo "💾 模型Checkpoint:"
echo "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-" "-"

SAVED_MODEL_DIR="/mnt/localssd/pykt-toolkit/examples/saved_model"
if [ -d "$SAVED_MODEL_DIR" ]; then
    ls -dt "$SAVED_MODEL_DIR"/*/ 2>/dev/null | head -10 | while read dir; do
        model_name=$(basename "$dir")
        latest_ckpt=$(ls -t "$dir"/*.ckpt 2>/dev/null | head -1)
        if [ -n "$latest_ckpt" ]; then
            ckpt_time=$(stat -c %y "$latest_ckpt" | cut -d. -f1)
            printf "%-50s | %s\n" "$model_name" "$ckpt_time"
        fi
    done
else
    echo "模型目录不存在"
fi

echo ""
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo ""
echo "💡 提示:"
echo "  查看实时日志: tail -f /tmp/kt_training_logs/<model_log>"
echo "  查看GPU: watch -n 1 nvidia-smi"
echo "  重新运行监控: bash /mnt/localssd/monitor_all_training.sh"
echo ""

