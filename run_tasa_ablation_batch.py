#!/usr/bin/env python3
"""
TASA Ablation批量评估脚本
支持3种ablation变体的评估
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
from tasa_tutoring_ablation import (
    TASATutorWithoutPersona,
    TASATutorWithoutMemory, 
    TASATutorWithoutForgetting
)
from tasa_evaluation_best_of_two import TASABestOfTwoEvaluator

# 全局锁
print_lock = Lock()
model_init_lock = Lock()

# 线程本地存储
import threading
thread_local = threading.local()

def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with print_lock:
        print(*args, **kwargs)

def get_tutor(ablation_type):
    """获取线程本地的对应ablation类型的Tutor实例"""
    tutor_key = f'tutor_{ablation_type}'
    if not hasattr(thread_local, tutor_key):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化TASA Tutor ({ablation_type})...")
            if ablation_type == 'woPersona':
                tutor = TASATutorWithoutPersona()
            elif ablation_type == 'woMemory':
                tutor = TASATutorWithoutMemory()
            elif ablation_type == 'woForgetting':
                tutor = TASATutorWithoutForgetting()
            else:
                raise ValueError(f"Unknown ablation type: {ablation_type}")
            setattr(thread_local, tutor_key, tutor)
    return getattr(thread_local, tutor_key)

def get_backbone_suffix():
    """获取backbone后缀"""
    from tasa_config import TUTOR_MODEL
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''

def get_evaluator():
    """获取线程本地的Evaluator实例"""
    if not hasattr(thread_local, 'evaluator'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Evaluator...")
            thread_local.evaluator = TASABestOfTwoEvaluator()
    return thread_local.evaluator

def process_single_student(student_id: int, dataset: str, ablation_type: str):
    """
    处理单个学生的完整流程（ablation版本）
    """
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🎓 开始处理学生 {student_id} (TASA-{ablation_type})")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        
        # Step 1: 检查dialogue是否存在
        from tasa_config import FORGETTING_SCORE_METHOD
        backbone_suffix = get_backbone_suffix()
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA-{ablation_type}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   📚 正在生成dialogue (TASA-{ablation_type})...")
            student_prompt = build_student_system_prompt(session)
            
            tutor = get_tutor(ablation_type)
            
            try:
                dialogue = tutor.conduct_tutoring_session(
                    student_id=student_id,
                    dataset=dataset,
                    concept_text=concept_text,
                    student_system_prompt=student_prompt
                )
                tutor.save_dialogue(dialogue, student_id, concept_text, dataset, backbone_suffix=backbone_suffix)
                safe_print(f"   ✅ Dialogue生成完成")
            except Exception as e:
                safe_print(f"   ❌ Dialogue生成失败: {e}")
                return None
        else:
            safe_print(f"   ✅ Dialogue已存在，跳过生成")
        
        # Step 2: 进行2次post-test评估
        safe_print(f"   📝 开始post-test评估 (Best-of-2)...")
        
        evaluator = get_evaluator()
        
        try:
            result = evaluator.evaluate_student_best_of_two(
                student_id=student_id,
                dataset=dataset
            )
            
            if result:
                safe_print(f"   ✅ 学生{student_id}评估完成")
                safe_print(f"      最高Post-test: {result['best_post_test_accuracy']*100:.1f}% (Gain={result['best_learning_gain']*100:.1f}%)")
                return result
            else:
                safe_print(f"   ❌ 学生{student_id}评估失败")
                return None
        except Exception as e:
            safe_print(f"   ❌ 评估失败: {e}")
            return None
    
    except Exception as e:
        safe_print(f"❌ 处理学生{student_id}时出错: {e}")
        return None

def batch_evaluate(students_file: str, dataset: str, ablation_type: str, max_workers: int = 5):
    """
    批量评估学生
    """
    # 加载学生列表
    with open(students_file) as f:
        students_data = json.load(f)
    
    if isinstance(students_data, list):
        student_ids = students_data
    elif isinstance(students_data, dict):
        if 'student_ids' in students_data:
            student_ids = students_data['student_ids']
        elif 'sampled_students' in students_data:
            student_ids = students_data['sampled_students']
        else:
            print(f"❌ 无法解析students文件: {students_file}")
            return
    else:
        print(f"❌ 无法解析students文件: {students_file}")
        return
    
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║          🔬 批量评估: TASA-{ablation_type} on {dataset}                     ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers}")
    print(f"{'='*80}\n")
    
    all_results = []
    successful_count = 0
    failed_count = 0
    
    # 并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_student, sid, dataset, ablation_type): sid 
            for sid in student_ids
        }
        
        for future in as_completed(futures):
            sid = futures[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    successful_count += 1
                else:
                    failed_count += 1
                
                # 打印进度
                total_processed = successful_count + failed_count
                safe_print(f"\n📈 进度: {total_processed}/{len(student_ids)} ({total_processed*100/len(student_ids):.1f}%) | 成功: {successful_count} | 失败: {failed_count}")
                
                if result:
                    safe_print(f"   ✅ 最高Post-test: {result['best_post_test_accuracy']*100:.1f}% (Gain={result['best_learning_gain']*100:.1f}%)")
                
            except Exception as e:
                safe_print(f"❌ 处理学生{sid}异常: {e}")
                failed_count += 1
    
    # 计算统计
    print(f"\n{'='*80}")
    print(f"\n📊 整体统计:")
    print(f"   学生数: {len(student_ids)}")
    
    if all_results:
        # Strategy 1: 最高分 (2次取最高)
        learning_gains_max = [r['best_learning_gain'] for r in all_results]
        print(f"\n   🔹 策略1: 最高分 (2次取最高)")
        print(f"      平均Learning Gain: {np.mean(learning_gains_max)*100:.1f}% ± {np.std(learning_gains_max)*100:.1f}%")
        print(f"      中位数: {np.median(learning_gains_max)*100:.1f}%")
        print(f"      范围: [{np.min(learning_gains_max)*100:.1f}%, {np.max(learning_gains_max)*100:.1f}%]")
        
        # Best-of-Two只有最佳策略
        # (不需要平均和最低策略，因为已经选择了最好的)
    
    print(f"\n✅ 批量评估完成！")
    print(f"   成功: {successful_count}/{len(student_ids)}")
    print(f"{'='*80}\n")
    
    # 保存结果
    from tasa_config import FORGETTING_SCORE_METHOD
    backbone_suffix = get_backbone_suffix()
    result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-{ablation_type}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
    os.makedirs(result_dir, exist_ok=True)
    
    overall_result = {
        'dataset': dataset,
        'ablation_type': ablation_type,
        'num_students': len(student_ids),
        'strategy_max': {
            'name': 'Best-of-Two策略 (2次取最高)',
            'avg_learning_gain': float(np.mean(learning_gains_max)),
            'std_learning_gain': float(np.std(learning_gains_max)),
            'median_learning_gain': float(np.median(learning_gains_max))
        } if all_results else None,
        'students': all_results
    }
    
    with open(f'{result_dir}/overall.json', 'w') as f:
        json.dump(overall_result, f, indent=2)
    
    print(f"💾 结果已保存: {result_dir}/overall.json")

def main():
    parser = argparse.ArgumentParser(description='TASA Ablation批量评估')
    parser.add_argument('--ablation', required=True, choices=['woPersona', 'woMemory', 'woForgetting'],
                       help='Ablation类型')
    parser.add_argument('--dataset', required=True, help='数据集名称')
    parser.add_argument('--students-file', required=True, help='学生ID列表文件')
    parser.add_argument('--max-workers', type=int, default=5, help='并行worker数量')
    parser.add_argument('--forgetting-method', default='lpkt', help='Forgetting score方法')
    
    args = parser.parse_args()
    
    # 设置forgetting方法
    os.environ['FORGETTING_SCORE_METHOD'] = args.forgetting_method
    
    batch_evaluate(
        students_file=args.students_file,
        dataset=args.dataset,
        ablation_type=args.ablation,
        max_workers=args.max_workers
    )

if __name__ == '__main__':
    main()

