#!/bin/bash

# Student Bank Creation - Final Run
# 这个脚本会在后台运行完整的bank创建过程

cd /mnt/localssd

echo "=========================================="
echo "  启动Student Bank创建 (nohup模式)"
echo "=========================================="
echo ""
echo "配置信息:"
echo "  - 数据集: ASSISTments2017, NIPS Task 3&4, Algebra2005, Bridge2Algebra2006"
echo "  - 学生数: ~8,345 个唯一学生"
echo "  - Temperature: 1.0 (Persona) / 0.7 (Memory)"
echo "  - 人称: 统一使用 'The student'"
echo "  - 风格: 6种自动轮换"
echo "  - 预计时间: ~10小时"
echo ""
echo "开始运行..."

# 激活conda环境并运行
nohup bash -c "source /home/colligo/miniconda3/etc/profile.d/conda.sh && conda activate pykt && cd /mnt/localssd && python -u create_student_bank_final.py" > bank_creation_full_final.log 2>&1 &


PID=$!
echo "✅ 后台进程已启动: PID $PID"
echo ""
echo "监控命令:"
echo "  查看日志: tail -f bank_creation_full_final.log"
echo "  检查进程: ps aux | grep create_student_bank_final"
echo "  查看文件: find bank -name '*.json' | wc -l"
echo "  停止进程: kill $PID"
echo ""

