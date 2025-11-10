#!/bin/bash
# 使用训练好的KT模型预测所有学生的概率并计算Forgetting Score

echo "======================================================================================================"
echo "🚀 使用KT模型预测并计算Forgetting Score"
echo "======================================================================================================"

cd /mnt/localssd/pykt-toolkit/examples

# 激活conda环境
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

# 数据集列表
DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")

# 使用LPKT模型（最稳定）
MODEL="lpkt"

echo ""
echo "配置:"
echo "  模型: ${MODEL^^}"
echo "  数据集: ${DATASETS[*]}"
echo "  设备: CPU (避免CUDA问题)"
echo ""

# 为每个数据集运行预测
for dataset in "${DATASETS[@]}"; do
    echo "======================================================================================================"
    echo "📊 数据集: ${dataset^^}"
    echo "======================================================================================================"
    
    python predict_all_with_kt_models.py \
        --dataset=$dataset \
        --model=$MODEL \
        --batch_size=64 \
        --device=cpu \
        2>&1 | tee log_predict_${dataset}_${MODEL}.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ ${dataset} 完成"
    else
        echo "❌ ${dataset} 失败"
    fi
    
    echo ""
done

echo "======================================================================================================"
echo "✅ 所有预测完成！"
echo "======================================================================================================"

echo ""
echo "📁 生成的文件:"
ls -lh predictions_*.csv fs_model_*.csv 2>/dev/null

echo ""
echo "📊 对比历史准确率 vs 模型预测:"
echo "  历史准确率结果在: /mnt/localssd/fs_all_students_*.csv"
echo "  模型预测结果在: /mnt/localssd/pykt-toolkit/examples/fs_model_*.csv"

