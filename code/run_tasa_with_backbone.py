#!/usr/bin/env python3
"""
TASA批量评估脚本 - 支持不同Backbone
基于run_tasa_batch_best_of_two.py，添加backbone支持
"""

import json
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import numpy as np

from student_roleplay_evaluation import build_student_system_prompt, load_session
from tasa_tutoring import TASATutor
from tasa_evaluation_best_of_two import TASABestOfTwoEvaluator

# 全局锁
print_lock = Lock()
model_init_lock = Lock()

import threading
thread_local = threading.local()

def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with print_lock:
        print(*args, **kwargs)

def get_method_name(backbone):
    """根据backbone生成method名称"""
    if backbone == "gpt-oss-120b":
        return "TASA-best-of-2"
    elif "llama" in backbone.lower():
        return "TASA-llama-best-of-2"
    elif "qwen" in backbone.lower():
        return "TASA-qwen-best-of-2"
    else:
        return f"TASA-{backbone}-best-of-2"

def evaluate_student_wrapper(args):
    """评估单个学生的wrapper"""
    student_id, dataset, backbone = args
    
    # 获取线程本地的evaluator
    if not hasattr(thread_local, 'evaluator'):
        with model_init_lock:
            thread_local.evaluator = TASABestOfTwoEvaluator()
    
    try:
        method_name = get_method_name(backbone)
        result = thread_local.evaluator.evaluate_student_best_of_two(student_id, dataset)
        
        if result:
            # 保存时使用带backbone的method名称
            thread_local.evaluator.save_result(result, method=method_name)
            return (True, result)
        else:
            return (False, None)
    except Exception as e:
        safe_print(f"❌ 学生{student_id}评估失败: {e}")
        return (False, None)

def load_student_list(dataset, args):
    """加载学生列表"""
    if args.students_file:
        list_file = args.students_file
        safe_print(f"📋 使用指定的学生列表: {list_file}")
    elif args.range20to60:
        list_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
        safe_print(f"📋 使用20%-60%过滤的学生列表")
    elif args.lt60:
        list_file = f'/mnt/localssd/qualified_students_{dataset}_lt60.json'
        safe_print(f"📋 使用<60%过滤的学生列表")
    elif args.filtered:
        list_file = f'/mnt/localssd/qualified_students_{dataset}_filtered.json'
        safe_print(f"📋 使用过滤后的学生列表（排除pre-test=100%）")
    else:
        list_file = f'/mnt/localssd/qualified_students_{dataset}.json'
        safe_print(f"📋 使用完整的学生列表")
    
    with open(list_file) as f:
        data = json.load(f)
    
    if 'sampled_students' in data:
        students = data['sampled_students']
    elif 'students' in data:
        students = data['students']
    else:
        students = list(data.keys())
    
    return students

def generate_overall_stats(results, dataset, backbone):
    """生成overall统计"""
    method_name = get_method_name(backbone)
    
    learning_gains = [r['best_learning_gain'] for r in results]
    improvements = [r['best_improvement'] for r in results]
    
    avg_gain = np.mean(learning_gains)
    std_gain = np.std(learning_gains, ddof=1) if len(learning_gains) > 1 else 0
    median_gain = np.median(learning_gains)
    avg_improvement = np.mean(improvements)
    
    # 按水平分组
    struggling = [r for r in results if r['pre_test_accuracy'] < 0.4]
    developing = [r for r in results if 0.4 <= r['pre_test_accuracy'] < 0.6]
    competent = [r for r in results if 0.6 <= r['pre_test_accuracy'] < 0.8]
    strong = [r for r in results if r['pre_test_accuracy'] >= 0.8]
    
    overall_stats = {
        "dataset": dataset,
        "num_students": len(results),
        "method": method_name,
        "backbone": backbone,
        "overall": {
            "avg_learning_gain": avg_gain,
            "std_learning_gain": std_gain,
            "median_learning_gain": median_gain,
            "avg_improvement": avg_improvement,
            "min_gain": min(learning_gains),
            "max_gain": max(learning_gains)
        },
        "by_level": {
            "struggling": {
                "count": len(struggling),
                "avg_gain": np.mean([r['best_learning_gain'] for r in struggling]) if struggling else 0,
                "avg_pre_test": np.mean([r['pre_test_accuracy'] for r in struggling]) if struggling else 0
            },
            "developing": {
                "count": len(developing),
                "avg_gain": np.mean([r['best_learning_gain'] for r in developing]) if developing else 0,
                "avg_pre_test": np.mean([r['pre_test_accuracy'] for r in developing]) if developing else 0
            },
            "competent": {
                "count": len(competent),
                "avg_gain": np.mean([r['best_learning_gain'] for r in competent]) if competent else 0,
                "avg_pre_test": np.mean([r['pre_test_accuracy'] for r in competent]) if competent else 0
            },
            "strong": {
                "count": len(strong),
                "avg_gain": np.mean([r['best_learning_gain'] for r in strong]) if strong else 0,
                "avg_pre_test": np.mean([r['pre_test_accuracy'] for r in strong]) if strong else 0
            }
        },
        "students": results
    }
    
    # 保存
    output_dir = f"/mnt/localssd/bank/evaluation_results/{method_name}/{dataset}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/overall.json"
    
    with open(output_file, 'w') as f:
        json.dump(overall_stats, f, indent=2)
    
    safe_print(f"\n📊 整体统计:")
    safe_print(f"   学生数: {len(results)}")
    safe_print(f"   平均Learning Gain: {avg_gain*100:.1f}% ± {std_gain*100:.1f}%")
    safe_print(f"   中位数: {median_gain*100:.1f}%")
    safe_print(f"   范围: [{min(learning_gains)*100:.1f}%, {max(learning_gains)*100:.1f}%]")
    safe_print(f"\n   按水平分组:")
    safe_print(f"      Struggling (<40%): {len(struggling)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in struggling])*100:.1f}%" if struggling else "      Struggling: 0人")
    safe_print(f"      Developing (40-60%): {len(developing)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in developing])*100:.1f}%" if developing else "      Developing: 0人")
    safe_print(f"      Competent (60-80%): {len(competent)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in competent])*100:.1f}%" if competent else "      Competent: 0人")
    safe_print(f"      Strong (≥80%): {len(strong)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in strong])*100:.1f}%" if strong else "      Strong: 0人")
    
    safe_print(f"\n💾 整体统计已保存至: {output_file}")
    
    return overall_stats

