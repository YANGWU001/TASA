#!/bin/bash
# 并行运行所有数据集+所有模型的FS计算
# 使用8个GPU，每个GPU运行2个任务

cd /mnt/localssd/pykt-toolkit/examples

# 激活环境
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

echo "======================================================================================================"
echo "🚀 并行计算所有数据集的Forgetting Score"
echo "======================================================================================================"
echo ""
echo "配置:"
echo "  数据集: assist2017, nips_task34, algebra2005, bridge2algebra2006"
echo "  模型: lpkt, simplekt, dkt, akt"
echo "  GPU: 8个 (每个运行2个任务)"
echo "  数据范围: train + valid + test"
echo ""

# 定义数据集和模型目录的映射
declare -A MODEL_DIRS

# LPKT模型
MODEL_DIRS["assist2017_lpkt"]="saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0"
MODEL_DIRS["nips_task34_lpkt"]="saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
MODEL_DIRS["algebra2005_lpkt"]="saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
MODEL_DIRS["bridge2algebra2006_lpkt"]="saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"

# simpleKT模型
MODEL_DIRS["assist2017_simplekt"]="saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0"
MODEL_DIRS["nips_task34_simplekt"]="saved_model/nips_task34_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0"
MODEL_DIRS["algebra2005_simplekt"]="saved_model/algebra2005_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0"
MODEL_DIRS["bridge2algebra2006_simplekt"]="saved_model/bridge2algebra2006_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0"

# DKT模型
MODEL_DIRS["assist2017_dkt"]="saved_model/assist2017_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["nips_task34_dkt"]="saved_model/nips_task34_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["algebra2005_dkt"]="saved_model/algebra2005_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["bridge2algebra2006_dkt"]="saved_model/bridge2algebra2006_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"

# AKT模型  
MODEL_DIRS["assist2017_akt"]="saved_model/assist2017_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"
MODEL_DIRS["nips_task34_akt"]="saved_model/nips_task34_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"
MODEL_DIRS["algebra2005_akt"]="saved_model/algebra2005_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"
MODEL_DIRS["bridge2algebra2006_akt"]="saved_model/bridge2algebra2006_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"

# GPU分配
# GPU 0-7, 每个GPU运行2个任务
declare -a GPU_TASKS
for i in {0..7}; do
    GPU_TASKS[$i]=""
done

# 分配任务到GPU
task_id=0
gpu_id=0

DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")
MODELS=("lpkt" "simplekt" "dkt" "akt")

for dataset in "${DATASETS[@]}"; do
    for model in "${MODELS[@]}"; do
        key="${dataset}_${model}"
        save_dir="${MODEL_DIRS[$key]}"
        
        if [ -z "$save_dir" ] || [ ! -d "$save_dir" ]; then
            echo "⚠️  跳过 $key: 模型目录不存在"
            continue
        fi
        
        # 分配到GPU
        gpu=$((task_id % 8))
        
        log_file="log_fs_all_${dataset}_${model}_gpu${gpu}.txt"
        
        echo "📋 任务 $task_id: ${dataset} + ${model} -> GPU $gpu"
        
        # 后台运行
        nohup python calc_fs_all_data_simple.py \
            --dataset=$dataset \
            --model=$model \
            --save_dir="$save_dir" \
            --gpu=$gpu \
            > "$log_file" 2>&1 &
        
        pid=$!
        echo "   PID: $pid, Log: $log_file"
        
        # 短暂延迟避免同时启动
        sleep 2
        
        task_id=$((task_id + 1))
    done
done

echo ""
echo "======================================================================================================"
echo "✅ 所有任务已启动！"
echo "======================================================================================================"
echo ""
echo "📊 任务分布:"
echo "   总任务数: $task_id"
echo "   使用GPU: 8个"
echo "   每GPU任务: ~2个"
echo ""
echo "📁 输出位置:"
echo "   Bank数据: /mnt/localssd/bank/forgetting/<dataset>/<model>.json"
echo "   日志文件: /mnt/localssd/pykt-toolkit/examples/log_fs_all_*.txt"
echo ""
echo "🔍 监控命令:"
echo "   查看进程: ps aux | grep calculate_all_fs_all_models.py"
echo "   查看GPU: nvidia-smi"
echo "   查看日志: tail -f log_fs_all_assist2017_lpkt_gpu0.txt"
echo ""
echo "⏳ 预计完成时间: 30-60分钟（取决于数据量）"

