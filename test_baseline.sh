#!/bin/bash

# 快速测试一个baseline方法

METHOD=$1
DATASET=${2:-assist2017}

if [ -z "$METHOD" ]; then
    echo "用法: ./test_baseline.sh <method> [dataset]"
    echo ""
    echo "Methods:"
    echo "  Vanilla-ICL"
    echo "  MathChat"
    echo "  TutorLLM"
    echo "  PSS-MV"
    echo ""
    echo "Datasets (默认: assist2017):"
    echo "  assist2017"
    echo "  algebra2005"
    echo "  bridge2006"
    echo ""
    echo "示例: ./test_baseline.sh Vanilla-ICL assist2017"
    exit 1
fi

echo "=================================="
echo "🧪 测试 $METHOD on $DATASET"
echo "=================================="
echo ""
echo "只评估前3个学生..."
echo ""

/opt/venv/bin/python3 /mnt/localssd/evaluate_baselines.py \
    --method $METHOD \
    --dataset $DATASET \
    --max-workers 3 \
    --test

echo ""
echo "=================================="
echo "✅ 测试完成"
echo "=================================="

