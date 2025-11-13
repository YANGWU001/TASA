#!/usr/bin/env python3
"""
LLM as Judge: 仅评估TASA-llama系列方法
"""

import sys
import os

# 导入主评估模块的函数
sys.path.insert(0, '/mnt/localssd')
from llm_as_judge_personalization import batch_judge, safe_print

def main():
    """仅评估TASA-llama系列方法"""
    
    # 只评估TASA-llama相关方法
    TARGET_METHODS = [
        'TASA-llama',  # llama主方法
        'TASA-woForgetting-llama',  # 消融实验
        'TASA-woMemory-llama',
        'TASA-woPersona-llama',
        'TASA-lambda0.5-llama',  # lambda参数
        'TASA-lambda0.5-gpt',
        'TASA-lambda0.5-qwen',
    ]
    
    DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          🎯 LLM as Judge: TASA Methods Evaluation (Supplementary)          ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("📋 配置:")
    print(f"  • Target Methods: {len(TARGET_METHODS)}")
    print(f"  • Datasets: {', '.join(DATASETS)}")
    print(f"  • Max Workers: 20")
    print()
    print("="*80)
    
    all_summaries = []
    
    for dataset in DATASETS:
        print(f"\n{'#'*80}")
        print(f"## Dataset: {dataset}")
        print(f"{'#'*80}\n")
        
        for method in TARGET_METHODS:
            # 检查该method在该dataset上是否有dialogue
            method_dir = f'/mnt/localssd/bank/dialogue/{method}/{dataset}'
            if not os.path.exists(method_dir):
                safe_print(f"⏭️  跳过{method}（{dataset}无数据）\n")
                continue
            
            # 检查是否已经评估过
            backbone_suffix = ''
            if '-llama' in method:
                baseline_method = 'Vanilla-ICL-llama'
                backbone = 'llama'
            elif '-qwen' in method:
                baseline_method = 'Vanilla-ICL-qwen'
                backbone = 'qwen'
            else:
                baseline_method = 'Vanilla-ICL'
                backbone = 'gpt'
            
            result_file = f'/mnt/localssd/llm_judge_results/{method}_vs_{baseline_method}_{dataset}.json'
            if os.path.exists(result_file):
                safe_print(f"✅ 跳过{method}（{dataset}已评估）\n")
                continue
            
            summary = batch_judge(method, dataset, max_workers=20)
            if summary:
                all_summaries.append(summary)
    
    # 生成总体报告
    print("\n" + "="*100)
    print("📊 TASA系列评估完成汇总")
    print("="*100)
    
    if all_summaries:
        print(f"\n{'Method':<40} {'Dataset':<15} {'Win Rate':<12} {'Record':<20}")
        print('-'*87)
        for s in all_summaries:
            wr_str = f"{s['win_rate']*100:.1f}%"
            record = f"{s['target_wins']}W-{s['ties']}T-{s['baseline_wins']}L ({s['total_comparisons']})"
            print(f"{s['target_method']:<40} {s['dataset']:<15} {wr_str:<12} {record:<20}")
    else:
        print("所有TASA方法均已评估完成！")
    
    print("\n" + "="*100)
    print("✅ TASA系列评估完成！")
    print(f"📁 结果保存在: /mnt/localssd/llm_judge_results/")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()

