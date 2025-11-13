#!/bin/bash
# 使用训练好的KT模型预测并计算Forgetting Score

echo "======================================================================================================"
echo "🚀 使用LPKT模型预测并计算Forgetting Score"
echo "======================================================================================================"

cd /mnt/localssd/pykt-toolkit/examples

# 激活conda环境
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

# 数据集和对应的模型目录
declare -A DATASETS
DATASETS[assist2017]="saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0"
DATASETS[nips_task34]="saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
DATASETS[algebra2005]="saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
DATASETS[bridge2algebra2006]="saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"

echo ""
echo "配置:"
echo "  模型: LPKT"
echo "  数据集: assist2017, nips_task34, algebra2005, bridge2algebra2006"
echo "  设备: CPU (稳定可靠)"
echo ""

# 为每个数据集运行预测
for dataset in assist2017 nips_task34 algebra2005 bridge2algebra2006; do
    save_dir="${DATASETS[$dataset]}"
    
    if [ ! -d "$save_dir" ]; then
        echo "⚠️  模型目录不存在: $save_dir"
        continue
    fi
    
    echo "======================================================================================================"
    echo "📊 数据集: ${dataset^^}"
    echo "======================================================================================================"
    
    python predict_and_calc_fs.py \
        --save_dir="$save_dir" \
        --batch_size=256 \
        --use_cpu \
        2>&1 | tee "log_fs_${dataset}_lpkt.txt"
    
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
echo "📁 生成的文件汇总:"
echo ""

for dataset in assist2017 nips_task34 algebra2005 bridge2algebra2006; do
    save_dir="${DATASETS[$dataset]}"
    if [ -d "$save_dir" ]; then
        echo "📂 ${dataset^^}:"
        ls -lh "$save_dir"/*.csv 2>/dev/null | awk '{print "  "$9" ("$5")"}'
        echo ""
    fi
done

echo "💡 结果说明:"
echo "  - predictions_*.csv: 模型的详细预测（每个时间步）"
echo "  - fs_*.csv: 计算的Forgetting Scores（每个学生-concept对）"
echo ""
echo "📊 与历史准确率对比:"
echo "  - 历史准确率: /mnt/localssd/fs_all_students_*.csv"
echo "  - 模型预测: saved_model/*/fs_*.csv"

