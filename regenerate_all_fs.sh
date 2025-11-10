#!/bin/bash
# 重新生成所有Forgetting Score数据（使用所有数据：train+valid+test）

cd /mnt/localssd/pykt-toolkit/examples

source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

echo "======================================================================================================"
echo "🔧 重新生成所有Forgetting Score (使用train+valid+test所有数据)"
echo "======================================================================================================"
echo ""
echo "将生成 12个文件 (4数据集 × 3模型):"
echo "  LPKT:  assist2017, nips_task34, algebra2005, bridge2006"
echo "  DKT:   assist2017, nips_task34, algebra2005, bridge2006"
echo "  AKT:   assist2017, nips_task34, algebra2005, bridge2006"
echo ""
echo "使用8个GPU并行处理"
echo ""

# Tau值
TAU_ASSIST=2.93
TAU_NIPS=2.93
TAU_ALGEBRA=0.70
TAU_BRIDGE=0.70

# 任务配置
declare -a TASKS=(
    "assist2017:lpkt:saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0:0:${TAU_ASSIST}"
    "assist2017:dkt:saved_model/assist2017_dkt_qid_saved_model_42_0_0.001_0.0_256_256_4_0:1:${TAU_ASSIST}"
    "assist2017:akt:saved_model/assist2017_akt_qid_saved_model_42_0_0.001_0.0_256_256_4_10_0.05_0_0_0_1_0:2:${TAU_ASSIST}"
    
    "nips_task34:lpkt:saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0:3:${TAU_NIPS}"
    "nips_task34:dkt:saved_model/nips_task34_dkt_qid_saved_model_42_0_0.001_0.0_256_256_4_1_0:4:${TAU_NIPS}"
    "nips_task34:akt:saved_model/nips_task34_akt_qid_saved_model_42_0_0.001_0.0_256_256_4_10_0.05_0_0_0_1_0:5:${TAU_NIPS}"
    
    "algebra2005:lpkt:saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0:6:${TAU_ALGEBRA}"
    "algebra2005:dkt:saved_model/algebra2005_dkt_qid_saved_model_42_0_0.001_0.0_256_256_4_0_0:7:${TAU_ALGEBRA}"
    "algebra2005:akt:saved_model/algebra2005_akt_qid_saved_model_42_0_0.001_0.0_256_256_4_10_0.05_0_0_0_0_0:0:${TAU_ALGEBRA}"
    
    "bridge2algebra2006:lpkt:saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0:1:${TAU_BRIDGE}"
    "bridge2algebra2006:dkt:saved_model/bridge2algebra2006_dkt_qid_saved_model_42_0_0.001_0.0_256_256_4_1_0:2:${TAU_BRIDGE}"
    "bridge2algebra2006:akt:saved_model/bridge2algebra2006_akt_qid_saved_model_42_0_0.001_0.0_256_256_4_10_0.05_0_0_0_1_0:3:${TAU_BRIDGE}"
)

# 启动所有任务
pids=()
for task in "${TASKS[@]}"; do
    IFS=':' read -r dataset model save_dir gpu tau <<< "$task"
    
    echo "启动: $dataset + $model (GPU $gpu)"
    
    CUDA_VISIBLE_DEVICES=$gpu python calc_fs_all_data_simple.py \
        --dataset=$dataset \
        --model=$model \
        --save_dir=$save_dir \
        --gpu=0 \
        --tau=$tau \
        > log_regen_${dataset}_${model}.txt 2>&1 &
    
    pids+=($!)
    sleep 2  # 避免同时启动导致资源冲突
done

echo ""
echo "所有任务已启动，等待完成..."
echo "任务PID: ${pids[@]}"
echo ""

# 等待所有任务完成
for pid in "${pids[@]}"; do
    wait $pid
done

echo ""
echo "======================================================================================================"
echo "📊 检查生成结果"
echo "======================================================================================================"
echo ""

success=0
failed=0

for task in "${TASKS[@]}"; do
    IFS=':' read -r dataset model save_dir gpu tau <<< "$task"
    
    # 确定输出路径
    if [ "$dataset" = "bridge2algebra2006" ]; then
        output_file="/mnt/localssd/bank/forgetting/bridge2006/${model}.json"
    else
        output_file="/mnt/localssd/bank/forgetting/${dataset}/${model}.json"
    fi
    
    if [ -f "$output_file" ]; then
        size=$(ls -lh "$output_file" | awk '{print $5}')
        echo "✅ ${dataset}/${model}.json ($size)"
        ((success++))
    else
        echo "❌ ${dataset}/${model}.json 失败"
        ((failed++))
        echo "   查看日志: log_regen_${dataset}_${model}.txt"
    fi
done

echo ""
echo "======================================================================================================"
echo "完成: $success/12 成功, $failed/12 失败"
echo "======================================================================================================"

