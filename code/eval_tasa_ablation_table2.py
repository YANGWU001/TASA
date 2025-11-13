#!/usr/bin/env python3
"""
Table 2消融实验：TASA变体 vs TASA (gpt作为baseline)
"""
import sys
sys.path.insert(0, '/mnt/localssd')
from llm_as_judge_personalization import batch_judge

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']

# 变体方法（与TASA (gpt)比较）
ABLATION_METHODS = [
    'TASA-woForgetting-llama',
    'TASA-woMemory-llama',
    'TASA-woPersona-llama',
]

print('='*80)
print('📊 Table 2: TASA消融实验')
print('='*80)
print(f'变体方法: {len(ABLATION_METHODS)}')
print(f'Datasets: {DATASETS}')
print(f'Baseline: TASA (gpt)')
print('='*80)

for method in ABLATION_METHODS:
    for dataset in DATASETS:
        print(f'\n🔄 {method} vs TASA ({dataset})')
        batch_judge(
            target_method=method,
            baseline_method='TASA',
            dataset=dataset,
            max_workers=20
        )
        print(f'✅ 完成\n')

print('='*80)
print('✅ 所有Table 2评估完成！')
print('='*80)

