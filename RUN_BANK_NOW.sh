#!/bin/bash

# 激活conda环境并运行bank creation
# 使用最新的架构：30个进程按学生并行，每个worker的BGE只加载一次

echo "=================================================="
echo "🚀 启动 Student Bank Creation"
echo "=================================================="
echo ""
echo "📋 配置信息："
echo "  - 并行进程: 30个"
echo "  - 架构: 按学生并行（LLM + BGE + 保存）"
echo "  - BGE加载: 每个worker进程只加载一次"
echo "  - 数据集: ASSISTments2017, EdNet, Algebra2005, Bridge2006"
echo "  - 预计学生数: ~8,345"
echo "  - 预计时间: ~23分钟"
echo ""
echo "=================================================="
echo ""

# 激活conda环境
source /home/colligo/miniconda3/etc/profile.d/conda.sh
conda activate pykt

# 进入工作目录
cd /mnt/localssd

# 运行（后台模式）
nohup python -u create_student_bank_final.py > bank_creation_final_run.log 2>&1 &

# 获取PID
PID=$!
echo "✅ 已启动！"
echo ""
echo "📊 监控信息："
echo "  - PID: $PID"
echo "  - 日志: tail -f /mnt/localssd/bank_creation_final_run.log"
echo "  - 查看进程: ps -p $PID -o pid,cmd,%cpu,%mem,etime"
echo "  - 停止: kill $PID"
echo ""
echo "=================================================="

