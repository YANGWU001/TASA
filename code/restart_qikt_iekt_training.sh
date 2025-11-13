#!/bin/bash
# 重新启动qikt和iekt训练（修复设备bug后）

cd /mnt/localssd/pykt-toolkit/examples
source activate pykt

echo "🔄 重新启动qikt和iekt训练..."
echo ""

# GPU 4: EdNet + qikt
echo "🎯 [GPU 4] 启动 EdNet + qikt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=4 stdbuf -oL -eL python -u wandb_qikt_train.py --dataset_name=ednet --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/ednet_qikt.log 2>&1 &
echo "   PID: $!"
sleep 2

# GPU 5: ASSISTments2017 + qikt
echo "🎯 [GPU 5] 启动 ASSISTments2017 + qikt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=5 stdbuf -oL -eL python -u wandb_qikt_train.py --dataset_name=assist2017 --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/assist2017_qikt.log 2>&1 &
echo "   PID: $!"
sleep 2

# GPU 6: EdNet + iekt
echo "🎯 [GPU 6] 启动 EdNet + iekt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=6 stdbuf -oL -eL python -u wandb_iekt_train.py --dataset_name=ednet --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/ednet_iekt.log 2>&1 &
echo "   PID: $!"
sleep 2

# GPU 7: ASSISTments2017 + iekt
echo "🎯 [GPU 7] 启动 ASSISTments2017 + iekt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=7 stdbuf -oL -eL python -u wandb_iekt_train.py --dataset_name=assist2017 --use_wandb=1 --add_uuid=0 --fold=0" > /tmp/kt_training_logs/assist2017_iekt.log 2>&1 &
echo "   PID: $!"

echo ""
echo "✅ qikt和iekt训练已重新启动"
echo ""
echo "查看日志:"
echo "  tail -f /tmp/kt_training_logs/ednet_qikt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_qikt.log"
echo "  tail -f /tmp/kt_training_logs/ednet_iekt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_iekt.log"

