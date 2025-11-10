"""
在所有数据集上运行所有baseline方法（保守版本）
使用2次post-test的平均值，包含负数learning gain
"""

import os
import subprocess
import json
import time
from datetime import datetime

# 配置
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 20

def get_student_count(dataset):
    """获取数据集的学生数"""
    student_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
    if os.path.exists(student_file):
        with open(student_file) as f:
            data = json.load(f)
        return data['filtered_count']
    return 0

def run_single_evaluation(method, dataset, max_workers):
    """运行单个评估"""
    print(f"\n{'#'*80}")
    print(f"# {method} on {dataset}")
    print(f"{'#'*80}\n")
    
    student_count = get_student_count(dataset)
    
    print(f"{'='*80}")
    print(f"📊 {method} on {dataset} (保守版本)")
    print(f"{'='*80}")
    print(f"  学生数: {student_count}")
    print(f"  并行度: {max_workers}")
    print(f"  策略: 2次post-test取平均，包含负数gain")
    
    # 预估时间
    estimated_time = (student_count * 6.5) / max_workers  # 每学生约6.5分钟
    print(f"  预计时间: {estimated_time:.0f}分钟 ({estimated_time/60:.1f}小时)")
    
    # 运行评估
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_conservative.py --method {method} --dataset {dataset} --max-workers {max_workers}"
    
    log_file = f'/mnt/localssd/logs/{method}-conservative_{dataset}.log'
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
        overall_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                overall = json.load(f)
            
            print(f"\n📊 结果:")
            print(f"   学生数: {overall['num_students']}")
            print(f"   策略1 (平均): {overall['strategy_avg']['avg_learning_gain']*100:.1f}% ± {overall['strategy_avg']['std_learning_gain']*100:.1f}%")
            print(f"   策略2 (最低): {overall['strategy_min']['avg_learning_gain']*100:.1f}% ± {overall['strategy_min']['std_learning_gain']*100:.1f}%")
            print(f"   正/负 (平均): {overall['strategy_avg']['num_positive_gain']}/{overall['strategy_avg']['num_negative_gain']}")
            print(f"   正/负 (最低): {overall['strategy_min']['num_positive_gain']}/{overall['strategy_min']['num_negative_gain']}")
        
        return True
    else:
        print(f"❌ {method} on {dataset} 失败")
        print(f"   查看日志: {log_file}")
        return False

def main():
    print("="*80)
    print("🚀 运行所有Baselines评估 (保守版本)")
    print("="*80)
    print(f"方法: {', '.join(METHODS)}")
    print(f"数据集: {', '.join(DATASETS)}")
    print(f"并行度: {MAX_WORKERS} workers")
    print(f"策略: 2次post-test取平均，包含负数gain")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示学生数
    print(f"\n学生数统计:")
    total_students = 0
    for dataset in DATASETS:
        count = get_student_count(dataset)
        total_students += count
        print(f"  {dataset}: {count}个")
    print(f"  总计: {total_students}个")
    
    # 预估总时间
    total_evaluations = len(METHODS) * len(DATASETS)
    avg_time_per_eval = 2.0  # 小时
    total_time = total_evaluations * avg_time_per_eval
    print(f"\n预计总时间: {total_time:.1f}小时 ({total_evaluations}个评估 × {avg_time_per_eval}小时)")
    
    overall_start = time.time()
    results = {}
    
    # 对每个方法和数据集的组合进行评估
    task_idx = 0
    
    for method in METHODS:
        for dataset in DATASETS:
            task_idx += 1
            
            print(f"\n\n{'='*80}")
            print(f"任务进度: {task_idx}/{total_evaluations}")
            print(f"{'='*80}")
            
            key = f"{method}_{dataset}"
            success = run_single_evaluation(method, dataset, MAX_WORKERS)
            results[key] = success
            
            if not success:
                print(f"\n⚠️  {key} 失败，继续下一个任务")
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 所有Baselines评估总结 (保守版本)")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n结果汇总:")
    print(f"{'方法':<15s} {'数据集':<15s} {'学生数':<8s} {'平均Gain(平均)':<18s} {'平均Gain(最低)':<18s} {'正/负(平均)':<12s} {'正/负(最低)'}")
    print("-"*120)
    
    for method in METHODS:
        for dataset in DATASETS:
            key = f"{method}_{dataset}"
            status = "✅" if results.get(key) else "❌"
            
            # 读取结果
            overall_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file) as f:
                    data = json.load(f)
                num = data['num_students']
                gain_avg_str = f"{data['strategy_avg']['avg_learning_gain']*100:.1f}%±{data['strategy_avg']['std_learning_gain']*100:.1f}%"
                gain_min_str = f"{data['strategy_min']['avg_learning_gain']*100:.1f}%±{data['strategy_min']['std_learning_gain']*100:.1f}%"
                pos_neg_avg = f"{data['strategy_avg']['num_positive_gain']}/{data['strategy_avg']['num_negative_gain']}"
                pos_neg_min = f"{data['strategy_min']['num_positive_gain']}/{data['strategy_min']['num_negative_gain']}"
                print(f"{method:<15s} {dataset:<15s} {num:<8d} {gain_avg_str:<18s} {gain_min_str:<18s} {pos_neg_avg:<12s} {pos_neg_min}")
            else:
                print(f"{method:<15s} {dataset:<15s} {'N/A':<8s} {'N/A':<18s} {'N/A':<18s} {'N/A':<12s} {'N/A'}")
    
    print(f"\n{'='*80}")
    print("✅ 所有Baselines评估完成！")
    print(f"{'='*80}")
    
    # 保存总结
    summary_file = '/mnt/localssd/baselines_conservative_summary.json'
    summary = {
        'version': 'conservative',
        'strategy': '2次post-test取平均，包含所有learning gain（含负数）',
        'methods': METHODS,
        'datasets': DATASETS,
        'max_workers': MAX_WORKERS,
        'start_time': datetime.now().isoformat(),
        'total_time_minutes': overall_time / 60,
        'results': results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 总结已保存: {summary_file}")

if __name__ == "__main__":
    main()

