"""
主评估脚本 - 运行所有评估任务
包括：
1. TASA-best-of-2: nips_task34
2. Baselines-conservative (4方法 × 4数据集): 16个任务
"""

import os
import subprocess
import json
import time
from datetime import datetime

# 配置
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 20  # 并行度设置

# nips_task34使用150个采样学生
NIPS_SAMPLED_FILE = '/mnt/localssd/qualified_students_nips_task34_150sampled.json'

def get_student_count(dataset):
    """获取数据集的学生数"""
    # nips_task34使用150个采样学生
    if dataset == 'nips_task34':
        student_file = NIPS_SAMPLED_FILE
        key = 'sampled_count'
    else:
        student_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
        key = 'filtered_count'
    
    if os.path.exists(student_file):
        with open(student_file) as f:
            data = json.load(f)
        return data[key]
    return 0

def run_tasa_nips34():
    """运行TASA评估在nips_task34上"""
    print(f"\n{'#'*80}")
    print(f"# 任务 1/17: TASA-best-of-2 on nips_task34")
    print(f"{'#'*80}\n")
    
    student_count = get_student_count('nips_task34')
    
    print(f"{'='*80}")
    print(f"📊 TASA-best-of-2 on nips_task34")
    print(f"{'='*80}")
    print(f"  学生数: {student_count}")
    print(f"  并行度: {MAX_WORKERS}")
    print(f"  策略: 2次post-test取最高分，排除负数gain")
    
    # 预估时间
    estimated_time = (student_count * 6.5) / MAX_WORKERS
    print(f"  预计时间: {estimated_time:.0f}分钟 ({estimated_time/60:.1f}小时)")
    
    # 运行评估 (使用150个采样学生)
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/run_tasa_batch_best_of_two.py --dataset nips_task34 --students-file {NIPS_SAMPLED_FILE} --all --max-workers {MAX_WORKERS}"
    
    log_file = '/mnt/localssd/logs/TASA_nips_task34.log'
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
        print(f"✅ TASA on nips_task34 完成")
        
        # 读取结果
        overall_file = f'/mnt/localssd/bank/evaluation_results/TASA-best-of-2/nips_task34/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                overall = json.load(f)
            
            print(f"\n📊 结果:")
            print(f"   学生数: {overall['num_students']}")
            print(f"   平均Learning Gain (best): {overall['overall']['avg_learning_gain']*100:.1f}% ± {overall['overall']['std_learning_gain']*100:.1f}%")
            print(f"   正增长: {overall.get('num_positive_gain', 'N/A')}个")
            print(f"   负增长: {overall.get('num_negative_gain', 0)}个")
        
        return True
    else:
        print(f"❌ TASA on nips_task34 失败")
        print(f"   查看日志: {log_file}")
        return False

