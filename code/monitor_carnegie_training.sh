#!/bin/bash

# 监控Carnegie Learning数据集模型训练

echo "=========================================="
echo "  Carnegie Learning 模型训练监控"
echo "=========================================="
echo ""

# 检查训练进程
RUNNING_COUNT=$(ps aux | grep "wandb.*train.py" | grep -v grep | wc -l)
echo "📊 运行中的训练进程: $RUNNING_COUNT / 8"
echo ""

if [ $RUNNING_COUNT -eq 0 ]; then
    echo "❌ 没有训练进程在运行"
    exit 1
fi

# 显示GPU使用情况
echo "🖥️  GPU 使用情况:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU %s: %s%% 使用率, %sMB / %sMB 显存\n", $1, $3, $4, $5}'
echo ""

# 显示训练进程
echo "📋 训练进程详情:"
ps aux | grep "wandb.*train.py" | grep -v grep | \
    awk '{print "  PID " $2 ": " $11 " " $12 " " $13}' | \
    sed 's/--dataset_name //' | sed 's/wandb_//' | sed 's/_train.py//'
echo ""

# 检查日志文件
echo "📁 最新日志（每个模型最后3行）:"
echo ""

echo "Algebra2005:"
for model in lpkt simplekt dkt akt; do
    logfile="/mnt/localssd/algebra2005_${model}_train.log"
    if [ -f "$logfile" ]; then
        echo "  $model:"
        tail -3 "$logfile" | sed 's/^/    /'
    fi
done

echo ""
echo "Bridge2Algebra2006:"
for model in lpkt simplekt dkt akt; do
    logfile="/mnt/localssd/bridge2006_${model}_train.log"
    if [ -f "$logfile" ]; then
        echo "  $model:"
        tail -3 "$logfile" | sed 's/^/    /'
    fi
done

echo ""
echo "=========================================="
echo "提示:"
echo "  - 实时监控: watch -n 10 bash /mnt/localssd/monitor_carnegie_training.sh"
echo "  - 查看完整日志: tail -f /mnt/localssd/algebra2005_lpkt_train.log"
echo "  - WandB: https://wandb.ai/"
echo "=========================================="

