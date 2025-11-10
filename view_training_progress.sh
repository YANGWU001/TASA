#!/bin/bash
# 查看当前训练进度脚本

echo "🔍 训练进度监控"
echo "================================"
echo ""

# 检查进程
echo "📍 训练进程状态:"
ps aux | grep "wandb_lpkt_train" | grep -v grep | awk '{printf "  %-8s %-10s CPU: %4s%% 运行时长: %s\n", $2, $11, $3, $10}'
echo ""

# 检查GPU
echo "🖥️  GPU使用情况:"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "  GPU %s: 使用率=%s%%, 显存=%sMB/%sMB\n", $1, $2, $3, $4}'
echo ""

# 检查模型文件
echo "💾 模型Checkpoint更新时间:"
echo "  EdNet:"
stat -c "    %y" /mnt/localssd/pykt-toolkit/examples/saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/qid_model.ckpt 2>/dev/null || echo "    未生成"
echo "  ASSISTments2017:"
stat -c "    %y" /mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/qid_model.ckpt 2>/dev/null || echo "    未生成"
echo ""

# 尝试从wandb获取信息
echo "📊 如果启用了WandB，请访问: https://wandb.ai"
echo ""

echo "💡 提示:"
echo "  - 模型每个epoch后更新一次checkpoint"
echo "  - 如果checkpoint文件时间在更新，说明训练正常进行"
echo "  - 总共需要训练200个epochs"
echo ""
echo "查看详细进度："
echo "  方案1: 观察checkpoint文件更新时间"
echo "  方案2: 如果需要WandB和实时进度，运行: bash /mnt/localssd/restart_training_with_wandb.sh"

