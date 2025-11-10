#!/usr/bin/env python3
"""
生成Table 2：TASA消融实验
直接使用TASA (GPT)作为TASA-llama的proxy
"""

import sys
import os
import json
import random
from concurrent.futures import ThreadPoolExecutor
sys.path.append('/mnt/localssd')

from llm_as_judge_personalization import judge_comparison, JUDGE_ENDPOINT, JUDGE_API_KEY, JUDGE_MODEL

# Table 2的三个变种方法
ABLATION_METHODS = [
    'TASA-woForgetting-llama',
    'TASA-woMemory-llama', 
    'TASA-woPersona-llama'
]

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
FS_METHODS = ['dkt']  # 使用dkt作为代表

def main():
    print("="*80)
    print("📊 Table 2: TASA消融实验评估")
    print("   Baseline: TASA (GPT，作为TASA-llama的proxy)")
    print("="*80)
    print()
    
    results = []
    
    for method in ABLATION_METHODS:
        print(f"\n{'='*80}")
        print(f"🔬 评估方法: {method}")
        print(f"{'='*80}\n")
        
        for dataset in DATASETS:
            print(f"\n{'='*80}")
            print(f"📂 数据集: {dataset}")
            print(f"{'='*80}\n")
            
            # 使用TASA作为baseline
            result = batch_judge(
                target_method=method,
                dataset=dataset,
                max_workers=20,
                baseline_method='TASA'
            )
            
            if result:
                results.append({
                    'method': method,
                    'dataset': dataset,
                    'win_rate': result.get('win_rate', 0),
                    'tie_rate': result.get('tie_rate', 0),
                    'common_students': result.get('common_students', 0)
                })
                print(f"✅ {method} vs TASA ({dataset}): Win Rate = {result.get('win_rate', 0):.1f}%")
            else:
                print(f"⚠️  {method} ({dataset}): 无可比较的数据")
    
    # 打印汇总表格
    print("\n\n" + "="*80)
    print("📊 Table 2 汇总结果")
    print("="*80)
    print(f"{'Method':<30} | {'assist2017':>12} | {'algebra2005':>12} | {'bridge2006':>12} | {'nips_task34':>12}")
    print("-"*80)
    
    for method in ABLATION_METHODS:
        method_results = [r for r in results if r['method'] == method]
        row = f"{method:<30} |"
        
        for dataset in DATASETS:
            dataset_result = next((r for r in method_results if r['dataset'] == dataset), None)
            if dataset_result:
                win_rate = dataset_result['win_rate']
                row += f" {win_rate:>10.1f}% |"
            else:
                row += f" {'N/A':>11} |"
        
        print(row)
    
    print("="*80)
    print(f"\n✅ Table 2评估完成！共完成 {len(results)} 个评估任务")
    print(f"   结果保存在: /mnt/localssd/llm_judge_results/\n")

if __name__ == '__main__':
    main()

