#!/bin/bash
# NIPS Task 3&4 数据集 - 训练四个KT模型
# 使用GPU 2-5 (GPU 0-1已被EdNet和ASSISTments2017的LPKT使用)

echo "🚀 开始训练NIPS Task 3&4数据集上的四个模型"
echo "=" | head -c 80; echo

# 创建日志目录
mkdir -p /tmp/nips_task34_training_logs

# Stop any existing nips_task34 training processes
echo "🛑 停止可能存在的旧训练进程..."
pkill -f "wandb_lpkt_train.py.*nips_task34"
pkill -f "wandb_simplekt_train.py.*nips_task34"
pkill -f "wandb_dkt_train.py.*nips_task34"
pkill -f "wandb_akt_train.py.*nips_task34"
sleep 3

cd /mnt/localssd/pykt-toolkit/examples

# Activate conda environment
source activate pykt

echo ""
echo "📊 训练配置:"
echo "  - 数据集: NIPS Task 3&4"
echo "  - 模型: LPKT, simpleKT, DKT, AKT"
echo "  - GPU分配: 2, 3, 4, 5"
echo "  - WandB: 启用"
echo ""

# Model 1: LPKT on GPU 2
echo "🔵 [1/4] 启动 LPKT 训练 (GPU 2)..."
CUDA_VISIBLE_DEVICES=2 nohup stdbuf -oL -eL python -u wandb_lpkt_train.py \
    --dataset_name=nips_task34 --use_wandb=1 --add_uuid=0 --fold=0 \
    > /tmp/nips_task34_training_logs/lpkt.log 2>&1 &
LPKT_PID=$!
echo "   PID: $LPKT_PID"
echo "   日志: /tmp/nips_task34_training_logs/lpkt.log"
sleep 2

# Model 2: simpleKT on GPU 3
echo "🟢 [2/4] 启动 simpleKT 训练 (GPU 3)..."
CUDA_VISIBLE_DEVICES=3 nohup stdbuf -oL -eL python -u wandb_simplekt_train.py \
    --dataset_name=nips_task34 --use_wandb=1 --add_uuid=0 --fold=0 \
    > /tmp/nips_task34_training_logs/simplekt.log 2>&1 &
SIMPLEKT_PID=$!
echo "   PID: $SIMPLEKT_PID"
echo "   日志: /tmp/nips_task34_training_logs/simplekt.log"
sleep 2

# Model 3: DKT on GPU 4
echo "🟡 [3/4] 启动 DKT 训练 (GPU 4)..."
CUDA_VISIBLE_DEVICES=4 nohup stdbuf -oL -eL python -u wandb_dkt_train.py \
    --dataset_name=nips_task34 --use_wandb=1 --add_uuid=0 --fold=0 \
    > /tmp/nips_task34_training_logs/dkt.log 2>&1 &
DKT_PID=$!
echo "   PID: $DKT_PID"
echo "   日志: /tmp/nips_task34_training_logs/dkt.log"
sleep 2

# Model 4: AKT on GPU 5
echo "🟠 [4/4] 启动 AKT 训练 (GPU 5)..."
CUDA_VISIBLE_DEVICES=5 nohup stdbuf -oL -eL python -u wandb_akt_train.py \
    --dataset_name=nips_task34 --use_wandb=1 --add_uuid=0 --fold=0 \
    > /tmp/nips_task34_training_logs/akt.log 2>&1 &
AKT_PID=$!
echo "   PID: $AKT_PID"
echo "   日志: /tmp/nips_task34_training_logs/akt.log"

echo ""
echo "=" | head -c 80; echo
echo "✅ 所有模型已启动！"
echo ""
echo "📋 训练进程摘要:"
echo "  LPKT    (GPU 2): PID $LPKT_PID"
echo "  simpleKT (GPU 3): PID $SIMPLEKT_PID"
echo "  DKT     (GPU 4): PID $DKT_PID"
echo "  AKT     (GPU 5): PID $AKT_PID"
echo ""
echo "📁 日志目录: /tmp/nips_task34_training_logs/"
echo ""
echo "🔍 监控命令:"
echo "  查看所有进程: ps aux | grep 'nips_task34'"
echo "  查看GPU使用: nvidia-smi"
echo "  查看日志: tail -f /tmp/nips_task34_training_logs/lpkt.log"
echo ""
echo "💾 模型保存位置: /mnt/localssd/pykt-toolkit/examples/saved_model/"
echo ""

