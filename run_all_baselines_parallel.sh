#!/bin/bash

# 并行运行所有baseline任务
# 每个任务单独运行，结果保存后手动移动到正确目录

DATASETS=("assist2017" "algebra2005" "bridge2006" "nips_task34")
METHODS=("Vanilla-ICL" "MathChat" "TutorLLM" "PSS-MV")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 并行运行所有Baseline任务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 函数：运行单个baseline并移动结果
run_baseline() {
    local method=$1
    local dataset=$2
    local backbone=$3
    local backbone_suffix=$4
    
    echo "[$backbone] 运行 $method on $dataset..."
    
    # 更新tasa_config.py
    python3 << EOF
import re
with open('/mnt/localssd/tasa_config.py', 'r') as f:
    content = f.read()
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.startswith('TUTOR_MODEL = '):
        lines[i] = f'TUTOR_MODEL = "$backbone"'
with open('/mnt/localssd/tasa_config.py', 'w') as f:
    f.write('\n'.join(lines))
EOF
    
    # 运行baseline
    students_file="/mnt/localssd/qualified_students_${dataset}_sampled10.json"
    log_file="/mnt/localssd/logs/baseline_${method}_${backbone_suffix}_${dataset}.log"
    
    /opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_conservative.py \
        --method "$method" \
        --dataset "$dataset" \
        --students-file "$students_file" \
        --max-workers 40 \
        > "$log_file" 2>&1
    
    # 移动结果到正确目录
    source_dir="/mnt/localssd/bank/evaluation_results/${method}-conservative/${dataset}"
    target_dir="/mnt/localssd/bank/evaluation_results/${method}-conservative-${backbone_suffix}/${dataset}"
    
    if [ -d "$source_dir" ]; then
        mkdir -p "$(dirname "$target_dir")"
        mv "$source_dir" "$target_dir"
        echo "[$backbone] ✅ $method on $dataset 完成"
    else
        echo "[$backbone] ❌ $method on $dataset 失败"
    fi
}

export -f run_baseline

# 生成所有任务
tasks=()

# Llama任务
for dataset in "${DATASETS[@]}"; do
    for method in "${METHODS[@]}"; do
        tasks+=("$method|$dataset|llama-3.1-8B-Instruct|llama")
    done
done

# Qwen任务
for dataset in "${DATASETS[@]}"; do
    for method in "${METHODS[@]}"; do
        tasks+=("$method|$dataset|Qwen3-4B-Instruct|qwen")
    done
done

echo "总任务数: ${#tasks[@]}"
echo ""

# 使用GNU parallel并行运行（如果没有则顺序执行）
if command -v parallel &> /dev/null; then
    echo "使用 GNU parallel 并行执行 (最多8个并行任务)..."
    printf '%s\n' "${tasks[@]}" | parallel -j 8 --colsep '|' run_baseline {1} {2} {3} {4}
else
    echo "顺序执行所有任务..."
    for task in "${tasks[@]}"; do
        IFS='|' read -r method dataset backbone backbone_suffix <<< "$task"
        run_baseline "$method" "$dataset" "$backbone" "$backbone_suffix"
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 所有任务完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

