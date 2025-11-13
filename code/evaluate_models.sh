#!/bin/bash
# 评估训练好的模型

cd /mnt/localssd/pykt-toolkit/examples
source activate pykt

echo "🔍 开始评估训练好的模型..."
echo "================================================================"
echo ""

# 评估 EdNet + LPKT
echo "1️⃣ 评估 EdNet + LPKT..."
python wandb_eval.py \
    --dataset_name=ednet \
    --model_name=lpkt \
    --emb_type=qid \
    --save_dir=saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0 \
    --fold=0 \
    > /tmp/eval_ednet_lpkt.log 2>&1
echo "   完成！日志: /tmp/eval_ednet_lpkt.log"
echo ""

# 评估 ASSISTments2017 + LPKT
echo "2️⃣ 评估 ASSISTments2017 + LPKT..."
python wandb_eval.py \
    --dataset_name=assist2017 \
    --model_name=lpkt \
    --emb_type=qid \
    --save_dir=saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0 \
    --fold=0 \
    > /tmp/eval_assist2017_lpkt.log 2>&1
echo "   完成！日志: /tmp/eval_assist2017_lpkt.log"
echo ""

# 评估 EdNet + simpleKT
echo "3️⃣ 评估 EdNet + simpleKT..."
python wandb_eval.py \
    --dataset_name=ednet \
    --model_name=simplekt \
    --emb_type=qid \
    --save_dir=saved_model/ednet_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0 \
    --fold=0 \
    > /tmp/eval_ednet_simplekt.log 2>&1
echo "   完成！日志: /tmp/eval_ednet_simplekt.log"
echo ""

# 评估 ASSISTments2017 + simpleKT  
echo "4️⃣ 评估 ASSISTments2017 + simpleKT..."
python wandb_eval.py \
    --dataset_name=assist2017 \
    --model_name=simplekt \
    --emb_type=qid \
    --save_dir=saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0 \
    --fold=0 \
    > /tmp/eval_assist2017_simplekt.log 2>&1
echo "   完成！日志: /tmp/eval_assist2017_simplekt.log"
echo ""

echo "================================================================"
echo "✅ 所有评估完成！"
echo ""
echo "📊 查看评估结果:"
echo "  cat /tmp/eval_ednet_lpkt.log | grep -E '(testauc|testacc|validauc|validacc)'"
echo "  cat /tmp/eval_assist2017_lpkt.log | grep -E '(testauc|testacc|validauc|validacc)'"
echo "  cat /tmp/eval_ednet_simplekt.log | grep -E '(testauc|testacc|validauc|validacc)'"
echo "  cat /tmp/eval_assist2017_simplekt.log | grep -E '(testauc|testacc|validauc|validacc)'"
echo ""

