#!/usr/bin/env python3
"""
统计TASA在不同lambda值和三种LLM backbone（GPT, Qwen, Llama）上的效果
"""

import json
import os
from pathlib import Path
import csv

# 设置
evaluation_dir = Path("/mnt/localssd/bank/evaluation_results")
lambda_values = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
backbones = ["gpt", "qwen", "llama"]
datasets = ["assist2017"]  # 可以扩展

# 收集数据
results = []

for backbone in backbones:
    for lambda_val in lambda_values:
        dir_name = f"TASA-lambda{lambda_val}-{backbone}"
        overall_file = evaluation_dir / dir_name / "assist2017" / "dkt" / "overall.json"
        
        if overall_file.exists():
            with open(overall_file, 'r') as f:
                data = json.load(f)
                
            results.append({
                'backbone': backbone,
                'lambda': lambda_val,
                'avg_learning_gain': data['strategy_max']['avg_learning_gain'],
                'std_learning_gain': data['strategy_max']['std_learning_gain'],
                'median_learning_gain': data['strategy_max']['median_learning_gain'],
                'num_students': data['num_students']
            })
            print(f"✓ 读取: {dir_name}")
        else:
            print(f"✗ 未找到: {dir_name}")

# 输出统计表格
print("\n" + "="*80)
print("TASA Lambda值实验结果统计 - 按Backbone分组")
print("="*80 + "\n")

for backbone in backbones:
    # 过滤并排序当前backbone的数据
    backbone_results = [r for r in results if r['backbone'] == backbone]
    backbone_results.sort(key=lambda x: x['lambda'])
    
    print(f"\n【{backbone.upper()}】")
    print("-" * 80)
    print(f"{'Lambda':<10} {'Avg Learning Gain':<20} {'Std':<15} {'Median':<15}")
    print("-" * 80)
    for row in backbone_results:
        print(f"{row['lambda']:<10.1f} {row['avg_learning_gain']:<20.4f} "
              f"{row['std_learning_gain']:<15.4f} {row['median_learning_gain']:<15.4f}")
    
    # 找到最佳lambda
    best_row = max(backbone_results, key=lambda x: x['avg_learning_gain'])
    print(f"\n最佳Lambda: {best_row['lambda']} (Avg Gain: {best_row['avg_learning_gain']:.4f})")

# 交叉对比表格 - 平均学习增益
print("\n" + "="*80)
print("Lambda值对比 - 平均学习增益 (Avg Learning Gain)")
print("="*80 + "\n")

# 创建pivot数据结构
pivot_data = {}
for lambda_val in lambda_values:
    pivot_data[lambda_val] = {}
    for backbone in backbones:
        for result in results:
            if result['lambda'] == lambda_val and result['backbone'] == backbone:
                pivot_data[lambda_val][backbone] = result['avg_learning_gain']
                break

# 打印表头
print(f"{'Lambda':<10}", end='')
for backbone in backbones:
    print(f"{backbone.upper():<15}", end='')
print()
print("-" * 55)

# 打印数据
for lambda_val in lambda_values:
    print(f"{lambda_val:<10.1f}", end='')
    for backbone in backbones:
        value = pivot_data[lambda_val].get(backbone, float('nan'))
        if value != float('nan'):
            print(f"{value:<15.6f}", end='')
        else:
            print(f"{'N/A':<15}", end='')
    print()

# 交叉对比表格 - 中位数学习增益
print("\n" + "="*80)
print("Lambda值对比 - 中位数学习增益 (Median Learning Gain)")
print("="*80 + "\n")

# 创建pivot数据结构（中位数）
pivot_data_median = {}
for lambda_val in lambda_values:
    pivot_data_median[lambda_val] = {}
    for backbone in backbones:
        for result in results:
            if result['lambda'] == lambda_val and result['backbone'] == backbone:
                pivot_data_median[lambda_val][backbone] = result['median_learning_gain']
                break

# 打印表头
print(f"{'Lambda':<10}", end='')
for backbone in backbones:
    print(f"{backbone.upper():<15}", end='')
print()
print("-" * 55)

# 打印数据
for lambda_val in lambda_values:
    print(f"{lambda_val:<10.1f}", end='')
    for backbone in backbones:
        value = pivot_data_median[lambda_val].get(backbone, float('nan'))
        if value != float('nan'):
            print(f"{value:<15.6f}", end='')
        else:
            print(f"{'N/A':<15}", end='')
    print()

# 保存CSV
output_csv = "/mnt/localssd/lambda_analysis_results.csv"
with open(output_csv, 'w', newline='') as f:
    fieldnames = ['backbone', 'lambda', 'avg_learning_gain', 'std_learning_gain', 'median_learning_gain', 'num_students']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)
print(f"\n✓ 详细数据已保存到: {output_csv}")

# 统计分析
print("\n" + "="*80)
print("关键发现")
print("="*80 + "\n")

# 每个backbone的最佳lambda
print("1. 各Backbone最佳Lambda值:")
for backbone in backbones:
    backbone_results = [r for r in results if r['backbone'] == backbone]
    best_row = max(backbone_results, key=lambda x: x['avg_learning_gain'])
    print(f"   - {backbone.upper()}: λ={best_row['lambda']} "
          f"(Gain={best_row['avg_learning_gain']:.4f})")

# 总体最佳配置
best_overall = max(results, key=lambda x: x['avg_learning_gain'])
print(f"\n2. 总体最佳配置: {best_overall['backbone'].upper()} with λ={best_overall['lambda']} "
      f"(Gain={best_overall['avg_learning_gain']:.4f})")

# Lambda=0 vs Lambda=1对比
print("\n3. Lambda=0 (无记忆) vs Lambda=1 (完全记忆):")
for backbone in backbones:
    gain_0 = next(r['avg_learning_gain'] for r in results if r['backbone'] == backbone and r['lambda'] == 0)
    gain_1 = next(r['avg_learning_gain'] for r in results if r['backbone'] == backbone and r['lambda'] == 1.0)
    improvement = ((gain_1 - gain_0) / gain_0) * 100
    print(f"   - {backbone.upper()}: {gain_0:.4f} → {gain_1:.4f} "
          f"({'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")

# 不同backbone之间的比较
print("\n4. Backbone性能对比 (在最佳Lambda下):")
best_by_backbone = []
for backbone in backbones:
    backbone_results = [r for r in results if r['backbone'] == backbone]
    best = max(r['avg_learning_gain'] for r in backbone_results)
    best_by_backbone.append((backbone, best))

best_by_backbone.sort(key=lambda x: x[1], reverse=True)
for i, (backbone, gain) in enumerate(best_by_backbone, 1):
    print(f"   {i}. {backbone.upper()}: {gain:.4f}")

# Lambda趋势分析
print("\n5. Lambda值趋势分析:")
for backbone in backbones:
    backbone_results = [r for r in results if r['backbone'] == backbone]
    backbone_results.sort(key=lambda x: x['lambda'])
    gains = [r['avg_learning_gain'] for r in backbone_results]
    
    # 计算趋势（简单的线性趋势）
    if gains[-1] > gains[0]:
        trend = "上升"
    elif gains[-1] < gains[0]:
        trend = "下降"
    else:
        trend = "持平"
    
    change = ((gains[-1] - gains[0]) / gains[0]) * 100
    print(f"   - {backbone.upper()}: 从λ=0到λ=1.0，Learning Gain {trend} {abs(change):.1f}%")

print("\n" + "="*80)

