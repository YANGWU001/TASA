#!/usr/bin/env python3
"""
TASA Ablation Study - Llama Backbone
测试3个变体 × 4个数据集 = 12个实验
"""

import json
import os
import sys
import time
import subprocess

# Ablation变体配置
ABLATIONS = ['woPersona', 'woMemory', 'woForgetting']
DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
MAX_WORKERS = 10
FORGETTING_METHOD = 'dkt'  # 使用DKT，没有则fallback到simplekt

# 完整版结果（作为参考）
FULL_VERSION_RESULTS = {
    'assist2017': 67.4,
    'nips_task34': 52.4,
    'algebra2005': 62.6,
    'bridge2006': 53.9
}

def run_ablation_experiment(ablation_type, dataset):
    """
    运行单个ablation实验
    
    Args:
        ablation_type: 'woPersona', 'woMemory', 'woForgetting'
        dataset: 数据集名称
    """
    print(f"\n{'='*80}")
    print(f"🔬 Running TASA Ablation: w/o {ablation_type[2:]}")
    print(f"   Dataset: {dataset}")
    print(f"   Forgetting Method: {FORGETTING_METHOD}")
    print(f"{'='*80}\n")
    
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    log_file = f'/mnt/localssd/logs/ablation_TASA-{ablation_type}-llama_{dataset}_{FORGETTING_METHOD}.log'
    
    # 检查students文件
    if not os.path.exists(students_file):
        students_file_alt = f'/mnt/localssd/qualified_students_{dataset}.json'
        if os.path.exists(students_file_alt):
            students_file = students_file_alt
        else:
            print(f"❌ No valid students file found for {dataset}")
            return False
    
    # 设置环境变量
    env = os.environ.copy()
    env['TASA_CONFIG'] = 'tasa_config_llama'
    env['TASA_ABLATION'] = ablation_type  # 标记ablation类型
    
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/run_tasa_ablation_batch.py',
        '--ablation', ablation_type,
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', str(MAX_WORKERS),
        '--forgetting-method', FORGETTING_METHOD
    ]
    
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
        
        if result.returncode == 0:
            print(f"✅ TASA-{ablation_type} on {dataset} completed")
            return True
        else:
            print(f"❌ TASA-{ablation_type} on {dataset} failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ TASA-{ablation_type} on {dataset} exception: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║              🔬 TASA Ablation Study - Llama Backbone                        ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 配置:")
    print(f"  • Ablations: {', '.join([f'w/o {a[2:]}' for a in ABLATIONS])}")
    print(f"  • Datasets: {', '.join(DATASETS)}")
    print(f"  • Total experiments: {len(ABLATIONS)} × {len(DATASETS)} = {len(ABLATIONS) * len(DATASETS)}")
    print(f"  • Max workers: {MAX_WORKERS}")
    print(f"  • Forgetting method: {FORGETTING_METHOD}")
    print(f"  • Backbone: Llama-3.1-8B")
    print(f"\n📈 完整版TASA结果（参考）:")
    for ds, gain in FULL_VERSION_RESULTS.items():
        print(f"  • {ds}: {gain}%")
    print(f"\n⏱️  预计总时间: ~2-3小时")
    print(f"\n{'='*80}\n")
    
    start_time = time.time()
    results = {}
    
    # Ablation在最外层循环
    for ablation in ABLATIONS:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  🔬 ABLATION: w/o {ablation[2:]:^62} ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        ablation_start = time.time()
        results[ablation] = {}
        
        for dataset in DATASETS:
            success = run_ablation_experiment(ablation, dataset)
            results[ablation][dataset] = 'Success' if success else 'Failed'
        
        ablation_elapsed = time.time() - ablation_start
        print(f"\n{'─'*80}")
        print(f"📊 w/o {ablation[2:]} 完成所有数据集")
        print(f"   耗时: {ablation_elapsed/60:.1f} 分钟")
        print(f"{'─'*80}\n")
    
    total_elapsed = time.time() - start_time
    
    # 打印汇总
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║                       📊 Ablation Study完成汇总                             ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    print("结果矩阵 (Ablation × Dataset):\n")
    print(f"{'Ablation':<20} | {' | '.join([f'{d:^13}' for d in DATASETS])}")
    print(f"{'-'*20}-+-{'-+-'.join(['-'*13]*len(DATASETS))}")
    
    for ablation in ABLATIONS:
        status_symbols = []
        for dataset in DATASETS:
            if results[ablation][dataset] == 'Success':
                status_symbols.append('✅ Success')
            else:
                status_symbols.append('❌ Failed')
        print(f"{'w/o '+ablation[2:]:<20} | {' | '.join([f'{s:^13}' for s in status_symbols])}")
    
    # 统计
    total_experiments = len(ABLATIONS) * len(DATASETS)
    successful = sum(1 for a in ABLATIONS for d in DATASETS if results[a][d] == 'Success')
    failed = total_experiments - successful
    
    print(f"\n{'='*80}")
    print(f"✅ 成功: {successful}/{total_experiments}")
    print(f"❌ 失败: {failed}/{total_experiments}")
    print(f"⏱️  总耗时: {total_elapsed/3600:.2f} 小时 ({total_elapsed/60:.1f} 分钟)")
    print(f"{'='*80}\n")
    
    # 保存结果
    results_file = '/mnt/localssd/logs/ablation_study_llama_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'ablations': ABLATIONS,
            'datasets': DATASETS,
            'forgetting_method': FORGETTING_METHOD,
            'backbone': 'Llama-3.1-8B',
            'full_version_results': FULL_VERSION_RESULTS,
            'results': results,
            'summary': {
                'total': total_experiments,
                'successful': successful,
                'failed': failed,
                'elapsed_hours': total_elapsed/3600
            }
        }, f, indent=2)
    print(f"📄 结果已保存至: {results_file}\n")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

