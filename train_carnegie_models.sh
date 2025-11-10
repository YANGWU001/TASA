#!/bin/bash

# Carnegie Learning数据集模型训练脚本
# 训练LPKT、simpleKT、DKT、AKT四个模型

echo "=========================================="
echo "Carnegie Learning数据集模型训练"
echo "=========================================="
echo ""

# 激活conda环境
source /opt/conda/etc/profile.d/conda.sh
conda activate pykt

# 检查可用GPU
echo "🖥️  可用GPU:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
echo ""

# 检查数据集是否存在
ALGEBRA2005_EXISTS=false
BRIDGE2006_EXISTS=false

if [ -f "/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv" ]; then
    ALGEBRA2005_EXISTS=true
    echo "✅ Algebra2005数据集已准备好"
fi

if [ -f "/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv" ]; then
    BRIDGE2006_EXISTS=true
    echo "✅ Bridge2Algebra2006数据集已准备好"
fi

if [ "$ALGEBRA2005_EXISTS" = false ] && [ "$BRIDGE2006_EXISTS" = false ]; then
    echo "❌ 没有找到任何已预处理的数据集"
    exit 1
fi

echo ""
echo "=========================================="
echo "开始训练模型"
echo "=========================================="
echo ""

cd /mnt/localssd/pykt-toolkit/examples

# 分配GPU（使用GPU 0-7）
# Algebra2005: GPU 0-3
# Bridge2Algebra2006: GPU 4-7

GPU_COUNTER=0

# Algebra2005训练
if [ "$ALGEBRA2005_EXISTS" = true ]; then
    echo "📚 Algebra2005 数据集训练"
    echo "─────────────────────────"
    
    # LPKT
    echo "  启动 LPKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_lpkt_train.py \
        --dataset_name algebra2005 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --learning_rate 0.003 \
        --dropout 0.2 \
        --d_a 50 \
        --d_e 128 \
        --d_k 128 \
        --gamma 0.03 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/algebra2005_lpkt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # simpleKT
    echo "  启动 simpleKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_simplekt_train.py \
        --dataset_name algebra2005 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/algebra2005_simplekt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # DKT
    echo "  启动 DKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_dkt_train.py \
        --dataset_name algebra2005 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/algebra2005_dkt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # AKT
    echo "  启动 AKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_akt_train.py \
        --dataset_name algebra2005 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/algebra2005_akt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    echo ""
fi

# Bridge2Algebra2006训练
if [ "$BRIDGE2006_EXISTS" = true ]; then
    echo "📚 Bridge2Algebra2006 数据集训练"
    echo "─────────────────────────────────"
    
    # LPKT
    echo "  启动 LPKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_lpkt_train.py \
        --dataset_name bridge2algebra2006 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --learning_rate 0.003 \
        --dropout 0.2 \
        --d_a 50 \
        --d_e 128 \
        --d_k 128 \
        --gamma 0.03 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/bridge2006_lpkt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # simpleKT
    echo "  启动 simpleKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_simplekt_train.py \
        --dataset_name bridge2algebra2006 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/bridge2006_simplekt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # DKT
    echo "  启动 DKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_dkt_train.py \
        --dataset_name bridge2algebra2006 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/bridge2006_dkt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    # AKT
    echo "  启动 AKT 训练 (GPU $GPU_COUNTER)..."
    CUDA_VISIBLE_DEVICES=$GPU_COUNTER nohup python -u wandb_akt_train.py \
        --dataset_name bridge2algebra2006 \
        --emb_type qid \
        --save_dir saved_model \
        --seed 42 \
        --fold 0 \
        --use_wandb 1 \
        --add_uuid 0 \
        > /mnt/localssd/bridge2006_akt_train.log 2>&1 &
    echo "  PID: $!"
    GPU_COUNTER=$((GPU_COUNTER + 1))
    sleep 5
    
    echo ""
fi

echo "=========================================="
echo "✅ 所有模型训练已启动"
echo "=========================================="
echo ""

echo "📊 训练进程："
ps aux | grep "wandb.*train.py" | grep -v grep | awk '{print "  PID " $2 ": " $14 " " $15}'

echo ""
echo "📁 日志文件："
if [ "$ALGEBRA2005_EXISTS" = true ]; then
    echo "  Algebra2005:"
    echo "    - /mnt/localssd/algebra2005_lpkt_train.log"
    echo "    - /mnt/localssd/algebra2005_simplekt_train.log"
    echo "    - /mnt/localssd/algebra2005_dkt_train.log"
    echo "    - /mnt/localssd/algebra2005_akt_train.log"
fi

if [ "$BRIDGE2006_EXISTS" = true ]; then
    echo "  Bridge2Algebra2006:"
    echo "    - /mnt/localssd/bridge2006_lpkt_train.log"
    echo "    - /mnt/localssd/bridge2006_simplekt_train.log"
    echo "    - /mnt/localssd/bridge2006_dkt_train.log"
    echo "    - /mnt/localssd/bridge2006_akt_train.log"
fi

echo ""
echo "🔍 监控训练："
echo "  watch -n 10 'nvidia-smi; echo; ps aux | grep wandb.*train.py | grep -v grep'"
echo ""
echo "📊 查看WandB:"
echo "  https://wandb.ai/"
echo ""

