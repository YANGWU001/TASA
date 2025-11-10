#!/bin/bash
# 自动监控TASA Llama完成后启动Baseline

TASA_PID=4118213
LOG_FILE="/mnt/localssd/logs/auto_baseline_starter.log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "🔍 监控TASA Llama进程 (PID: $TASA_PID)" | tee -a $LOG_FILE
echo "⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 等待TASA进程结束
while ps -p $TASA_PID > /dev/null 2>&1; do
    echo "[$(date '+%H:%M:%S')] TASA Llama still running..." | tee -a $LOG_FILE
    sleep 60  # 每分钟检查一次
done

echo "" | tee -a $LOG_FILE
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "✅ TASA Llama已完成！" | tee -a $LOG_FILE
echo "⏰ 完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 等待5秒
echo "⏳ 等待5秒后启动Baseline..." | tee -a $LOG_FILE
sleep 5

# 启动Baseline
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "🚀 启动Llama+Qwen Baseline..." | tee -a $LOG_FILE
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

cd /mnt/localssd
nohup /opt/venv/bin/python3 -u run_baselines_parallel_with_env.py > logs/baselines_llama_qwen_auto.log 2>&1 &
BASELINE_PID=$!

echo "✅ Baseline已启动！" | tee -a $LOG_FILE
echo "📋 PID: $BASELINE_PID" | tee -a $LOG_FILE
echo "📝 日志: logs/baselines_llama_qwen_auto.log" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a $LOG_FILE

