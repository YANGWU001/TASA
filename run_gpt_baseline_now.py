#!/usr/bin/env python3
"""
运行GPT Baseline评估（max_workers=10）
"""
import subprocess
import os
import time

DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 10
BACKBONE = 'gpt'
BACKBONE_SUFFIX = '-gpt'

def run_baseline(dataset, method):
    """运行单个baseline评估"""
    print(f"\n{'='*80}")
    print(f"🚀 Running {method} on {dataset} (GPT, max_workers={MAX_WORKERS})")
    print(f"{'='*80}\n")
    
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    log_file = f'/mnt/localssd/logs/baseline_{method}_{BACKBONE_SUFFIX}_{dataset}.log'
    
    # 设置环境变量
    env = os.environ.copy()
    env['TASA_CONFIG'] = 'tasa_config_gpt'
    
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/baseline_evaluation_conservative.py',
        '--method', method,
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', str(MAX_WORKERS),
        f'--backbone-suffix={BACKBONE_SUFFIX}'
    ]
    
    with open(log_file, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
    
    if result.returncode == 0:
        print(f"✅ {method} on {dataset} completed")
        return True
    else:
        print(f"❌ {method} on {dataset} failed")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          🚀 GPT Baseline评估 (max_workers=10)                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 配置:")
    print(f"  • Datasets: {len(DATASETS)} 个")
    print(f"  • Methods: {len(METHODS)} 个")
    print(f"  • Total tasks: {len(DATASETS) * len(METHODS)} 个")
    print(f"  • Max workers per task: {MAX_WORKERS}")
    print(f"  • 预计时间: ~2-2.5小时")
    print(f"\n{'='*80}\n")
    
    start_time = time.time()
    completed = 0
    failed = 0
    
    for dataset in DATASETS:
        for method in METHODS:
            if run_baseline(dataset, method):
                completed += 1
            else:
                failed += 1
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"📊 GPT Baseline评估完成")
    print(f"{'='*80}")
    print(f"✅ 完成: {completed}/{len(DATASETS) * len(METHODS)}")
    print(f"❌ 失败: {failed}")
    print(f"⏱️  总耗时: {elapsed/3600:.2f} 小时")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
