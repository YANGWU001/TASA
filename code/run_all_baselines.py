"""
在所有数据集上运行所有baseline方法
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime

def run_baseline_on_dataset(method, dataset, max_workers=10):
    """对单个数据集运行baseline评估"""
    print(f"\n\n{'#'*80}")
    print(f"# {method} on {dataset}")
    print(f"{'#'*80}\n")
    
    # 检查学生列表
    student_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
    
    if not os.path.exists(student_file):
        print(f"❌ 学生列表不存在: {student_file}")
        return False
    
    with open(student_file) as f:
        data = json.load(f)
    
    num_students = data['filtered_count']
    
    print(f"{'='*80}")
    print(f"📊 {method} on {dataset}")
    print(f"{'='*80}")
    print(f"  学生数: {num_students}")
    print(f"  并行度: {max_workers}")
    
    # 预估时间
    estimated_time = (num_students * 6.5) / max_workers
    print(f"  预计时间: {estimated_time:.0f}分钟")
    
    # 运行评估
    cmd = f"/opt/venv/bin/python3 /mnt/localssd/evaluate_baselines.py --method {method} --dataset {dataset} --max-workers {max_workers}"
    
    log_file = f'/mnt/localssd/logs/{method}_{dataset}.log'
    print(f"  日志文件: {log_file}")
    
    print(f"\n{'='*80}")
    print(f"🚀 开始评估")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    with open(log_file, 'w') as log:
        result = subprocess.run(cmd, shell=True, stdout=log, stderr=subprocess.STDOUT)
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  实际用时: {elapsed/60:.1f}分钟")
    
    if result.returncode == 0:
        print(f"✅ {method} on {dataset} 完成")
        
        # 读取结果
        overall_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                overall = json.load(f)
            
            print(f"\n📊 结果:")
            print(f"   学生数: {overall['num_students']}")
            print(f"   平均Gain: {overall['overall']['avg_learning_gain']*100:.1f}%")
            print(f"   中位数: {overall['overall']['median_learning_gain']*100:.1f}%")
        
        return True
    else:
        print(f"❌ {method} on {dataset} 失败")
        print(f"   查看日志: {log_file}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='运行所有baseline评估')
    parser.add_argument('--methods', nargs='+',
                       default=['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV'],
                       choices=['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV'],
                       help='要评估的方法列表')
    parser.add_argument('--datasets', nargs='+',
                       default=['assist2017', 'algebra2005', 'bridge2006'],
                       help='要评估的数据集列表')
    parser.add_argument('--max-workers', type=int, default=10,
                       help='每个评估的并行度')
    
    args = parser.parse_args()
    
    methods = args.methods
    datasets = args.datasets
    
    print("="*80)
    print("🚀 运行所有Baseline评估")
    print("="*80)
    print(f"方法: {', '.join(methods)}")
    print(f"数据集: {', '.join(datasets)}")
    print(f"并行度: {args.max_workers} workers per task")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = time.time()
    results = {}
    
    # 对每个方法和数据集的组合进行评估
    total_tasks = len(methods) * len(datasets)
    task_idx = 0
    
    for method in methods:
        for dataset in datasets:
            task_idx += 1
            
            print(f"\n\n{'='*80}")
            print(f"任务进度: {task_idx}/{total_tasks}")
            print(f"{'='*80}")
            
            key = f"{method}_{dataset}"
            success = run_baseline_on_dataset(method, dataset, args.max_workers)
            results[key] = success
            
            if not success:
                print(f"\n⚠️  {key} 失败，继续下一个任务")
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 所有Baseline评估总结")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n结果汇总:")
    print(f"{'方法':<15s} {'数据集':<15s} {'状态':<10s} {'平均Gain'}")
    print("-"*80)
    
    for method in methods:
        for dataset in datasets:
            key = f"{method}_{dataset}"
            status = "✅ 成功" if results.get(key) else "❌ 失败"
            
            # 读取结果
            overall_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file) as f:
                    data = json.load(f)
                gain_str = f"{data['overall']['avg_learning_gain']*100:.1f}%"
            else:
                gain_str = "N/A"
            
            print(f"{method:<15s} {dataset:<15s} {status:<10s} {gain_str}")
    
    print(f"\n{'='*80}")
    print("✅ 所有Baseline评估完成！")
    print(f"{'='*80}")
    
    # 保存总结
    summary_file = '/mnt/localssd/baselines_summary.json'
    summary = {
        'methods': methods,
        'datasets': datasets,
        'start_time': datetime.now().isoformat(),
        'total_time_minutes': overall_time / 60,
        'results': results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 总结已保存: {summary_file}")

if __name__ == "__main__":
    main()

