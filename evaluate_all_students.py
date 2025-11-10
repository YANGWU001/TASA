#!/usr/bin/env python3
"""
评估数据集中的所有学生
支持断点续传、进度显示、错误处理
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict
import time
from tqdm import tqdm

from batch_test_students import evaluate_single_student

def get_all_student_ids(dataset: str) -> List[int]:
    """获取数据集中所有学生的ID"""
    session_dir = f'/mnt/localssd/bank/session/{dataset}'
    student_files = [f for f in os.listdir(session_dir) if f.endswith('.json')]
    student_ids = [int(f.replace('.json', '')) for f in student_files]
    return sorted(student_ids)

def get_completed_students(method: str, dataset: str) -> List[int]:
    """获取已完成评估的学生ID"""
    result_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
    if not os.path.exists(result_dir):
        return []
    
    completed = []
    for filename in os.listdir(result_dir):
        if filename.startswith('student_') and filename.endswith('.json'):
            try:
                # 解析 student_{id}_concept_{cid}.json
                parts = filename.replace('student_', '').replace('.json', '').split('_concept_')
                student_id = int(parts[0])
                completed.append(student_id)
            except:
                pass
    
    return list(set(completed))  # 去重

def generate_overall_statistics(method: str, dataset: str):
    """生成overall.json统计"""
    result_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
    
    # 读取所有学生结果
    results = []
    for filename in os.listdir(result_dir):
        if filename.startswith('student_') and filename.endswith('.json'):
            filepath = os.path.join(result_dir, filename)
            try:
                with open(filepath) as f:
                    result = json.load(f)
                results.append(result)
            except:
                pass
    
    if not results:
        print("❌ 没有找到评估结果")
        return
    
    # 计算统计
    avg_original = sum(r['original_accuracy'] for r in results) / len(results)
    avg_roleplay = sum(r['roleplay_accuracy'] for r in results) / len(results)
    avg_deviation = sum(abs(r['deviation']) for r in results) / len(results)
    
    # 按水平分组
    struggling = [r for r in results if r['original_accuracy'] < 0.4]
    developing = [r for r in results if 0.4 <= r['original_accuracy'] < 0.6]
    competent = [r for r in results if 0.6 <= r['original_accuracy'] < 0.8]
    strong = [r for r in results if r['original_accuracy'] >= 0.8]
    
    overall = {
        "method": method,
        "dataset": dataset,
        "num_students_evaluated": len(results),
        "average_original_accuracy": avg_original,
        "average_roleplay_accuracy": avg_roleplay,
        "average_absolute_deviation": avg_deviation,
        "performance_by_level": {
            "struggling": {
                "range": "<40%",
                "num_students": len(struggling),
                "avg_original_accuracy": sum(r['original_accuracy'] for r in struggling) / len(struggling) if struggling else 0,
                "avg_roleplay_accuracy": sum(r['roleplay_accuracy'] for r in struggling) / len(struggling) if struggling else 0,
                "avg_deviation": sum(abs(r['deviation']) for r in struggling) / len(struggling) if struggling else 0
            },
            "developing": {
                "range": "40-60%",
                "num_students": len(developing),
                "avg_original_accuracy": sum(r['original_accuracy'] for r in developing) / len(developing) if developing else 0,
                "avg_roleplay_accuracy": sum(r['roleplay_accuracy'] for r in developing) / len(developing) if developing else 0,
                "avg_deviation": sum(abs(r['deviation']) for r in developing) / len(developing) if developing else 0
            },
            "competent": {
                "range": "60-80%",
                "num_students": len(competent),
                "avg_original_accuracy": sum(r['original_accuracy'] for r in competent) / len(competent) if competent else 0,
                "avg_roleplay_accuracy": sum(r['roleplay_accuracy'] for r in competent) / len(competent) if competent else 0,
                "avg_deviation": sum(abs(r['deviation']) for r in competent) / len(competent) if competent else 0
            },
            "strong": {
                "range": "≥80%",
                "num_students": len(strong),
                "avg_original_accuracy": sum(r['original_accuracy'] for r in strong) / len(strong) if strong else 0,
                "avg_roleplay_accuracy": sum(r['roleplay_accuracy'] for r in strong) / len(strong) if strong else 0,
                "avg_deviation": sum(abs(r['deviation']) for r in strong) / len(strong) if strong else 0
            }
        }
    }
    
    # 保存
    overall_file = f'{result_dir}/overall.json'
    with open(overall_file, 'w') as f:
        json.dump(overall, f, indent=2)
    
    return overall

def evaluate_all_students(
    dataset: str = "assist2017",
    method: str = "pre-test",
    max_workers: int = 20,
    resume: bool = True
):
    """评估所有学生"""
    
    print(f"\n{'='*80}")
    print(f"🚀 全量学生评估系统")
    print(f"{'='*80}")
    print(f"Method: {method}")
    print(f"Dataset: {dataset}")
    print(f"Max Workers: {max_workers}")
    print(f"Resume Mode: {resume}")
    print(f"{'='*80}\n")
    
    # 获取所有学生
    all_students = get_all_student_ids(dataset)
    print(f"📊 总学生数: {len(all_students)}")
    
    # 检查已完成的学生
    if resume:
        completed = get_completed_students(method, dataset)
        print(f"✅ 已完成: {len(completed)}个学生")
        remaining = [sid for sid in all_students if sid not in completed]
        print(f"⏳ 待评估: {len(remaining)}个学生")
    else:
        remaining = all_students
        print(f"⏳ 待评估: {len(remaining)}个学生")
    
    if not remaining:
        print("\n✅ 所有学生都已完成评估！")
        print("\n生成最终统计...")
        overall = generate_overall_statistics(method, dataset)
        print_overall_summary(overall)
        return
    
    # 开始评估
    print(f"\n开始评估... (预计时间: ~{len(remaining) * 30 / max_workers / 60:.1f}分钟)\n")
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_student = {
            executor.submit(evaluate_single_student, student_id, dataset, method): student_id
            for student_id in remaining
        }
        
        # 使用tqdm显示进度
        with tqdm(total=len(remaining), desc="评估进度", ncols=100) as pbar:
            for future in as_completed(future_to_student):
                student_id = future_to_student[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"\n❌ 学生 {student_id} 失败: {e}")
                
                pbar.update(1)
                pbar.set_postfix({
                    'Success': success_count,
                    'Error': error_count
                })
                
                # 每100个学生更新一次overall统计
                if (success_count + error_count) % 100 == 0:
                    try:
                        generate_overall_statistics(method, dataset)
                    except:
                        pass
    
    elapsed_time = time.time() - start_time
    
    # 最终统计
    print(f"\n{'='*80}")
    print(f"✅ 评估完成!")
    print(f"{'='*80}")
    print(f"总耗时: {elapsed_time/60:.1f}分钟 ({elapsed_time:.1f}秒)")
    print(f"成功: {success_count}个学生")
    print(f"失败: {error_count}个学生")
    print(f"平均速度: {elapsed_time/len(remaining):.1f}秒/学生")
    print(f"{'='*80}\n")
    
    # 生成最终overall统计
    print("生成最终统计...")
    overall = generate_overall_statistics(method, dataset)
    print_overall_summary(overall)

def print_overall_summary(overall: Dict):
    """打印overall统计摘要"""
    if not overall:
        return
    
    print(f"\n{'='*80}")
    print(f"📊 Overall统计 - {overall['method']} @ {overall['dataset']}")
    print(f"{'='*80}")
    print(f"评估学生数: {overall['num_students_evaluated']}")
    print(f"平均原始准确率: {overall['average_original_accuracy']*100:.1f}%")
    print(f"平均Role-play准确率: {overall['average_roleplay_accuracy']*100:.1f}%")
    print(f"平均绝对偏差: {overall['average_absolute_deviation']*100:.1f}%")
    
    print(f"\n按水平分析:")
    for level, data in overall['performance_by_level'].items():
        if data['num_students'] > 0:
            print(f"\n{level.upper()} ({data['range']}):")
            print(f"  学生数: {data['num_students']}")
            print(f"  平均原始准确率: {data['avg_original_accuracy']*100:.1f}%")
            print(f"  平均Role-play准确率: {data['avg_roleplay_accuracy']*100:.1f}%")
            print(f"  平均偏差: {data['avg_deviation']*100:.1f}%")
    
    print(f"\n{'='*80}")
    print(f"💾 完整统计已保存至:")
    print(f"   /mnt/localssd/bank/evaluation_results/{overall['method']}/{overall['dataset']}/overall.json")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='评估数据集中的所有学生')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集名称')
    parser.add_argument('--method', type=str, default='pre-test', help='评估方法名称')
    parser.add_argument('--max-workers', type=int, default=20, help='并行线程数')
    parser.add_argument('--no-resume', action='store_true', help='不使用断点续传，重新评估所有学生')
    
    args = parser.parse_args()
    
    evaluate_all_students(
        dataset=args.dataset,
        method=args.method,
        max_workers=args.max_workers,
        resume=not args.no_resume
    )

