#!/usr/bin/env python3
"""
Table 2: 直接对三个TASA变种进行LLM as Judge评估
Baseline: TASA (GPT)
"""

import sys
sys.path.append('/mnt/localssd')

from llm_as_judge_personalization import batch_judge

# 三个变种方法
VARIANTS = [
    'TASA-woForgetting-llama',
    'TASA-woMemory-llama',
    'TASA-woPersona-llama'
]

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']

def main():
    print("="*80)
    print("📊 Table 2: TASA消融实验")
    print("   变种 vs TASA (GPT作为baseline)")
    print("="*80)
    print()
    
    all_results = {}
    
    for variant in VARIANTS:
        print(f"\n{'='*80}")
        print(f"🔬 评估变种: {variant}")
        print(f"{'='*80}\n")
        
        variant_results = {}
        
        for dataset in DATASETS:
            print(f"\n📂 数据集: {dataset}")
            print("-"*80)
            
            result = batch_judge(
                target_method=variant,
                dataset=dataset,
                max_workers=20,
                baseline_method='TASA'
            )
            
            if result:
                win_rate = result.get('win_rate', 0)
                tie_rate = result.get('tie_rate', 0)
                common_students = result.get('common_students', 0)
                
                variant_results[dataset] = {
                    'win_rate': win_rate,
                    'tie_rate': tie_rate,
                    'common_students': common_students
                }
                
                print(f"✅ {dataset}: Win={win_rate:.1f}%, Tie={tie_rate:.1f}%, Students={common_students}")
            else:
                variant_results[dataset] = None
                print(f"⚠️  {dataset}: 无可比较数据")
        
        all_results[variant] = variant_results
    
    # 打印Table 2汇总
    print("\n\n" + "="*80)
    print("📊 TABLE 2: TASA消融实验结果汇总")
    print("="*80)
    print()
    print(f"{'Variant Method':<35} | {'assist2017':>11} | {'algebra2005':>11} | {'bridge2006':>11} | {'nips_task34':>11}")
    print("-"*80)
    
    for variant in VARIANTS:
        row = f"{variant:<35} |"
        for dataset in DATASETS:
            result = all_results[variant].get(dataset)
            if result:
                win_rate = result['win_rate']
                row += f" {win_rate:>9.1f}% |"
            else:
                row += f" {'N/A':>10} |"
        print(row)
    
    print("="*80)
    print("\n说明:")
    print("  - Baseline: TASA (GPT-OSS-120b)")
    print("  - Win Rate: 变种方法在个性化教学质量上优于TASA的比例")
    print("  - 预期: 变种的Win Rate应该低于TASA (因为移除了某些模块)")
    print()
    print("✅ Table 2评估完成！")
    print()

if __name__ == '__main__':
    main()

