#!/usr/bin/env python3
"""
从evaluation_results目录中提取所有Baseline方法的结果
"""

import json
import os
from pathlib import Path
import csv

# 设置
evaluation_dir = Path("/mnt/localssd/bank/evaluation_results")
methods = ["Vanilla-ICL", "TutorLLM", "MathChat", "PSS-MV"]
backbones = ["llama", "qwen", "gpt"]
datasets = ["assist2017", "nips_task34", "algebra2005", "bridge2006"]

# 收集数据
results = []

print("="*80)
print("提取Baseline结果数据")
print("="*80 + "\n")

for method in methods:
    for backbone in backbones:
        for dataset in datasets:
            dir_name = f"{method}-conservative-{backbone}"
            overall_file = evaluation_dir / dir_name / dataset / "overall.json"
            
            if overall_file.exists():
                with open(overall_file, 'r') as f:
                    data = json.load(f)
                
                results.append({
                    'method': method,
                    'backbone': backbone,
                    'dataset': dataset,
                    'num_students': data['num_students'],
                    'avg_learning_gain': data['strategy_max']['avg_learning_gain'],
                    'std_learning_gain': data['strategy_max']['std_learning_gain'],
                    'median_learning_gain': data['strategy_max']['median_learning_gain']
                })
                print(f"✓ {method}-{backbone}-{dataset}: {data['strategy_max']['avg_learning_gain']:.4f}")
            else:
                print(f"✗ 未找到: {dir_name}/{dataset}")

# 保存CSV
output_csv = "/mnt/localssd/baseline_results.csv"
with open(output_csv, 'w', newline='') as f:
    fieldnames = ['method', 'backbone', 'dataset', 'num_students', 'avg_learning_gain', 'std_learning_gain', 'median_learning_gain']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)

print(f"\n✓ 数据已保存到: {output_csv}\n")

# 生成README格式的表格
print("="*80)
print("Baseline方法对比表格 (按Backbone分组)")
print("="*80 + "\n")

for backbone in backbones:
    print(f"\n### {backbone.upper()} Backbone\n")
    print(f"| Method | Assist2017 | NIPS34 | Algebra2005 | Bridge2006 | 平均 |")
    print(f"|--------|-----------|---------|-------------|------------|------|")
    
    for method in methods:
        method_results = [r for r in results if r['method'] == method and r['backbone'] == backbone]
        
        if not method_results:
            continue
        
        # 按数据集顺序提取结果
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
        
        # 格式化输出
        assist_str = f"{gains['assist2017']*100:.1f}" if gains.get('assist2017') else "N/A"
        nips_str = f"{gains['nips_task34']*100:.1f}" if gains.get('nips_task34') else "N/A"
        algebra_str = f"{gains['algebra2005']*100:.1f}" if gains.get('algebra2005') else "N/A"
        bridge_str = f"{gains['bridge2006']*100:.1f}" if gains.get('bridge2006') else "N/A"
        avg_str = f"{avg_gain*100:.1f}" if avg_gain > 0 else "N/A"
        
        print(f"| {method} | {assist_str} | {nips_str} | {algebra_str} | {bridge_str} | {avg_str} |")

# 跨backbone对比
print("\n" + "="*80)
print("跨Backbone对比 (Assist2017数据集)")
print("="*80 + "\n")

print(f"| Method | GPT | Qwen | Llama | 最佳 |")
print(f"|--------|-----|------|-------|------|")

for method in methods:
    method_results = [r for r in results if r['method'] == method and r['dataset'] == 'assist2017']
    
    gains = {}
    for backbone in backbones:
        result = next((r for r in method_results if r['backbone'] == backbone), None)
        if result:
            gains[backbone] = result['avg_learning_gain']
        else:
            gains[backbone] = None
    
    # 找最佳
    valid_gains = {k: v for k, v in gains.items() if v is not None}
    best_backbone = max(valid_gains.items(), key=lambda x: x[1])[0] if valid_gains else "N/A"
    best_gain = valid_gains[best_backbone] if valid_gains else 0
    
    gpt_str = f"{gains.get('gpt', 0)*100:.1f}" if gains.get('gpt') else "N/A"
    qwen_str = f"{gains.get('qwen', 0)*100:.1f}" if gains.get('qwen') else "N/A"
    llama_str = f"{gains.get('llama', 0)*100:.1f}" if gains.get('llama') else "N/A"
    best_str = f"{best_backbone.upper()} ({best_gain*100:.1f})"
    
    print(f"| {method} | {gpt_str} | {qwen_str} | {llama_str} | {best_str} |")

# 总体排名
print("\n" + "="*80)
print("总体性能排名 (所有配置)")
print("="*80 + "\n")

# 计算每个方法的平均性能
method_avg = {}
for method in methods:
    method_results = [r for r in results if r['method'] == method]
    if method_results:
        avg_gain = sum(r['avg_learning_gain'] for r in method_results) / len(method_results)
        method_avg[method] = avg_gain

# 排序
sorted_methods = sorted(method_avg.items(), key=lambda x: x[1], reverse=True)

print(f"{'排名':<6} {'方法':<20} {'平均Learning Gain':<20}")
print("-" * 50)
for i, (method, gain) in enumerate(sorted_methods, 1):
    print(f"{i:<6} {method:<20} {gain*100:.2f}%")

print("\n" + "="*80)

