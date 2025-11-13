#!/bin/bash

cd /mnt/localssd/pykt-toolkit/examples
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

# 模型目录
declare -A model_dirs
model_dirs["assist2017_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
model_dirs["assist2017_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
model_dirs["assist2017_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"

model_dirs["nips_task34_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
model_dirs["nips_task34_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
model_dirs["nips_task34_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"

model_dirs["algebra2005_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
model_dirs["algebra2005_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
model_dirs["algebra2005_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"

model_dirs["bridge2algebra2006_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
model_dirs["bridge2algebra2006_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
model_dirs["bridge2algebra2006_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"

datasets=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")
models=("lpkt" "dkt" "akt")

echo "========================================"
echo "最终版：生成所有Forgetting数据"
echo "直接在内存中预测，不依赖临时文件"
echo "========================================"
echo ""

task_count=0
mkdir -p /mnt/localssd/logs

for dataset in "${datasets[@]}"; do
    for model in "${models[@]}"; do
        key="${dataset}_${model}"
        save_dir="${model_dirs[$key]}"
        gpu=$((task_count % 8))
        
        log_file="/mnt/localssd/logs/final_${dataset}_${model}.log"
        
        echo "[$(date '+%H:%M:%S')] 启动: ${dataset} + ${model} (GPU ${gpu})"
        
        nohup python generate_fs_all_models_final.py \
            --dataset "${dataset}" \
            --model "${model}" \
            --save_dir "${save_dir}" \
            --gpu ${gpu} \
            > "${log_file}" 2>&1 &
        
        task_count=$((task_count + 1))
        
        if [ $((task_count % 2)) -eq 0 ]; then
            sleep 2
        fi
    done
done

echo ""
echo "✅ 所有12个任务已启动！"
echo ""
echo "监控: watch -n 5 'ps aux | grep generate_fs_all_models_final | grep -v grep | wc -l'"
echo "日志: tail -f /mnt/localssd/logs/final_*.log"

