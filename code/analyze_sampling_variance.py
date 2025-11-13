#!/opt/venv/bin/python3
"""
分析随机抽样对learning gain统计的影响
"""

import json
import random
import numpy as np

# 读取overall.json
with open('/mnt/localssd/bank/evaluation_results/TASA-llama-best-of-2/algebra2005/simple_time/overall.json') as f:
    data = json.load(f)

# 提取所有学生的best_learning_gain
all_students = data['students']
all_gains = [s['best_learning_gain'] for s in all_students]

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 随机抽样分析：20人样本 vs 全部26人")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# 全部26人的统计
full_mean = np.mean(all_gains)
full_std = np.std(all_gains, ddof=1)
full_median = np.median(all_gains)

print(f"🎯 全部 {len(all_gains)} 个学生的结果：")
print(f"   • 平均 Learning Gain:  {full_mean:.4f} ({full_mean*100:.1f}%)")
print(f"   • 标准差:              {full_std:.4f}")
print(f"   • 中位数:              {full_median:.4f} ({full_median*100:.1f}%)")
print(f"   • 最小值:              {min(all_gains):.4f} ({min(all_gains)*100:.1f}%)")
print(f"   • 最大值:              {max(all_gains):.4f} ({max(all_gains)*100:.1f}%)")
print("\n" + "─"*80 + "\n")

# 测试不同样本量
random.seed(42)  # 固定种子以便复现
sample_sizes = [10]
num_trials = 10

all_results = {}

for sample_size in sample_sizes:
    print(f"{'='*80}")
    print(f"🎯 样本量: {sample_size} 个学生")
    print(f"{'='*80}\n")
    
    results = []
    
    for trial in range(1, num_trials + 1):
        # 随机抽取学生
        sampled_indices = random.sample(range(len(all_students)), sample_size)
        sampled_students = [all_students[i] for i in sorted(sampled_indices)]
        sampled_gains = [s['best_learning_gain'] for s in sampled_students]
        
        # 计算统计量
        sample_mean = np.mean(sampled_gains)
        sample_std = np.std(sampled_gains, ddof=1)
        sample_median = np.median(sampled_gains)
        
        # 计算与全集的差异
        mean_diff = sample_mean - full_mean
        mean_diff_pct = (mean_diff / full_mean) * 100
        std_diff = sample_std - full_std
        median_diff = sample_median - full_median
        
        results.append({
            'trial': trial,
            'mean': sample_mean,
            'std': sample_std,
            'median': sample_median,
            'mean_diff': mean_diff,
            'mean_diff_pct': mean_diff_pct,
            'std_diff': std_diff,
            'median_diff': median_diff,
            'student_ids': [s['student_id'] for s in sampled_students]
        })
        
        print(f"🎲 随机抽样 #{trial} ({sample_size}个学生)：")
        print(f"   • 平均 Learning Gain:  {sample_mean:.4f} ({sample_mean*100:.1f}%)")
        print(f"   • 标准差:              {sample_std:.4f}")
        print(f"   • 中位数:              {sample_median:.4f} ({sample_median*100:.1f}%)")
        print(f"   • 最小值:              {min(sampled_gains):.4f} ({min(sampled_gains)*100:.1f}%)")
        print(f"   • 最大值:              {max(sampled_gains):.4f} ({max(sampled_gains)*100:.1f}%)")
        print()
        print(f"   📏 与全集的差异：")
        print(f"      - 平均值差异:  {mean_diff:+.4f} ({mean_diff_pct:+.1f}%)")
        print(f"      - 标准差差异:  {std_diff:+.4f}")
        print(f"      - 中位数差异:  {median_diff:+.4f}")
        print("\n" + "─"*80 + "\n")
    
    all_results[sample_size] = results
    
    # 汇总统计
    print(f"📈 汇总分析 ({sample_size}人样本)：\n")
    
    mean_diffs = [r['mean_diff'] for r in results]
    mean_diff_pcts = [r['mean_diff_pct'] for r in results]
    
    print(f"   平均值差异范围:")
    print(f"   • 绝对差异: {min(mean_diffs):+.4f} ~ {max(mean_diffs):+.4f}")
    print(f"   • 相对差异: {min(mean_diff_pcts):+.1f}% ~ {max(mean_diff_pcts):+.1f}%")
    print(f"   • 平均偏差: {np.mean(np.abs(mean_diffs)):.4f} ({np.mean(np.abs(mean_diff_pcts)):.1f}%)")
    print()
    
    print(f"   标准差差异范围:")
    std_diffs = [r['std_diff'] for r in results]
    print(f"   • {min(std_diffs):+.4f} ~ {max(std_diffs):+.4f}")
    print(f"   • 平均偏差: {np.mean(np.abs(std_diffs)):.4f}")
    print()
    
    print(f"   中位数差异范围:")
    median_diffs = [r['median_diff'] for r in results]
    print(f"   • {min(median_diffs):+.4f} ~ {max(median_diffs):+.4f}")
    print(f"   • 平均偏差: {np.mean(np.abs(median_diffs)):.4f}")
    print("\n" + "━"*80 + "\n")

# 对比不同样本量
print("\n" + "="*80)
print("📊 10人样本稳定性分析 (10次随机抽样)")
print("="*80 + "\n")

results = all_results[10]
mean_diff_pcts = [abs(r['mean_diff_pct']) for r in results]
avg_abs_pct_diff = np.mean(mean_diff_pcts)
min_pct_diff = min(mean_diff_pcts)
max_pct_diff = max(mean_diff_pcts)

print(f"   偏差分布:")
print(f"   • 最小偏差: {min_pct_diff:.1f}%")
print(f"   • 最大偏差: {max_pct_diff:.1f}%")
print(f"   • 平均偏差: {avg_abs_pct_diff:.1f}%")
print(f"   • 偏差标准差: {np.std(mean_diff_pcts):.1f}%")
print()

# 统计偏差范围分布
ranges = {"<5%": 0, "5-10%": 0, "10-15%": 0, ">15%": 0}
for pct in mean_diff_pcts:
    if pct < 5:
        ranges["<5%"] += 1
    elif pct < 10:
        ranges["5-10%"] += 1
    elif pct < 15:
        ranges["10-15%"] += 1
    else:
        ranges[">15%"] += 1

print(f"   偏差范围分布 (10次抽样):")
for range_name, count in ranges.items():
    print(f"   • {range_name:6s}: {count}次 ({count*10}%)")
print()

print("━"*80)
print("💡 结论：")
print("━"*80 + "\n")

if avg_abs_pct_diff < 5:
    conclusion = "与全部26人的结果非常接近，差异可忽略 ✅"
    recommendation = "10人样本足够代表全体"
elif avg_abs_pct_diff < 10:
    conclusion = "能较好代表全体，差异在可接受范围内 ⚠️"
    recommendation = "10人样本可用，但建议增加到15-20人更稳定"
else:
    conclusion = "与全体存在明显差异，建议增加样本量 ❌"
    recommendation = "建议至少使用20人样本"

print(f"   {conclusion}")
print(f"   平均相对偏差: ±{avg_abs_pct_diff:.1f}%")
print(f"   偏差范围: {min_pct_diff:.1f}% ~ {max_pct_diff:.1f}%")
print()
print(f"   💡 建议: {recommendation}")
print()
print("━"*80)

