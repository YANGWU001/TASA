#!/bin/bash
# 训练DKT和AKT模型

cd /mnt/localssd/pykt-toolkit/examples
source activate pykt

mkdir -p /tmp/kt_training_logs

echo "🚀 开始训练DKT和AKT模型..."
echo "================================================================"
echo ""
echo "📋 训练计划:"
echo "  GPU 2: EdNet + DKT"
echo "  GPU 3: ASSISTments2017 + DKT"
echo "  GPU 4: EdNet + AKT"
echo "  GPU 5: ASSISTments2017 + AKT"
echo ""
echo "开始训练..."
echo ""

# GPU 2: EdNet + DKT
echo "🎯 [GPU 2] 启动 EdNet + DKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=2 stdbuf -oL -eL python -u wandb_dkt_train.py --dataset_name=ednet --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/ednet_dkt.log 2>&1 &
DKT_EDNET_PID=$!
echo "   PID: $DKT_EDNET_PID"
sleep 3

# GPU 3: ASSISTments2017 + DKT
echo "🎯 [GPU 3] 启动 ASSISTments2017 + DKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=3 stdbuf -oL -eL python -u wandb_dkt_train.py --dataset_name=assist2017 --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/assist2017_dkt.log 2>&1 &
DKT_ASSIST_PID=$!
echo "   PID: $DKT_ASSIST_PID"
sleep 3

# GPU 4: EdNet + AKT
echo "🎯 [GPU 4] 启动 EdNet + AKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=4 stdbuf -oL -eL python -u wandb_akt_train.py --dataset_name=ednet --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/ednet_akt.log 2>&1 &
AKT_EDNET_PID=$!
echo "   PID: $AKT_EDNET_PID"
sleep 3

# GPU 5: ASSISTments2017 + AKT
echo "🎯 [GPU 5] 启动 ASSISTments2017 + AKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=5 stdbuf -oL -eL python -u wandb_akt_train.py --dataset_name=assist2017 --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/assist2017_akt.log 2>&1 &
AKT_ASSIST_PID=$!
echo "   PID: $AKT_ASSIST_PID"
sleep 3

echo ""
echo "================================================================"
echo "✅ 所有训练任务已启动！"
echo ""
echo "进程信息:"
echo "  GPU 2 (EdNet + DKT):           PID $DKT_EDNET_PID"
echo "  GPU 3 (ASSISTments2017 + DKT): PID $DKT_ASSIST_PID"
echo "  GPU 4 (EdNet + AKT):           PID $AKT_EDNET_PID"
echo "  GPU 5 (ASSISTments2017 + AKT): PID $AKT_ASSIST_PID"
echo ""
echo "📊 查看训练日志:"
echo "  tail -f /tmp/kt_training_logs/ednet_dkt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_dkt.log"
echo "  tail -f /tmp/kt_training_logs/ednet_akt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_akt.log"
echo ""
echo "🌐 WandB监控: https://wandb.ai"
echo ""
echo "✅ 所有训练使用nohup后台运行，可以安全关闭terminal"
echo "================================================================"