def run_baseline_evaluation(method, dataset, task_num):
    """运行单个baseline评估"""
    print(f"\n{'#'*80}")
    print(f"# 任务 {task_num}/17: {method} on {dataset}")
    print(f"{'#'*80}\n")
    
    student_count = get_student_count(dataset)
    
    # 对nips_task34显示采样信息
    if dataset == 'nips_task34':
        note = " (150个采样学生)"
    else:
        note = ""
    
    print(f"{'='*80}")
    print(f"📊 {method} on {dataset}{note} (保守版本)")
    print(f"{'='*80}")
    print(f"  学生数: {student_count}")
    print(f"  并行度: {MAX_WORKERS}")
    print(f"  策略: 2次post-test (平均+最低)，包含负数gain")
    
    # 预估时间
    estimated_time = (student_count * 6.5) / MAX_WORKERS
    print(f"  预计时间: {estimated_time:.0f}分钟 ({estimated_time/60:.1f}小时)")
    
    # 运行评估
    # 对于nips_task34，需要临时替换学生列表文件
    if dataset == 'nips_task34':
        # 备份原文件（如果存在）
        original_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json'
        backup_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json.backup'
        if os.path.exists(original_file):
            subprocess.run(f"cp {original_file} {backup_file}", shell=True)
        # 使用采样文件
        subprocess.run(f"cp {NIPS_SAMPLED_FILE} {original_file}", shell=True)
    
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_conservative.py --method {method} --dataset {dataset} --max-workers {MAX_WORKERS}"
    
    log_file = f'/mnt/localssd/logs/{method}-conservative_{dataset}.log'
    print(f"  日志文件: {log_file}")
    
    print(f"\n{'='*80}")
    print(f"🚀 开始评估")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    with open(log_file, 'w') as log:
        result = subprocess.run(cmd, shell=True, stdout=log, stderr=subprocess.STDOUT)
    
    # 恢复原文件（如果nips_task34）
    if dataset == 'nips_task34':
        backup_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json.backup'
        original_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json'
        if os.path.exists(backup_file):
            subprocess.run(f"mv {backup_file} {original_file}", shell=True)
    
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
    print("🚀 运行所有评估 - 主脚本")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示学生数
    print(f"\n学生数统计:")
    total_students = 0
    for dataset in DATASETS:
        count = get_student_count(dataset)
        total_students += count
        print(f"  {dataset}: {count}个")
    print(f"  总计: {total_students}个")
    
    # 任务列表
    print(f"\n任务列表:")
    print(f"  1. TASA-best-of-2 × nips_task34")
    print(f"  2-17. Baselines-conservative (4方法 × 4数据集)")
    print(f"  总计: 17个任务")
    
    # 预估总时间
    total_time = (total_students * 6.5) / MAX_WORKERS  # TASA
    total_time += (total_students * 6.5 * 4) / MAX_WORKERS  # 4个Baselines
    print(f"\n预计总时间: {total_time:.0f}分钟 ({total_time/60:.1f}小时)")
    
    overall_start = time.time()
    results = {}
    
    # 任务1: TASA on nips_task34
    print(f"\n\n{'='*80}")
    print(f"开始任务 1/17")
    print(f"{'='*80}")
    
    success = run_tasa_nips34()
    results['TASA_nips_task34'] = success
    
    if not success:
        print(f"\n⚠️  TASA on nips_task34 失败，继续下一个任务")
    
    # 任务2-17: Baselines
    task_num = 2
    
    for method in METHODS:
        for dataset in DATASETS:
            print(f"\n\n{'='*80}")
            print(f"开始任务 {task_num}/17")
            print(f"{'='*80}")
            
            key = f"{method}_{dataset}"
            success = run_baseline_evaluation(method, dataset, task_num)
            results[key] = success
            
            if not success:
                print(f"\n⚠️  {key} 失败，继续下一个任务")
            
            task_num += 1
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 所有评估总结")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n结果汇总:")
    print(f"{'任务':<40s} {'状态':<10s} {'平均Gain'}")
    print("-"*80)
    
    # TASA结果
    overall_file = '/mnt/localssd/bank/evaluation_results/TASA-best-of-2/nips_task34/overall.json'
    if os.path.exists(overall_file):
        with open(overall_file) as f:
            data = json.load(f)
        gain_str = f"{data['overall']['avg_best_learning_gain']*100:.1f}%"
        status = "✅ 成功"
    else:
        gain_str = "N/A"
        status = "❌ 失败"
    
    print(f"{'TASA-best-of-2 × nips_task34':<40s} {status:<10s} {gain_str}")
    
    # Baselines结果
    for method in METHODS:
        for dataset in DATASETS:
            key = f"{method}_{dataset}"
            
            overall_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file) as f:
                    data = json.load(f)
                gain_avg = f"{data['strategy_avg']['avg_learning_gain']*100:.1f}%"
                gain_min = f"{data['strategy_min']['avg_learning_gain']*100:.1f}%"
                gain_str = f"平均:{gain_avg} 最低:{gain_min}"
                status = "✅ 成功"
            else:
                gain_str = "N/A"
                status = "❌ 失败"
            
            print(f"{f'{method} × {dataset}':<40s} {status:<10s} {gain_str}")
    
    print(f"\n{'='*80}")
    print("✅ 所有评估完成！")
    print(f"{'='*80}")
    
    # 保存总结
    summary_file = '/mnt/localssd/all_evaluations_summary.json'
    summary = {
        'version': 'complete',
        'description': 'TASA + 4 Baselines on 4 datasets',
        'start_time': datetime.now().isoformat(),
        'total_time_hours': overall_time / 3600,
        'total_tasks': 17,
        'tasks': {
            'TASA': ['nips_task34'],
            'Baselines': METHODS,
            'Datasets': DATASETS
        },
        'results': results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 总结已保存: {summary_file}")

if __name__ == "__main__":
    main()

