#!/bin/bash

# 运行完整的bank创建流程

echo "=========================================="
echo "  创建完整Student Bank"
echo "=========================================="
echo ""

cd /mnt/localssd

# 修改脚本为完整模式
echo "修改为完整模式..."
sed -i 's/TEST_MODE = True/TEST_MODE = False/' create_student_bank_v2.py
sed -i 's/max_students = 3/max_students = None/' create_student_bank_v2.py

echo "✅ 已切换到完整模式"
echo ""

# 运行
echo "开始处理所有数据集..."
echo "预计时间: 10-20小时"
echo ""

source activate pykt
nohup python -u create_student_bank_v2.py > bank_creation_full.log 2>&1 &

PID=$!
echo "✅ 后台进程已启动: PID $PID"
echo ""
echo "监控日志: tail -f /mnt/localssd/bank_creation_full.log"
echo "检查进程: ps aux | grep create_student_bank"
echo "查看GPU: nvidia-smi"
echo ""

