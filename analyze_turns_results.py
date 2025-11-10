#!/usr/bin/env python3
"""
统计Turns数量对Vanilla-ICL-llama, TutorLLM, TASA三种方法的影响
"""

import json
import os
from pathlib import Path
import csv

# 设置
evaluation_dir = Path("/mnt/localssd/bank/evaluation_results")
turns_values = [0, 4, 8, 12, 16, 20, 24, 28]
methods = ["Vanilla-ICL", "TutorLLM", "TASA"]
datasets = ["assist2017"]

# 收集数据
results = []

for method in methods:
    for turns in turns_values:
        dir_name = f"{method}-turns{turns}-llama"
        overall_file = evaluation_dir / dir_name / "assist2017" / "dkt" / "overall.json"
        
        if overall_file.exists():
            with open(overall_file, 'r') as f:
                data = json.load(f)
            
            # TASA使用不同的数据结构（直接在顶层），其他方法使用strategy_max
            if 'strategy_max' in data:
                avg_gain = data['strategy_max']['avg_learning_gain']
                std_gain = data['strategy_max']['std_learning_gain']
                median_gain = data['strategy_max']['median_learning_gain']
            else:
                avg_gain = data['avg_learning_gain']
                std_gain = data['std_learning_gain']
                median_gain = data['median_learning_gain']
                
            results.append({
                'method': method,
                'turns': turns,
                'avg_learning_gain': avg_gain,
                'std_learning_gain': std_gain,
                'median_learning_gain': median_gain,
                'num_students': data['num_students']
            })
            print(f"✓ 读取: {dir_name}")
        else:
            print(f"✗ 未找到: {dir_name}")

# 输出统计表格
print("\n" + "="*80)
print("Turns数量实验结果统计 - 按方法分组")
print("="*80 + "\n")

for method in methods:
    # 过滤并排序当前方法的数据
    method_results = [r for r in results if r['method'] == method]
    method_results.sort(key=lambda x: x['turns'])
    
    print(f"\n【{method}】")
    print("-" * 80)
    print(f"{'Turns':<10} {'Avg Learning Gain':<20} {'Std':<15} {'Median':<15}")
    print("-" * 80)
    for row in method_results:
        print(f"{row['turns']:<10} {row['avg_learning_gain']:<20.4f} "
              f"{row['std_learning_gain']:<15.4f} {row['median_learning_gain']:<15.4f}")
    
    if method_results:
        # 找到最佳turns
        best_row = max(method_results, key=lambda x: x['avg_learning_gain'])
        print(f"\n最佳Turns: {best_row['turns']} (Avg Gain: {best_row['avg_learning_gain']:.4f})")
        
        # 计算从turns=0的提升
        turns0_row = next((r for r in method_results if r['turns'] == 0), None)
        if turns0_row and best_row['turns'] != 0:
            if turns0_row['avg_learning_gain'] > 0:
                improvement = ((best_row['avg_learning_gain'] - turns0_row['avg_learning_gain']) / 
                              turns0_row['avg_learning_gain']) * 100
                print(f"相比Turns=0提升: {improvement:+.1f}%")
            else:
                absolute_gain = best_row['avg_learning_gain'] - turns0_row['avg_learning_gain']
                print(f"相比Turns=0增加: +{absolute_gain:.4f} (Turns=0为零基线)")

# 交叉对比表格 - 平均学习增益
print("\n" + "="*80)
print("Turns值对比 - 平均学习增益 (Avg Learning Gain)")
print("="*80 + "\n")

# 创建pivot数据结构
pivot_data = {}
for turns in turns_values:
    pivot_data[turns] = {}
    for method in methods:
        for result in results:
            if result['turns'] == turns and result['method'] == method:
                pivot_data[turns][method] = result['avg_learning_gain']
                break

# 打印表头
print(f"{'Turns':<10}", end='')
for method in methods:
    print(f"{method:<20}", end='')
print()
print("-" * 70)

# 打印数据
for turns in turns_values:
    print(f"{turns:<10}", end='')
    for method in methods:
        value = pivot_data[turns].get(method, float('nan'))
        if value != float('nan'):
            print(f"{value:<20.6f}", end='')
        else:
            print(f"{'N/A':<20}", end='')
    print()

# 交叉对比表格 - 中位数学习增益
print("\n" + "="*80)
print("Turns值对比 - 中位数学习增益 (Median Learning Gain)")
print("="*80 + "\n")

# 创建pivot数据结构（中位数）
pivot_data_median = {}
for turns in turns_values:
    pivot_data_median[turns] = {}
    for method in methods:
        for result in results:
            if result['turns'] == turns and result['method'] == method:
                pivot_data_median[turns][method] = result['median_learning_gain']
                break

# 打印表头
print(f"{'Turns':<10}", end='')
for method in methods:
    print(f"{method:<20}", end='')
print()
print("-" * 70)

