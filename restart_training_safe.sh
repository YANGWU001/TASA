#!/bin/bash
# 安全重启训练脚本 - 使用nohup确保不受terminal关闭影响

echo "⚠️  这将停止当前训练并使用nohup安全重启"
echo "⚠️  重启后，训练进度会从最后一个checkpoint继续（如果有的话）"
echo ""
echo "确认要继续吗？ (输入 yes 继续)"
read -r response

if [ "$response" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# 停止当前训练
echo "停止当前训练进程..."
pkill -f "wandb_lpkt_train.py --dataset_name=ednet"
pkill -f "wandb_lpkt_train.py --dataset_name=assist2017"
sleep 3

# 进入工作目录
cd /mnt/localssd/pykt-toolkit/examples

# 激活环境并启动EdNet训练（使用nohup）
echo "🚀 在GPU 0上启动EdNet训练（nohup保护）..."
nohup bash -c "source activate pykt && CUDA_VISIBLE_DEVICES=0 stdbuf -oL -eL python -u wandb_lpkt_train.py --dataset_name=ednet --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=3e-3" > /tmp/lpkt_ednet_safe.log 2>&1 &
EDNET_PID=$!

# 启动ASSISTments2017训练（使用nohup）
echo "🚀 在GPU 1上启动ASSISTments2017训练（nohup保护）..."
nohup bash -c "source activate pykt && CUDA_VISIBLE_DEVICES=1 stdbuf -oL -eL python -u wandb_lpkt_train.py --dataset_name=assist2017 --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=3e-3" > /tmp/lpkt_assist2017_safe.log 2>&1 &
ASSIST_PID=$!

sleep 2

echo ""
echo "✅ 训练已安全重启！"
echo ""
echo "进程信息："
echo "  EdNet PID: $EDNET_PID (GPU 0)"
echo "  ASSISTments2017 PID: $ASSIST_PID (GPU 1)"
echo ""
echo "📊 查看实时日志："
echo "  EdNet: tail -f /tmp/lpkt_ednet_safe.log"
echo "  ASSISTments2017: tail -f /tmp/lpkt_assist2017_safe.log"
echo ""
echo "🔍 查看训练进度："
echo "  bash /mnt/localssd/show_progress.sh"
echo ""
echo "🌐 WandB链接将显示在日志中，或访问: https://wandb.ai"
echo ""
echo "✅ 现在您可以安全地关闭terminal窗口，训练不会被打断！"
echo ""