def main():
    parser = argparse.ArgumentParser(description='TASA批量评估 - 支持不同Backbone')
    parser.add_argument('--dataset', type=str, required=True, help='数据集名称')
    parser.add_argument('--backbone', type=str, default='gpt-oss-120b', 
                       help='Backbone模型 (gpt-oss-120b, llama-3.1-8b, qwen3-4b)')
    parser.add_argument('--students-file', type=str, help='直接指定学生列表文件路径')
    parser.add_argument('--range20to60', action='store_true', help='使用20%-60%范围的学生')
    parser.add_argument('--lt60', action='store_true', help='使用<60%的学生')
    parser.add_argument('--filtered', action='store_true', help='使用过滤后的学生（排除100%）')
    parser.add_argument('--all', action='store_true', help='评估所有学生')
    parser.add_argument('--max-workers', type=int, default=10, help='最大并行数')
    
    args = parser.parse_args()
    
    dataset = args.dataset
    backbone = args.backbone
    method_name = get_method_name(backbone)
    
    safe_print("="*80)
    safe_print(f"🚀 TASA批量评估 (Best-of-2策略)")
    safe_print("="*80)
    safe_print(f"   Dataset: {dataset}")
    safe_print(f"   Backbone: {backbone}")
    safe_print(f"   Method: {method_name}")
    safe_print(f"   Max Workers: {args.max_workers}")
    safe_print("="*80)
    
    # 加载学生列表
    students = load_student_list(dataset, args)
    
    if not args.all:
        safe_print(f"\n请使用 --all 参数来评估所有学生")
        return
    
    safe_print(f"\n将评估 {len(students)} 个学生")
    
    # 并行评估
    start_time = time.time()
    results = []
    failed = []
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_student = {
            executor.submit(evaluate_student_wrapper, (s['student_id'] if isinstance(s, dict) else int(s), dataset, backbone)): 
            (s['student_id'] if isinstance(s, dict) else int(s)) for s in students
        }
        
        for future in as_completed(future_to_student):
            student_id = future_to_student[future]
            try:
                success, result = future.result()
                if success and result:
                    results.append(result)
                    safe_print(f"✅ 学生{student_id}评估完成 ({len(results)}/{len(students)})")
                else:
                    failed.append(student_id)
                    safe_print(f"❌ 学生{student_id}评估失败 ({len(results)}/{len(students)})")
            except Exception as e:
                failed.append(student_id)
                safe_print(f"❌ 学生{student_id}发生异常: {e}")
    
    elapsed_time = (time.time() - start_time) / 60
    
    safe_print(f"\n✅ 批量评估完成！")
    safe_print(f"   总用时: {elapsed_time:.1f}分钟")
    safe_print(f"   成功: {len(results)}/{len(students)}")
    safe_print(f"   失败: {len(failed)}/{len(students)}")
    
    if failed:
        safe_print(f"\n失败的学生ID: {failed}")
    
    if results:
        generate_overall_stats(results, dataset, backbone)

if __name__ == '__main__':
    main()

