#!/bin/bash

# 重新生成所有LPKT/DKT/AKT的forgetting数据（包含所有学生+delta_t/tau字段）

cd /mnt/localssd/pykt-toolkit/examples
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

# 定义数据集和模型
datasets=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")
models=("lpkt" "dkt" "akt")

# 模型目录映射（使用正确的目录名）
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

# 计数器
task_count=0
total_tasks=12  # 4 datasets * 3 models

echo "========================================"
echo "开始重新生成LPKT/DKT/AKT数据"
echo "总任务数: ${total_tasks}"
echo "========================================"
echo ""

# 启动所有任务（后台运行，使用nohup）
for dataset in "${datasets[@]}"; do
    for model in "${models[@]}"; do
        key="${dataset}_${model}"
        save_dir="${model_dirs[$key]}"
        
        # 使用GPU轮询（8个GPU）
        gpu=$((task_count % 8))
        
        log_file="/mnt/localssd/logs/regen_${dataset}_${model}.log"
        mkdir -p /mnt/localssd/logs
        
        echo "[任务 $((task_count+1))/${total_tasks}] ${dataset} + ${model} (GPU ${gpu})"
        echo "  模型目录: ${save_dir}"
        echo "  日志: ${log_file}"
        
        # 启动后台任务
        nohup python calc_fs_all_data_simple.py \
            --dataset "${dataset}" \
            --model "${model}" \
            --save_dir "${save_dir}" \
            --gpu ${gpu} \
            > "${log_file}" 2>&1 &
        
        echo "  PID: $!"
        echo ""
        
        task_count=$((task_count + 1))
        
        # 每启动2个任务休息一下，避免同时加载太多
        if [ $((task_count % 2)) -eq 0 ]; then
            sleep 2
        fi
    done
done

echo "========================================"
echo "✅ 所有任务已启动！"
echo "========================================"
echo ""
echo "监控命令:"
echo "  watch -n 5 'ps aux | grep calc_fs_all_data_simple | grep -v grep | wc -l'"
echo ""
echo "查看日志:"
echo "  tail -f /mnt/localssd/logs/regen_*.log"
echo ""
echo "检查进度:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/lpkt.json"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/dkt.json"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/akt.json"

