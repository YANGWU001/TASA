#!/usr/bin/env python3
"""
LLM as Judge: 评估TASA-llama系列方法（仅assist2017数据集）
"""

import sys
import os

# 导入主评估模块的函数
sys.path.insert(0, '/mnt/localssd')
from llm_as_judge_personalization import batch_judge, safe_print

def main():
    """仅评估TASA-llama系列方法在assist2017上"""
    
    # 只评估TASA-llama相关方法
    TARGET_METHODS = [
        'TASA-llama',  # llama主方法
        'TASA-woForgetting-llama',  # 消融实验
        'TASA-woMemory-llama',
        'TASA-woPersona-llama',
    ]
    
    DATASETS = ['assist2017']  # 只评估assist2017
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║     🎯 LLM as Judge: TASA-llama Methods (assist2017 only)                 ║")
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
            result_file = f'/mnt/localssd/llm_judge_results/{method}_vs_Vanilla-ICL-llama_{dataset}.json'
            if os.path.exists(result_file):
                safe_print(f"✅ 跳过{method}（{dataset}已评估）\n")
                continue
            
            summary = batch_judge(method, dataset, max_workers=20)
            if summary:
                all_summaries.append(summary)
    
    # 生成总体报告
    print("\n" + "="*100)
    print("📊 TASA-llama系列评估完成汇总（assist2017）")
    print("="*100)
    
    if all_summaries:
        print(f"\n{'Method':<40} {'Dataset':<15} {'Win Rate':<12} {'Record':<25} {'Avg Scores':<15}")
        print('-'*107)
        for s in all_summaries:
            wr_str = f"{s['win_rate']*100:.1f}%"
            record = f"{s['target_wins']}W-{s['ties']}T-{s['baseline_wins']}L ({s['total_comparisons']})"
            scores = f"{s.get('avg_score_target', 0):.2f}/{s.get('avg_score_baseline', 0):.2f}"
            print(f"{s['target_method']:<40} {s['dataset']:<15} {wr_str:<12} {record:<25} {scores:<15}")
    else:
        print("所有方法均已评估或无数据！")
    
    print("\n" + "="*100)
    print("✅ 评估完成！")
    print(f"📁 结果保存在: /mnt/localssd/llm_judge_results/")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()

