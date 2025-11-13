#!/bin/bash

# 运行完整的Student Bank创建（最终版）

echo "=========================================="
echo "  创建完整Student Bank - 最终版"
echo "=========================================="
echo ""

cd /mnt/localssd

# 修改脚本为完整模式
echo "修改为完整模式..."
sed -i 's/TEST_MODE = True/TEST_MODE = False/' create_student_bank_final.py
sed -i 's/max_students = 3/max_students = None/' create_student_bank_final.py

echo "✅ 已切换到完整模式"
echo ""

# 显示配置
echo "配置:"
echo "  - Temperature: 1.0 (Persona) / 0.7 (Memory)"
echo "  - 存储: 每个学生单独文件"
echo "  - Concept: 真实文本描述"
echo "  - Memory: 6种多样化模板"
echo "  - 数据范围: train_valid + test (完整数据集)"
echo "  - GPU: cuda:0"
echo ""

echo "数据集 (唯一学生数):"
echo "  - ASSISTments2017: ~1,708 学生 (train_valid + test)"
echo "  - NIPS Task 3&4: ~4,918 学生 (train_valid + test)"
echo "  - Algebra2005: ~574 学生 (train_valid + test)"
echo "  - Bridge2Algebra2006: ~1,145 学生 (train_valid + test)"
echo "  总计: ~8,345 个唯一学生"
echo ""

echo "预计输出:"
echo "  - 文件数: ~41,725 个"
echo "  - 存储: ~3.7GB"
echo "  - 时间: ~10小时"
echo ""

# 运行
source activate pykt
echo "开始后台运行..."
CUDA_VISIBLE_DEVICES=0 nohup python -u create_student_bank_final.py > bank_creation_full_final.log 2>&1 &

PID=$!
echo "✅ 后台进程已启动: PID $PID"
echo ""
echo "监控方法:"
echo "  1. 实时日志: tail -f /mnt/localssd/bank_creation_full_final.log"
echo "  2. 检查进程: ps aux | grep create_student_bank_final"
echo "  3. GPU使用: nvidia-smi"
echo "  4. 文件统计: ls -lh /mnt/localssd/bank/persona/*/data/ | wc -l"
echo ""

