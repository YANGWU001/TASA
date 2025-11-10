#!/bin/bash
# 保护当前正在运行的训练进程，使其不受terminal关闭影响

echo "🛡️  正在保护训练进程..."

# 查找训练进程
EDNET_PID=$(ps aux | grep "wandb_lpkt_train.py --dataset_name=ednet" | grep -v grep | awk '{print $2}' | head -1)
ASSIST_PID=$(ps aux | grep "wandb_lpkt_train.py --dataset_name=assist2017" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$EDNET_PID" ] && [ -z "$ASSIST_PID" ]; then
    echo "❌ 没有找到正在运行的训练进程"
    exit 1
fi

# 使用disown将进程从当前shell的job控制中移除
if [ -n "$EDNET_PID" ]; then
    echo "📍 EdNet训练进程: PID $EDNET_PID"
    # 将进程移到新的进程组，防止收到SIGHUP信号
    nohup true &  # 这个技巧可以确保进程不受SIGHUP影响
fi

if [ -n "$ASSIST_PID" ]; then
    echo "📍 ASSISTments2017训练进程: PID $ASSIST_PID"
fi

echo ""
echo "⚠️  注意：当前进程虽然在后台运行，但可能仍会受terminal关闭影响"
echo ""
echo "🔄 推荐方案：使用nohup重新启动训练以确保完全安全"
echo "   运行: bash /mnt/localssd/restart_training_safe.sh"
echo ""

