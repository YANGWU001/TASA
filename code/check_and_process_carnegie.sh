#!/bin/bash

# 检查并处理Carnegie Learning数据集的完整流程
# 一旦数据可用，自动完成所有步骤

echo "=========================================="
echo "Carnegie Learning数据集处理流程"
echo "=========================================="
echo ""

# 检查数据是否存在
ALGEBRA2005_FILE="/mnt/localssd/pykt-toolkit/data/algebra2005/algebra_2005_2006_train.txt"
BRIDGE2006_FILE="/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/bridge_to_algebra_2006_2007_train.txt"

ALGEBRA2005_EXISTS=false
BRIDGE2006_EXISTS=false

if [ -f "$ALGEBRA2005_FILE" ] && [ -s "$ALGEBRA2005_FILE" ]; then
    ALGEBRA2005_EXISTS=true
    echo "✅ Algebra2005数据文件已找到: $(ls -lh $ALGEBRA2005_FILE | awk '{print $5}')"
else
    echo "❌ Algebra2005数据文件未找到"
fi

if [ -f "$BRIDGE2006_FILE" ] && [ -s "$BRIDGE2006_FILE" ]; then
    BRIDGE2006_EXISTS=true
    echo "✅ Bridge2Algebra2006数据文件已找到: $(ls -lh $BRIDGE2006_FILE | awk '{print $5}')"
else
    echo "❌ Bridge2Algebra2006数据文件未找到"
fi

echo ""

# 如果两个数据集都不存在，提示用户
if [ "$ALGEBRA2005_EXISTS" = false ] && [ "$BRIDGE2006_EXISTS" = false ]; then
    echo "⚠️  未找到任何Carnegie Learning数据集"
    echo ""
    echo "请下载数据集并放置到以下位置："
    echo "  - Algebra2005: $ALGEBRA2005_FILE"
    echo "  - Bridge2Algebra2006: $BRIDGE2006_FILE"
    echo ""
    echo "下载方式参见: /mnt/localssd/CARNEGIE_DATASETS_GUIDE.md"
    echo ""
    exit 1
fi

# 激活conda环境
source /opt/conda/etc/profile.d/conda.sh
conda activate pykt

echo "=========================================="
echo "步骤1: 数据预处理"
echo "=========================================="
echo ""

cd /mnt/localssd/pykt-toolkit/examples

# 预处理Algebra2005
if [ "$ALGEBRA2005_EXISTS" = true ]; then
    if [ ! -f "/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv" ]; then
        echo "🔄 正在预处理 Algebra2005..."
        python data_preprocess.py --dataset_name algebra2005 2>&1 | tee /mnt/localssd/algebra2005_preprocess.log
        echo "✅ Algebra2005预处理完成"
    else
        echo "✅ Algebra2005已预处理"
    fi
    echo ""
fi

# 预处理Bridge2Algebra2006
if [ "$BRIDGE2006_EXISTS" = true ]; then
    if [ ! -f "/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv" ]; then
        echo "🔄 正在预处理 Bridge2Algebra2006..."
        python data_preprocess.py --dataset_name bridge2algebra2006 2>&1 | tee /mnt/localssd/bridge2006_preprocess.log
        echo "✅ Bridge2Algebra2006预处理完成"
    else
        echo "✅ Bridge2Algebra2006已预处理"
    fi
    echo ""
fi

echo "=========================================="
echo "步骤2: 生成数据统计"
echo "=========================================="
echo ""

cd /mnt/localssd
python analyze_carnegie_datasets.py

echo ""
echo "=========================================="
echo "步骤3: 训练模型"
echo "=========================================="
echo ""

bash /mnt/localssd/train_carnegie_models.sh

echo ""
echo "=========================================="
echo "✅ 所有任务完成"
echo "=========================================="

