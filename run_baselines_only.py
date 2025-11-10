#!/usr/bin/env python3
"""
直接运行所有Baseline评估（跳过TASA）
"""
import subprocess
import time
import json
import os
from datetime import datetime

# 配置
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
MAX_WORKERS = 40
NIPS_SAMPLED_FILE = '/mnt/localssd/qualified_students_nips_task34_150sampled.json'

def get_student_count(dataset):
    """获取数据集学生数"""
    if dataset == 'nips_task34':
        student_file = NIPS_SAMPLED_FILE
        key = 'sampled_count'
    else:
        student_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
        key = 'filtered_count'
    
    try:
        with open(student_file, 'r') as f:
            data = json.load(f)
        return data.get(key, 0)
    except:
        return 0

def run_baseline_evaluation(method, dataset, task_num):
    """运行单个baseline评估"""
    print(f"\n{'='*80}")
    print(f"开始任务 {task_num}/16")
    print(f"{'='*80}\n")
    
    print("#" * 80)
    print(f"# 任务 {task_num}/16: {method} on {dataset}")
    print("#" * 80)
    
    student_count = get_student_count(dataset)
    estimated_time = (student_count * 6.5) / MAX_WORKERS
    
    print(f"\n{'='*80}")
    print(f"📊 {method} on {dataset}")
    print(f"{'='*80}")
    print(f"  学生数: {student_count}")
    print(f"  并行度: {MAX_WORKERS}")
    print(f"  策略: 2次post-test取平均和最低分，包含负数gain")
    print(f"  预计时间: {estimated_time:.0f}分钟 ({estimated_time/60:.1f}小时)")
    print(f"  日志文件: /mnt/localssd/logs/{method}_{dataset}.log")
    
    print(f"\n{'='*80}")
    print(f"🚀 开始评估")
    print(f"{'='*80}\n")
    
    # nips_task34需要临时替换学生列表
    if dataset == 'nips_task34':
        original_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json'
        backup_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json.backup'
        if os.path.exists(original_file):
            subprocess.run(f"cp {original_file} {backup_file}", shell=True)
        subprocess.run(f"cp {NIPS_SAMPLED_FILE} {original_file}", shell=True)
    
    # 运行评估
    log_file = f'/mnt/localssd/logs/{method}_{dataset}.log'
    cmd = f"/opt/venv/bin/python3 -u /mnt/localssd/baseline_evaluation_conservative.py --method {method} --dataset {dataset} --max-workers {MAX_WORKERS}"
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, stdout=open(log_file, 'w'), stderr=subprocess.STDOUT)
    elapsed_time = (time.time() - start_time) / 60
    
    # 恢复原始文件
    if dataset == 'nips_task34':
        backup_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json.backup'
        original_file = '/mnt/localssd/qualified_students_nips_task34_20to60.json'
        if os.path.exists(backup_file):
            subprocess.run(f"mv {backup_file} {original_file}", shell=True)
    
    if result.returncode == 0:
        print(f"\n⏱️  实际用时: {elapsed_time:.1f}分钟")
        print(f"✅ {method} on {dataset} 完成")
        
        # 读取结果
        overall_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}/overall.json'
        if os.path.exists(overall_file):
            with open(overall_file) as f:
                overall = json.load(f)
            
            print(f"\n📊 结果:")
            print(f"   学生数: {overall['num_students']}")
            
            # 最高分策略
            if 'strategy_max' in overall:
                max_stats = overall['strategy_max']
                print(f"\n   【最高分策略】")
                print(f"   平均Learning Gain: {max_stats['avg_learning_gain']*100:.1f}% ± {max_stats['std_learning_gain']*100:.1f}%")
                print(f"   正增长: {max_stats['num_positive_gain']}个, 负增长: {max_stats['num_negative_gain']}个")
            
            # 平均分策略
            if 'strategy_avg' in overall:
                avg_stats = overall['strategy_avg']
                print(f"\n   【平均分策略】")
                print(f"   平均Learning Gain: {avg_stats['avg_learning_gain']*100:.1f}% ± {avg_stats['std_learning_gain']*100:.1f}%")
                print(f"   正增长: {avg_stats['num_positive_gain']}个, 负增长: {avg_stats['num_negative_gain']}个")
            
            # 最低分策略
            if 'strategy_min' in overall:
                min_stats = overall['strategy_min']
                print(f"\n   【最低分策略】")
                print(f"   平均Learning Gain: {min_stats['avg_learning_gain']*100:.1f}% ± {min_stats['std_learning_gain']*100:.1f}%")
                print(f"   正增长: {min_stats['num_positive_gain']}个, 负增长: {min_stats['num_negative_gain']}个")
        
        return True
    else:
        print(f"❌ {method} on {dataset} 失败")
        print(f"   查看日志: {log_file}")
        return False

def main():
    print("="*80)
    print("🚀 运行所有Baseline评估")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 统计
    student_counts = {ds: get_student_count(ds) for ds in DATASETS}
    total_students = sum(student_counts.values())
    
    print(f"\n学生数统计:")
    for ds, count in student_counts.items():
        print(f"  {ds}: {count}个")
    print(f"  总计: {total_students}个")
    
    print(f"\n任务列表:")
    print(f"  Baselines-conservative (4方法 × 4数据集)")
    print(f"  总计: 16个任务")
    
    # 时间估算
    total_time = (total_students * 6.5 * 4) / MAX_WORKERS
    print(f"\n预计总时间: {total_time:.0f}分钟 ({total_time/60:.1f}小时)")
    print("\n")
    
    # 运行所有baseline任务
    start_time = time.time()
    task_num = 1
    completed = 0
    
    for method in METHODS:
        for dataset in DATASETS:
            success = run_baseline_evaluation(method, dataset, task_num)
            if success:
                completed += 1
            task_num += 1
            print("\n")
    
    # 总结
    elapsed_time = (time.time() - start_time) / 60
    print("\n" + "="*80)
    print("📊 所有Baseline评估完成")
    print("="*80)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总用时: {elapsed_time:.0f}分钟 ({elapsed_time/60:.1f}小时)")
    print(f"完成任务: {completed}/16")
    
    # 显示所有结果
    print("\n" + "="*80)
    print("📈 所有结果汇总")
    print("="*80)
    
    for method in METHODS:
        print(f"\n【{method}】")
        for dataset in DATASETS:
            overall_file = f'/mnt/localssd/bank/evaluation_results/{method}-conservative/{dataset}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file) as f:
                    overall = json.load(f)
                
                print(f"\n  {dataset} ({overall['num_students']}个学生):")
                
                if 'strategy_max' in overall:
                    max_stats = overall['strategy_max']
                    print(f"    最高分策略: {max_stats['avg_learning_gain']*100:.1f}% ± {max_stats['std_learning_gain']*100:.1f}%")
                
                if 'strategy_avg' in overall:
                    avg_stats = overall['strategy_avg']
                    print(f"    平均分策略: {avg_stats['avg_learning_gain']*100:.1f}% ± {avg_stats['std_learning_gain']*100:.1f}%")
                
                if 'strategy_min' in overall:
                    min_stats = overall['strategy_min']
                    print(f"    最低分策略: {min_stats['avg_learning_gain']*100:.1f}% ± {min_stats['std_learning_gain']*100:.1f}%")

if __name__ == '__main__':
    main()

