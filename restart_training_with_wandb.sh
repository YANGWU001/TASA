#!/bin/bash
# 重启训练脚本 - 启用WandB和实时输出

echo "⚠️  这将停止当前训练并重新开始"
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
sleep 2

# 激活环境
source activate pykt
cd /mnt/localssd/pykt-toolkit/examples

# 启动EdNet训练（GPU 0，启用WandB和实时输出）
echo "启动EdNet训练（GPU 0）..."
CUDA_VISIBLE_DEVICES=0 python -u wandb_lpkt_train.py \
    --dataset_name=ednet \
    --use_wandb=1 \
    --add_uuid=0 \
    --fold=0 \
    --learning_rate=3e-3 \
    > /tmp/lpkt_ednet_live.log 2>&1 &

# 启动ASSISTments2017训练（GPU 1，启用WandB和实时输出）
echo "启动ASSISTments2017训练（GPU 1）..."
CUDA_VISIBLE_DEVICES=1 python -u wandb_lpkt_train.py \
    --dataset_name=assist2017 \
    --use_wandb=1 \
    --add_uuid=0 \
    --fold=0 \
    --learning_rate=3e-3 \
    > /tmp/lpkt_assist2017_live.log 2>&1 &

echo ""
echo "✅ 训练已重启！"
echo ""
echo "查看实时日志："
echo "  EdNet: tail -f /tmp/lpkt_ednet_live.log"
echo "  ASSISTments2017: tail -f /tmp/lpkt_assist2017_live.log"
echo ""
echo "WandB链接将显示在日志中"

