#!/bin/bash
#################################################################################
# 等待Qwen Baseline完成后自动启动TASA Ablation实验
#################################################################################

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║          🔬 等待Qwen Baseline完成后运行TASA Ablation Study                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 目标：等待Qwen baseline达到16/16
TARGET_QWEN=16
CHECK_INTERVAL=60  # 每60秒检查一次

echo "⏱️  监控设置:"
echo "   目标: Qwen完成 ${TARGET_QWEN}/16 任务"
echo "   检查间隔: ${CHECK_INTERVAL}秒"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    # 检查Qwen完成数量
    qwen_count=$(ls /mnt/localssd/bank/evaluation_results/*-qwen/*/overall.json 2>/dev/null | wc -l)
    
    current_time=$(date +"%H:%M:%S")
    echo "[$current_time] 🟣 Qwen: $qwen_count/$TARGET_QWEN"
    
    if [ "$qwen_count" -ge "$TARGET_QWEN" ]; then
        echo ""
        echo "✅ Qwen Baseline已完成所有任务！"
        echo ""
        break
    fi
    
    # 等待
    sleep $CHECK_INTERVAL
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 开始启动TASA Ablation Study..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Ablation配置:"
echo "   • 变体: w/o Persona, w/o Memory, w/o Forgetting"
echo "   • 数据集: Assist2017, NIPS34, Algebra2005, Bridge2006"
echo "   • Backbone: Llama-3.1-8B"
echo "   • Forgetting Method: lpkt"
echo "   • 总实验数: 3 × 4 = 12"
echo ""

# 切换到项目目录
cd /mnt/localssd

# 启动ablation实验
echo "🔬 启动TASA Ablation Study..."
/opt/venv/bin/python3 run_tasa_ablation_llama.py 2>&1 | tee logs/tasa_ablation_llama.log

# 检查完成状态
if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                   ✅ TASA Ablation Study 完成！                              ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 生成结果汇总
    echo "📊 生成结果汇总..."
    /opt/venv/bin/python3 << 'PYEOF'
import json
import os

ablations = ['woPersona', 'woMemory', 'woForgetting']
datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
forgetting_method = 'lpkt'

print("\n" + "="*80)
print("🔬 TASA Ablation Study - 结果汇总")
print("="*80 + "\n")

results_matrix = {}
for ablation in ablations:
    results_matrix[ablation] = {}
    for dataset in datasets:
        result_file = f'/mnt/localssd/bank/evaluation_results/TASA-{ablation}-llama/{dataset}/{forgetting_method}/overall.json'
        if os.path.exists(result_file):
            with open(result_file) as f:
                data = json.load(f)
                lg = data['strategy_max']['avg_learning_gain'] * 100
                std = data['strategy_max']['std_learning_gain'] * 100
                results_matrix[ablation][dataset] = (lg, std)
        else:
            results_matrix[ablation][dataset] = None

# 打印结果表格
print(f"{'Ablation':<20} | {'Assist2017':<12} | {'NIPS34':<12} | {'Algebra2005':<12} | {'Bridge2006':<12}")
print("-"*20 + "-+-" + "-+-".join(["-"*12]*4))

for ablation in ablations:
    row = [f"w/o {ablation[2:]:<13}"]
    for dataset in datasets:
        if results_matrix[ablation][dataset]:
            lg, std = results_matrix[ablation][dataset]
            row.append(f"{lg:>5.1f} ({std:.1f})")
        else:
            row.append("  -")
    print(" | ".join(row))

print("\n" + "="*80)
print("📈 完整版TASA结果（参考）:")
full_version = {
    'assist2017': (67.4, 1.0),
    'nips_task34': (52.4, 1.2),
    'algebra2005': (62.6, 1.5),
    'bridge2006': (53.9, 1.7)
}
row = ["Full TASA         "]
for dataset in datasets:
    lg, std = full_version[dataset]
    row.append(f"{lg:>5.1f} ({std:.1f})")
print(" | ".join(row))
print("="*80 + "\n")

# 计算平均下降
print("📉 相对完整版的性能下降:")
print(f"{'Ablation':<20} | {'平均LG':<10} | {'vs Full':<10} | {'下降幅度'}")
print("-"*20 + "-+-" + "-+-".join(["-"*10]*3))

full_avg = sum([v[0] for v in full_version.values()]) / len(full_version)

for ablation in ablations:
    valid_results = [v[0] for v in results_matrix[ablation].values() if v is not None]
    if valid_results:
        avg_lg = sum(valid_results) / len(valid_results)
        diff = full_avg - avg_lg
        percent = (diff / full_avg) * 100
        print(f"w/o {ablation[2:]:<13} | {avg_lg:>8.1f}% | {diff:>+8.1f}% | {percent:>6.1f}%")

print(f"{'Full TASA':<20} | {full_avg:>8.1f}% |     -      |   -")
print("\n" + "="*80 + "\n")
PYEOF
else
    echo ""
    echo "❌ TASA Ablation Study 执行过程中出现错误"
    echo "请查看日志: logs/tasa_ablation_llama.log"
fi

echo ""
echo "📁 结果文件位置:"
echo "   • 主日志: logs/tasa_ablation_llama.log"
echo "   • 各实验日志: logs/ablation_TASA-*-llama_*.log"
echo "   • 评估结果: bank/evaluation_results/TASA-wo*-llama/"
echo "   • 汇总JSON: logs/ablation_study_llama_results.json"
echo ""

