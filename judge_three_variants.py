#!/usr/bin/env python3
"""
专门评估TASA三个变种 vs TASA (GPT作为proxy)
"""
import sys
sys.path.append('/mnt/localssd')

from llm_as_judge_personalization import batch_judge

VARIANTS = [
    'TASA-woForgetting-llama',
    'TASA-woMemory-llama', 
    'TASA-woPersona-llama'
]

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']

def main():
    print("="*80)
    print("📊 Table 2: 评估三个TASA变种")
    print("   Baseline: Vanilla-ICL-llama")
    print("="*80)
    
    all_results = []
    
    for variant in VARIANTS:
        print(f"\n{'='*80}")
        print(f"🔬 变种: {variant}")
        print(f"{'='*80}\n")
        
        for dataset in DATASETS:
            result = batch_judge(
                target_method=variant,
                dataset=dataset,
                max_workers=20,
                baseline_method='Vanilla-ICL-llama'
            )
            
            if result:
                all_results.append({
                    'variant': variant,
                    'dataset': dataset,
                    'win_rate': result.get('win_rate', 0),
                    'tie_rate': result.get('tie_rate', 0),
                    'loss_rate': 100 - result.get('win_rate', 0) - result.get('tie_rate', 0),
                    'students': result.get('common_students', 0)
                })
    
    # 打印Table 2
    print("\n\n" + "="*100)
    print("📊 Table 2: TASA消融实验结果（Win Rate %）")
    print("="*100)
    print(f"{'Variant':<30} | {'assist2017':>12} | {'algebra2005':>12} | {'bridge2006':>12} | {'nips_task34':>12}")
    print("-"*100)
    
    for variant in VARIANTS:
        variant_short = variant.replace('TASA-', '').replace('-llama', '')
        row = f"{variant_short:<30} |"
        
        for dataset in DATASETS:
            result = next((r for r in all_results if r['variant'] == variant and r['dataset'] == dataset), None)
            if result:
                win_rate = result['win_rate']
                row += f" {win_rate:>10.1f}% |"
            else:
                row += f" {'N/A':>11} |"
        
        print(row)
    
    print("="*100)
    print(f"\n✅ 评估完成！共 {len(all_results)} 个任务\n")
    
    # 详细结果
    print("\n" + "="*100)
    print("📋 详细结果")
    print("="*100)
    for result in all_results:
        print(f"{result['variant']:<30} | {result['dataset']:<15} | "
              f"Win: {result['win_rate']:>5.1f}%  Tie: {result['tie_rate']:>5.1f}%  "
              f"Loss: {result['loss_rate']:>5.1f}%  (n={result['students']})")
    print("="*100)

if __name__ == '__main__':
    main()

