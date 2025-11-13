#!/usr/bin/env python3
"""
统计不同KT方法（Forgetting Score方法）在TASA系统中的效果
"""

import json
import os
from pathlib import Path
import csv

# 设置
evaluation_dir = Path("/mnt/localssd/bank/evaluation_results/TASA-llama-best-of-2")
methods = ["simple_time", "history", "lpkt", "dkt", "akt", "simplekt"]
datasets = ["assist2017", "nips_task34", "algebra2005", "bridge2006"]

# 收集数据
results = []

print("="*80)
print("提取不同KT方法（Forgetting Score方法）的评估结果")
print("="*80 + "\n")

for dataset in datasets:
    for method in methods:
        overall_file = evaluation_dir / dataset / method / "overall.json"
        
        if overall_file.exists():
            with open(overall_file, 'r') as f:
                data = json.load(f)
            
            results.append({
                'method': method,
                'dataset': dataset,
                'num_students': data['num_students'],
                'avg_learning_gain': data['overall']['avg_learning_gain'],
                'std_learning_gain': data['overall']['std_learning_gain'],
                'median_learning_gain': data['overall']['median_learning_gain']
            })
            print(f"✓ {method:12} @ {dataset:15}: {data['overall']['avg_learning_gain']:.4f}")
        else:
            print(f"✗ 未找到: {dataset}/{method}")

# 保存CSV
output_csv = "/mnt/localssd/kt_methods_results.csv"
with open(output_csv, 'w', newline='') as f:
    fieldnames = ['method', 'dataset', 'num_students', 'avg_learning_gain', 'std_learning_gain', 'median_learning_gain']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)

print(f"\n✓ 数据已保存到: {output_csv}\n")

# 生成对比表格
print("="*80)
print("不同KT方法在各数据集上的Learning Gain对比")
print("="*80 + "\n")

print(f"| Method       | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | Average |")
print(f"|--------------|------------|--------|-------------|------------|---------|")

method_averages = {}
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    
    gains = {}
    for dataset in datasets:
        result = next((r for r in method_results if r['dataset'] == dataset), None)
        if result:
            gains[dataset] = result['avg_learning_gain']
        else:
            gains[dataset] = None
    
    # 计算平均值
    valid_gains = [g for g in gains.values() if g is not None]
    avg_gain = sum(valid_gains) / len(valid_gains) if valid_gains else 0
    method_averages[method] = avg_gain
    
    # 格式化输出
    assist_str = f"{gains.get('assist2017', 0)*100:.1f}" if gains.get('assist2017') else "N/A"
    nips_str = f"{gains.get('nips_task34', 0)*100:.1f}" if gains.get('nips_task34') else "N/A"
    algebra_str = f"{gains.get('algebra2005', 0)*100:.1f}" if gains.get('algebra2005') else "N/A"
    bridge_str = f"{gains.get('bridge2006', 0)*100:.1f}" if gains.get('bridge2006') else "N/A"
    avg_str = f"**{avg_gain*100:.1f}**" if avg_gain > 0 else "N/A"
    
    # 格式化方法名
    method_display = f"**{method.upper()}**" if method in ['dkt', 'lpkt'] else method.capitalize().replace('_', ' ')
    
    print(f"| {method_display:12} | {assist_str:10} | {nips_str:6} | {algebra_str:11} | {bridge_str:10} | {avg_str:7} |")

# 数据集平均
print(f"|--------------|------------|--------|-------------|------------|---------|")
dataset_avgs = {}
for dataset in datasets:
    dataset_results = [r for r in results if r['dataset'] == dataset]
    avg = sum(r['avg_learning_gain'] for r in dataset_results) / len(dataset_results) if dataset_results else 0
    dataset_avgs[dataset] = avg

avg_str = f"{dataset_avgs.get('assist2017', 0)*100:.1f}"
nips_str = f"{dataset_avgs.get('nips_task34', 0)*100:.1f}"
algebra_str = f"{dataset_avgs.get('algebra2005', 0)*100:.1f}"
bridge_str = f"{dataset_avgs.get('bridge2006', 0)*100:.1f}"
total_avg = sum(dataset_avgs.values()) / len(dataset_avgs) * 100 if dataset_avgs else 0

print(f"| **Dataset Avg** | {avg_str:10} | {nips_str:6} | {algebra_str:11} | {bridge_str:10} | **{total_avg:.1f}** |")

# 方法排名
print("\n" + "="*80)
print("KT方法性能排名 (按平均Learning Gain)")
print("="*80 + "\n")

sorted_methods = sorted(method_averages.items(), key=lambda x: x[1], reverse=True)