# 打印数据
for turns in turns_values:
    print(f"{turns:<10}", end='')
    for method in methods:
        value = pivot_data_median[turns].get(method, float('nan'))
        if value != float('nan'):
            print(f"{value:<20.6f}", end='')
        else:
            print(f"{'N/A':<20}", end='')
    print()

# 保存CSV
output_csv = "/mnt/localssd/turns_analysis_results.csv"
with open(output_csv, 'w', newline='') as f:
    fieldnames = ['method', 'turns', 'avg_learning_gain', 'std_learning_gain', 'median_learning_gain', 'num_students']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)
print(f"\n✓ 详细数据已保存到: {output_csv}")

# 统计分析
print("\n" + "="*80)
print("关键发现")
print("="*80 + "\n")

# 每个方法的最佳turns
print("1. 各方法最佳Turns值:")
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if method_results:
        best_row = max(method_results, key=lambda x: x['avg_learning_gain'])
        print(f"   - {method}: Turns={best_row['turns']} "
              f"(Gain={best_row['avg_learning_gain']:.4f})")

# 总体最佳配置
best_overall = max(results, key=lambda x: x['avg_learning_gain'])
print(f"\n2. 总体最佳配置: {best_overall['method']} with Turns={best_overall['turns']} "
      f"(Gain={best_overall['avg_learning_gain']:.4f})")

# Turns=0 vs 最佳Turns对比
print("\n3. Turns=0 (零样本) vs 最佳Turns配置:")
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if not method_results:
        continue
    
    turns0_result = next((r for r in method_results if r['turns'] == 0), None)
    best_result = max(method_results, key=lambda x: x['avg_learning_gain'])
    
    if turns0_result and best_result:
        if turns0_result['avg_learning_gain'] > 0:
            improvement = ((best_result['avg_learning_gain'] - turns0_result['avg_learning_gain']) / 
                          turns0_result['avg_learning_gain']) * 100
            print(f"   - {method}: {turns0_result['avg_learning_gain']:.4f} → "
                  f"{best_result['avg_learning_gain']:.4f} "
                  f"({'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%)")
        else:
            absolute_gain = best_result['avg_learning_gain'] - turns0_result['avg_learning_gain']
            print(f"   - {method}: {turns0_result['avg_learning_gain']:.4f} → "
                  f"{best_result['avg_learning_gain']:.4f} (从零基线提升)")

# 不同方法之间的比较
print("\n4. 方法性能对比 (在最佳Turns下):")
best_by_method = []
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if method_results:
        best = max(r['avg_learning_gain'] for r in method_results)
        best_by_method.append((method, best))

best_by_method.sort(key=lambda x: x[1], reverse=True)
for i, (method, gain) in enumerate(best_by_method, 1):
    print(f"   {i}. {method}: {gain:.4f}")

# Turns趋势分析
print("\n5. Turns增加的边际效益分析:")
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if not method_results:
        continue
    
    method_results.sort(key=lambda x: x['turns'])
    gains = [r['avg_learning_gain'] for r in method_results]
    
    # 计算总体趋势
    if gains[0] > 0:  # 只有在起始值非零时才计算百分比
        if gains[-1] > gains[0]:
            trend = "上升"
            change = ((gains[-1] - gains[0]) / gains[0]) * 100
        elif gains[-1] < gains[0]:
            trend = "下降"
            change = ((gains[0] - gains[-1]) / gains[0]) * 100
        else:
            trend = "持平"
            change = 0
        print(f"   - {method}: 从Turns=0到Turns=28，Learning Gain {trend} {abs(change):.1f}%")
    else:
        absolute_change = gains[-1] - gains[0]
        print(f"   - {method}: 从Turns=0到Turns=28，Learning Gain 增加 {absolute_change:.4f} (从零基线)")

# 计算边际收益递减点
print("\n6. 边际收益分析 (每增加4个turns的收益):")
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if not method_results:
        continue
    
    method_results.sort(key=lambda x: x['turns'])
    print(f"\n   {method}:")
    
    marginal_gains = []
    for i in range(1, len(method_results)):
        prev_gain = method_results[i-1]['avg_learning_gain']
        curr_gain = method_results[i]['avg_learning_gain']
        marginal = curr_gain - prev_gain
        turns_from = method_results[i-1]['turns']
        turns_to = method_results[i]['turns']
        marginal_gains.append((turns_from, turns_to, marginal))
        
        symbol = "↑" if marginal > 0 else "↓"
        print(f"      Turns {turns_from}→{turns_to}: {symbol} {abs(marginal):.4f}")
    
    # 找到收益最大的区间
    if marginal_gains:
        best_interval = max(marginal_gains, key=lambda x: x[2])
        print(f"      最佳增长区间: Turns {best_interval[0]}→{best_interval[1]} "
              f"(+{best_interval[2]:.4f})")

print("\n" + "="*80)

