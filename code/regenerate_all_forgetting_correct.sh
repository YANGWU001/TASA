#!/bin/bash

# 重新生成所有Forgetting Score数据（使用正确的Concept ID）
# 修复了之前使用Question ID的问题

cd /mnt/localssd/pykt-toolkit/examples

# 定义任务
DATASETS=("assist2017" "nips_task34" "algebra2005" "bridge2algebra2006")
MODELS=("lpkt" "dkt" "akt")

# 创建日志目录
mkdir -p /mnt/localssd/logs/regen_correct

echo "=========================================="
echo "重新生成Forgetting Score数据（Concept Level）"
echo "=========================================="
echo ""
echo "数据集: ${DATASETS[@]}"
echo "模型: ${MODELS[@]}"
echo "总任务数: $((${#DATASETS[@]} * ${#MODELS[@]}))"
echo ""

# 定义模型目录（使用绝对路径）
declare -A MODEL_DIRS
MODEL_DIRS["assist2017_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
MODEL_DIRS["assist2017_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["assist2017_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"

MODEL_DIRS["nips_task34_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0"
MODEL_DIRS["nips_task34_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["nips_task34_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0"

MODEL_DIRS["algebra2005_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
MODEL_DIRS["algebra2005_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["algebra2005_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"

MODEL_DIRS["bridge2algebra2006_lpkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0"
MODEL_DIRS["bridge2algebra2006_dkt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0"
MODEL_DIRS["bridge2algebra2006_akt"]="/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_akt_qid_saved_model_42_0_0.2_256_512_8_4_0.0001_1_0"

# 并行运行所有任务
TASK_ID=0
for DATASET in "${DATASETS[@]}"; do
    for MODEL in "${MODELS[@]}"; do
        GPU_ID=$((TASK_ID % 8))
        KEY="${DATASET}_${MODEL}"
        SAVE_DIR="${MODEL_DIRS[$KEY]}"
        LOG_FILE="/mnt/localssd/logs/regen_correct/${KEY}.log"
        
        if [ -z "$SAVE_DIR" ]; then
            echo "❌ 跳过 $KEY - 找不到模型目录"
            continue
        fi
        
        if [ ! -d "$SAVE_DIR" ]; then
            echo "❌ 跳过 $KEY - 模型目录不存在: $SAVE_DIR"
            continue
        fi
        
        echo "🚀 启动 $KEY (GPU $GPU_ID)"
        
        nohup python generate_fs_all_models_final.py \
            --dataset "$DATASET" \
            --model "$MODEL" \
            --save_dir "$SAVE_DIR" \
            --gpu "$GPU_ID" \
            > "$LOG_FILE" 2>&1 &
        
        TASK_ID=$((TASK_ID + 1))
        sleep 1
    done
done

echo ""
echo "✅ 所有任务已启动！"
echo ""
echo "监控命令:"
echo "  watch -n 5 'ps aux | grep generate_fs_all_models_final.py | grep -v grep'"
echo ""
echo "查看日志:"
echo "  tail -f /mnt/localssd/logs/regen_correct/*.log"
echo ""
echo "检查进度:"
echo "  ls -lh /mnt/localssd/bank/forgetting/*/*.json"
