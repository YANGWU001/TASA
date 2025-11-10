#!/usr/bin/env python3
"""
运行所有Llama Baseline评估
- Baseline放在最外层循环
- Dataset在内层循环
- max_workers=10
"""
import subprocess
import os
import time
import sys

# 配置
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
MAX_WORKERS = 10
BACKBONE_SUFFIX = '-llama'

def run_baseline(method, dataset):
    """运行单个baseline评估"""
    print(f"\n{'='*80}")
    print(f"🚀 Running {method} on {dataset}")
    print(f"{'='*80}\n")
    
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    log_file = f'/mnt/localssd/logs/baseline_{method}_{BACKBONE_SUFFIX}_{dataset}.log'
    
    # 检查students文件是否存在
    if not os.path.exists(students_file):
        print(f"⚠️  Students file not found: {students_file}")
        # 尝试不带sampled10的版本
        students_file_alt = f'/mnt/localssd/qualified_students_{dataset}.json'
        if os.path.exists(students_file_alt):
            print(f"   使用: {students_file_alt}")
            students_file = students_file_alt
        else:
            print(f"❌ No valid students file found")
            return False
    
    # 设置环境变量
    env = os.environ.copy()
    env['TASA_CONFIG'] = 'tasa_config_llama'
    
    cmd = [
        '/opt/venv/bin/python3',
        '/mnt/localssd/baseline_evaluation_conservative.py',
        '--method', method,
        '--dataset', dataset,
        '--students-file', students_file,
        '--max-workers', str(MAX_WORKERS),
        f'--backbone-suffix={BACKBONE_SUFFIX}'
    ]
    
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
        
        if result.returncode == 0:
            print(f"✅ {method} on {dataset} completed")
            return True
        else:
            print(f"❌ {method} on {dataset} failed (exit code: {result.returncode})")
            # 打印最后几行日志
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    print("最后10行日志:")
                    print("".join(lines[-10:]))
            except:
                pass
            return False
    except Exception as e:
        print(f"❌ {method} on {dataset} exception: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          🚀 Llama Baseline评估 - 所有方法和数据集                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 配置:")
    print(f"  • Methods: {', '.join(METHODS)}")
    print(f"  • Datasets: {', '.join(DATASETS)}")
    print(f"  • Total tasks: {len(METHODS)} methods × {len(DATASETS)} datasets = {len(METHODS) * len(DATASETS)} tasks")
    print(f"  • Max workers per task: {MAX_WORKERS}")
    print(f"  • Loop structure: Method (outer) -> Dataset (inner)")
    print(f"\n⏱️  预计总时间: ~4-6小时")
    print(f"\n{'='*80}\n")
    
    start_time = time.time()
    results = {}
    
    # Baseline在最外层循环，Dataset在内层
    for method in METHODS:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  📋 METHOD: {method:^66} ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        method_start = time.time()
        results[method] = {}
        
        for dataset in DATASETS:
            success = run_baseline(method, dataset)
            results[method][dataset] = 'Success' if success else 'Failed'
        
        method_elapsed = time.time() - method_start
        print(f"\n{'─'*80}")
        print(f"📊 {method} 完成所有数据集")
        print(f"   耗时: {method_elapsed/60:.1f} 分钟")
        print(f"{'─'*80}\n")
    
    total_elapsed = time.time() - start_time
    
    # 打印汇总
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║                           📊 评估完成汇总                                   ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    print("结果矩阵 (Method × Dataset):\n")
    print(f"{'Method':<15} | {' | '.join([f'{d:^13}' for d in DATASETS])}")
    print(f"{'-'*15}-+-{'-+-'.join(['-'*13]*len(DATASETS))}")
    
    for method in METHODS:
        status_symbols = []
        for dataset in DATASETS:
            if results[method][dataset] == 'Success':
                status_symbols.append('✅ Success')
            else:
                status_symbols.append('❌ Failed')
        print(f"{method:<15} | {' | '.join([f'{s:^13}' for s in status_symbols])}")
    
    # 统计
    total_tasks = len(METHODS) * len(DATASETS)
    successful = sum(1 for m in METHODS for d in DATASETS if results[m][d] == 'Success')
    failed = total_tasks - successful
    
    print(f"\n{'='*80}")
    print(f"✅ 成功: {successful}/{total_tasks}")
    print(f"❌ 失败: {failed}/{total_tasks}")
    print(f"⏱️  总耗时: {total_elapsed/3600:.2f} 小时 ({total_elapsed/60:.1f} 分钟)")
    print(f"{'='*80}\n")
    
    # 保存结果
    results_file = '/mnt/localssd/logs/baseline_llama_all_results.json'
    import json
    with open(results_file, 'w') as f:
        json.dump({
            'methods': METHODS,
            'datasets': DATASETS,
            'results': results,
            'summary': {
                'total': total_tasks,
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

