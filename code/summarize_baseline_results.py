#!/usr/bin/env python3
"""
统计所有baseline结果并生成表格
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# 定义baseline方法和数据集
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
BACKBONES = ['llama', 'qwen', 'gpt']
DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']

def load_learning_gain(result_path):
    """从overall.json读取learning gain"""
    try:
        with open(result_path, 'r') as f:
            data = json.load(f)
            # 使用strategy_max的avg_learning_gain（最佳表现）
            if 'strategy_max' in data and 'avg_learning_gain' in data['strategy_max']:
                return data['strategy_max']['avg_learning_gain'] * 100  # 转为百分比
            elif 'average_learning_gain' in data:
                return data['average_learning_gain'] * 100
            elif 'learning_gain' in data:
                return data['learning_gain'] * 100
    except Exception as e:
        print(f"❌ 读取失败: {result_path} - {e}")
        return None

def main():
    results = defaultdict(lambda: defaultdict(dict))
    
    # 收集所有结果
    base_dir = Path('/mnt/localssd/bank/evaluation_results')
    
    for method in METHODS:
        for backbone in BACKBONES:
            for dataset in DATASETS:
                # 构造路径
                result_dir = base_dir / f"{method}-conservative-{backbone}" / dataset
                overall_path = result_dir / "overall.json"
                
                if overall_path.exists():
                    learning_gain = load_learning_gain(overall_path)
                    if learning_gain is not None:
                        results[method][backbone][dataset] = learning_gain
                        print(f"✅ {method}-{backbone} on {dataset}: {learning_gain:.1f}%")
    
    # 生成表格
    print("\n" + "="*100)
    print("📊 Baseline Results Summary (Learning Gain %)")
    print("="*100)
    
    # 按backbone分组显示
    for backbone in BACKBONES:
        print(f"\n{'='*100}")
        print(f"🎯 Backbone: {backbone.upper()}")
        print(f"{'='*100}")
        
        # 表头
        header = f"{'Method':<20}"
        for dataset in DATASETS:
            header += f"{dataset:>15}"
        print(header)
        print("-" * 100)
        
        # 每个方法
        for method in METHODS:
            row = f"{method:<20}"
            for dataset in DATASETS:
                if dataset in results[method][backbone]:
                    gain = results[method][backbone][dataset]
                    row += f"{gain:>14.1f}%"
                else:
                    row += f"{'N/A':>15}"
            print(row)
    
    # 生成对比表格（所有backbone）
    print(f"\n{'='*100}")
    print("📊 Complete Comparison Table")
    print(f"{'='*100}")
    
    header = f"{'Method':<30}"
    for dataset in DATASETS:
        header += f"{dataset:>17}"
    print(header)
    print("-" * 130)
    
    for method in METHODS:
        for backbone in BACKBONES:
            row = f"{method}-{backbone:<26}"
            for dataset in DATASETS:
                if dataset in results[method][backbone]:
                    gain = results[method][backbone][dataset]
                    row += f"{gain:>16.1f}%"
                else:
                    row += f"{'N/A':>17}"
            print(row)
        print("-" * 130)
    
    # 统计完成情况
    print(f"\n{'='*100}")
    print("📈 Completion Status")
    print(f"{'='*100}")
    
    total_tasks = len(METHODS) * len(BACKBONES) * len(DATASETS)
    completed_tasks = sum(
        1 for method in METHODS 
        for backbone in BACKBONES 
        for dataset in DATASETS 
        if dataset in results[method][backbone]
    )
    
    print(f"Total Tasks: {total_tasks}")
    print(f"Completed: {completed_tasks}")
    print(f"Missing: {total_tasks - completed_tasks}")
    print(f"Completion Rate: {completed_tasks/total_tasks*100:.1f}%")
    
    # 列出缺失的任务
    if completed_tasks < total_tasks:
        print(f"\n{'='*100}")
        print("❌ Missing Tasks:")
        print(f"{'='*100}")
        for method in METHODS:
            for backbone in BACKBONES:
                for dataset in DATASETS:
                    if dataset not in results[method][backbone]:
                        print(f"  • {method}-{backbone} on {dataset}")

if __name__ == '__main__':
    main()