print(f"{'排名':<6} {'方法':<15} {'平均Learning Gain':<20} {'相对最佳':<15}")
print("-" * 60)

best_gain = sorted_methods[0][1]
for i, (method, gain) in enumerate(sorted_methods, 1):
    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
    relative = f"{(gain/best_gain-1)*100:+.1f}%" if i > 1 else "基准"
    print(f"{emoji} {i:<4} {method.upper():<15} {gain*100:.2f}%{' '*13} {relative:<15}")

# 各数据集最佳方法
print("\n" + "="*80)
print("各数据集的最佳KT方法")
print("="*80 + "\n")

print(f"| 数据集 | 最佳方法 | Learning Gain | 与平均相比 |")
print(f"|--------|----------|---------------|-----------|")

for dataset in datasets:
    dataset_results = [r for r in results if r['dataset'] == dataset]
    best = max(dataset_results, key=lambda x: x['avg_learning_gain'])
    dataset_avg = dataset_avgs[dataset]
    improvement = (best['avg_learning_gain'] - dataset_avg) / dataset_avg * 100
    
    print(f"| {dataset.replace('_', ' ').title():15} | {best['method'].upper():8} | {best['avg_learning_gain']*100:.1f}% | +{improvement:.1f}% |")

# 稳定性分析
print("\n" + "="*80)
print("稳定性分析 (跨数据集的标准差)")
print("="*80 + "\n")

import statistics

method_stds = {}
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    gains = [r['avg_learning_gain'] for r in method_results]
    if len(gains) > 1:
        std = statistics.stdev(gains)
        method_stds[method] = std

sorted_by_stability = sorted(method_stds.items(), key=lambda x: x[1])

print(f"{'排名':<6} {'方法':<15} {'标准差':<15} {'稳定性':<15}")
print("-" * 55)

for i, (method, std) in enumerate(sorted_by_stability, 1):
    emoji = "✅" if i <= 2 else "⚠️" if i <= 4 else "❌"
    stability = "最稳定" if i == 1 else "较稳定" if i <= 3 else "较不稳定" if i <= 5 else "不稳定"
    print(f"{emoji} {i:<4} {method.upper():<15} {std:.4f}{' '*8} {stability:<15}")

# 知识追踪模型 vs 基线方法
print("\n" + "="*80)
print("知识追踪模型 vs 基线方法")
print("="*80 + "\n")

kt_models = ['lpkt', 'dkt', 'akt', 'simplekt']
baseline_methods = ['simple_time', 'history']

kt_results = [r for r in results if r['method'] in kt_models]
baseline_results = [r for r in results if r['method'] in baseline_methods]

kt_avg = sum(r['avg_learning_gain'] for r in kt_results) / len(kt_results) if kt_results else 0
baseline_avg = sum(r['avg_learning_gain'] for r in baseline_results) / len(baseline_results) if baseline_results else 0

improvement = (kt_avg - baseline_avg) / baseline_avg * 100

print(f"知识追踪模型平均 (LPKT, DKT, AKT, SimpleKT): {kt_avg*100:.2f}%")
print(f"基线方法平均 (Simple Time, History):         {baseline_avg*100:.2f}%")
print(f"提升: {kt_avg*100 - baseline_avg*100:.2f}% (相对提升 {improvement:.1f}%)")

if improvement > 0:
    print(f"\n✅ 结论: 知识追踪模型整体优于基线方法")
else:
    print(f"\n⚠️ 结论: 基线方法表现更好，可能模型训练有问题")

# 推荐策略
print("\n" + "="*80)
print("推荐策略")
print("="*80 + "\n")

best_method = sorted_methods[0]
most_stable = sorted_by_stability[0]

print(f"🏆 总体推荐: **{best_method[0].upper()}**")
print(f"   - 平均Learning Gain: {best_method[1]*100:.2f}%")
print(f"   - 理由: 在所有数据集上平均表现最佳")

print(f"\n🛡️ 稳定性优先: **{most_stable[0].upper()}**")
print(f"   - 跨数据集标准差: {most_stable[1]:.4f}")
print(f"   - 理由: 在不同数据集上表现最一致")

print(f"\n⚡ 快速部署: **SIMPLE_TIME**")
print(f"   - 理由: 无需训练模型，实现简单")

# 避免使用
worst_method = sorted_methods[-1]
print(f"\n❌ 避免使用: **{worst_method[0].upper()}**")
print(f"   - 平均Learning Gain: {worst_method[1]*100:.2f}%")
print(f"   - 理由: 表现最差，可能模型训练不充分或设计问题")

print("\n" + "="*80)

