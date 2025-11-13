#!/bin/bash
# 批量训练多个KT模型的脚本
# 使用GPU 2-7训练3个模型 × 2个数据集 = 6个训练任务

echo "🚀 开始批量训练KT模型..."
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo ""

# 进入工作目录
cd /mnt/localssd/pykt-toolkit/examples

# 激活环境
source activate pykt

# 创建日志目录
mkdir -p /tmp/kt_training_logs

echo "📋 训练计划:"
echo "  GPU 2: EdNet + simpleKT"
echo "  GPU 3: ASSISTments2017 + simpleKT"
echo "  GPU 4: EdNet + qikt"
echo "  GPU 5: ASSISTments2017 + qikt"
echo "  GPU 6: EdNet + iekt"
echo "  GPU 7: ASSISTments2017 + iekt"
echo ""
echo "开始训练..."
echo ""

# GPU 2: EdNet + simpleKT
echo "🎯 [GPU 2] 启动 EdNet + simpleKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=2 stdbuf -oL -eL python -u wandb_train.py --dataset_name=ednet --model_name=simplekt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.2 --d_model=128 --n_blocks=2 --final_fc_dim=256" > /tmp/kt_training_logs/ednet_simplekt.log 2>&1 &
EDNET_SIMPLEKT_PID=$!
echo "   PID: $EDNET_SIMPLEKT_PID"
sleep 2

# GPU 3: ASSISTments2017 + simpleKT
echo "🎯 [GPU 3] 启动 ASSISTments2017 + simpleKT..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=3 stdbuf -oL -eL python -u wandb_train.py --dataset_name=assist2017 --model_name=simplekt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.2 --d_model=128 --n_blocks=2 --final_fc_dim=256" > /tmp/kt_training_logs/assist2017_simplekt.log 2>&1 &
ASSIST_SIMPLEKT_PID=$!
echo "   PID: $ASSIST_SIMPLEKT_PID"
sleep 2

# GPU 4: EdNet + qikt
echo "🎯 [GPU 4] 启动 EdNet + qikt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=4 stdbuf -oL -eL python -u wandb_train.py --dataset_name=ednet --model_name=qikt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.1 --emb_size=128" > /tmp/kt_training_logs/ednet_qikt.log 2>&1 &
EDNET_QIKT_PID=$!
echo "   PID: $EDNET_QIKT_PID"
sleep 2

# GPU 5: ASSISTments2017 + qikt
echo "🎯 [GPU 5] 启动 ASSISTments2017 + qikt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=5 stdbuf -oL -eL python -u wandb_train.py --dataset_name=assist2017 --model_name=qikt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.1 --emb_size=128" > /tmp/kt_training_logs/assist2017_qikt.log 2>&1 &
ASSIST_QIKT_PID=$!
echo "   PID: $ASSIST_QIKT_PID"
sleep 2

# GPU 6: EdNet + iekt
echo "🎯 [GPU 6] 启动 EdNet + iekt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=6 stdbuf -oL -eL python -u wandb_train.py --dataset_name=ednet --model_name=iekt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.2 --d_model=128 --n_blocks=2" > /tmp/kt_training_logs/ednet_iekt.log 2>&1 &
EDNET_IEKT_PID=$!
echo "   PID: $EDNET_IEKT_PID"
sleep 2

# GPU 7: ASSISTments2017 + iekt
echo "🎯 [GPU 7] 启动 ASSISTments2017 + iekt..."
nohup bash -c "source activate pykt && cd /mnt/localssd/pykt-toolkit/examples && CUDA_VISIBLE_DEVICES=7 stdbuf -oL -eL python -u wandb_train.py --dataset_name=assist2017 --model_name=iekt --emb_type=qid --save_dir=saved_model --use_wandb=1 --add_uuid=0 --fold=0 --learning_rate=1e-3 --dropout=0.2 --d_model=128 --n_blocks=2" > /tmp/kt_training_logs/assist2017_iekt.log 2>&1 &
ASSIST_IEKT_PID=$!
echo "   PID: $ASSIST_IEKT_PID"
sleep 2

echo ""
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo "✅ 所有训练任务已启动！"
echo ""
echo "进程信息:"
echo "  GPU 2 (EdNet + simpleKT):         PID $EDNET_SIMPLEKT_PID"
echo "  GPU 3 (ASSISTments2017 + simpleKT): PID $ASSIST_SIMPLEKT_PID"
echo "  GPU 4 (EdNet + qikt):             PID $EDNET_QIKT_PID"
echo "  GPU 5 (ASSISTments2017 + qikt):     PID $ASSIST_QIKT_PID"
echo "  GPU 6 (EdNet + iekt):             PID $EDNET_IEKT_PID"
echo "  GPU 7 (ASSISTments2017 + iekt):     PID $ASSIST_IEKT_PID"
echo ""
echo "📊 查看训练日志:"
echo "  tail -f /tmp/kt_training_logs/ednet_simplekt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_simplekt.log"
echo "  tail -f /tmp/kt_training_logs/ednet_qikt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_qikt.log"
echo "  tail -f /tmp/kt_training_logs/ednet_iekt.log"
echo "  tail -f /tmp/kt_training_logs/assist2017_iekt.log"
echo ""
echo "🌐 WandB监控:"
echo "  访问 https://wandb.ai 查看训练进度"
echo ""
echo "🔍 查看GPU使用情况:"
echo "  nvidia-smi"
echo ""
echo "✅ 所有训练使用nohup后台运行，可以安全关闭terminal"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 

