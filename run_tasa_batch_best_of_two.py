#!/usr/bin/env python3
"""
TASA批量评估脚本 - Best-of-2策略
对筛选后的学生进行批量评估，每个学生测试2次，选择Learning Gain最大的
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import numpy as np

from student_roleplay_evaluation import build_student_system_prompt, load_session
from tasa_tutoring import TASATutor
from tasa_evaluation_best_of_two import TASABestOfTwoEvaluator

# 全局锁用于打印和模型初始化
print_lock = Lock()
model_init_lock = Lock()

# 全局模型缓存（每个线程第一次使用时初始化）
import threading
thread_local = threading.local()

def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with print_lock:
        print(*args, **kwargs)

def get_tutor():
    """获取线程本地的TASATutor实例"""
    if not hasattr(thread_local, 'tutor'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化TASATutor...")
            thread_local.tutor = TASATutor()
    return thread_local.tutor

def get_backbone_suffix():
    """根据TUTOR_MODEL获取backbone后缀，用于区分dialogue目录"""
    from tasa_config import TUTOR_MODEL
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''  # gpt-oss-120b 不加后缀，保持向后兼容

def get_evaluator():
    """获取线程本地的TASABestOfTwoEvaluator实例"""
    if not hasattr(thread_local, 'evaluator'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Evaluator...")
            thread_local.evaluator = TASABestOfTwoEvaluator()
    return thread_local.evaluator

def process_single_student(student_id: int, dataset: str):
    """
    处理单个学生的完整流程
    1. 检查/生成dialogue（如果不存在则生成）
    2. 进行2次post-test评估
    3. 选择最佳结果
    
    注意：使用线程本地存储+锁保护初始化，支持并行
    """
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🎓 开始处理学生 {student_id}")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        
        # Step 1: 检查dialogue是否存在，不存在则生成
        # 根据backbone使用不同的dialogue目录，根据FS_METHOD使用不同子目录
        from tasa_config import FORGETTING_SCORE_METHOD
        backbone_suffix = get_backbone_suffix()
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   📚 正在生成dialogue (backbone{backbone_suffix})...")
            student_prompt = build_student_system_prompt(session)
            
            # 获取线程本地的tutor实例（自动初始化）
            tutor = get_tutor()
            
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
            safe_print(f"   ✅ Dialogue已存在 (backbone{backbone_suffix})")
        
        # Step 2: 进行Best-of-2评估
        safe_print(f"   📊 开始Best-of-2评估...")
        
        # 获取线程本地的evaluator实例（自动初始化）
        evaluator = get_evaluator()
        
        result = evaluator.evaluate_student_best_of_two(student_id, dataset)
        
        if result:
            evaluator.save_result(result)
            safe_print(f"   ✅ 学生{student_id}评估完成: Gain={result['best_learning_gain']*100:.1f}%")
            return result
        else:
            safe_print(f"   ❌ 学生{student_id}评估失败")
            return None
            
    except Exception as e:
        safe_print(f"   ❌ 学生{student_id}处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_batch_evaluation(student_ids, dataset='assist2017', max_workers=10):
    """
    批量运行TASA评估
    
    Args:
        student_ids: 学生ID列表
        dataset: 数据集名称
        max_workers: 最大并行worker数
    """
    print("="*80)
    print(f"🚀 TASA批量评估启动")
    print("="*80)
    print(f"   数据集: {dataset}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers} workers")
    print(f"   策略: Best-of-2 (每个学生2次，选最好)")
    print(f"   模式: 并行处理（自动生成缺失的dialogue）")
    print("="*80)
    
    # 记录开始时间
    start_time = time.time()
    
    # 使用线程池并行处理
    all_results = []
    completed = 0
    failed = 0
    
    print(f"\n{'='*80}")
    print(f"🔄 开始批量处理 ({max_workers}个并行worker)")
    print(f"   技术: 线程本地存储 + 锁保护初始化")
    print(f"   优势: 支持并行但避免模型初始化冲突")
    print(f"{'='*80}\n")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务（不传递共享的对象，让每个worker自己初始化）
        future_to_student = {
            executor.submit(process_single_student, student_id, dataset): student_id
            for student_id in student_ids
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_student):
            student_id = future_to_student[future]
            
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    completed += 1
                else:
                    failed += 1
                
                # 显示进度
                total_processed = completed + failed
                progress = total_processed / len(student_ids) * 100
                elapsed = time.time() - start_time
                avg_time = elapsed / total_processed if total_processed > 0 else 0
                eta = avg_time * (len(student_ids) - total_processed)
                
                with print_lock:
                    print(f"\n{'─'*80}")
                    print(f"📈 进度: {total_processed}/{len(student_ids)} ({progress:.1f}%) | "
                          f"成功: {completed} | 失败: {failed}")
                    print(f"⏱️  已用时: {elapsed/60:.1f}分钟 | 预计剩余: {eta/60:.1f}分钟")
                    print(f"{'─'*80}")
                
            except Exception as e:
                failed += 1
                with print_lock:
                    print(f"\n❌ 学生{student_id}处理异常: {e}")
    
    # 总结
    total_time = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ 批量评估完成！")
    print(f"{'='*80}")
    print(f"   总学生数: {len(student_ids)}")
    print(f"   成功: {completed}")
    print(f"   失败: {failed}")
    print(f"   总耗时: {total_time/60:.1f}分钟 ({total_time/3600:.2f}小时)")
    print(f"   平均每个学生: {total_time/len(student_ids):.1f}秒")
    
    # 生成统计
    if all_results:
        generate_overall_stats(all_results, dataset)
    
    return all_results

def generate_overall_stats(results, dataset):
    """生成整体统计"""
    print(f"\n{'='*80}")
    print(f"📊 生成整体统计")
    print(f"{'='*80}")
    
    # 计算统计量
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
        "method": "TASA-best-of-2",
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
    
    # 保存（使用backbone suffix区分不同LLM，使用FS_METHOD区分不同遗忘曲线方法）
    from tasa_config import FORGETTING_SCORE_METHOD
    backbone_suffix = get_backbone_suffix()
    output_dir = f"/mnt/localssd/bank/evaluation_results/TASA{backbone_suffix}-best-of-2/{dataset}/{FORGETTING_SCORE_METHOD}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/overall.json"
    
    with open(output_file, 'w') as f:
        json.dump(overall_stats, f, indent=2)
    
    print(f"\n📊 整体统计:")
    print(f"   学生数: {len(results)}")
    print(f"   平均Learning Gain: {avg_gain*100:.1f}% ± {std_gain*100:.1f}%")
    print(f"   中位数: {median_gain*100:.1f}%")
    print(f"   范围: [{min(learning_gains)*100:.1f}%, {max(learning_gains)*100:.1f}%]")
    
    print(f"\n   按水平分组:")
    print(f"      Struggling (<40%): {len(struggling)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in struggling])*100:.1f}%" if struggling else "      Struggling: 0人")
    print(f"      Developing (40-60%): {len(developing)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in developing])*100:.1f}%" if developing else "      Developing: 0人")
    print(f"      Competent (60-80%): {len(competent)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in competent])*100:.1f}%" if competent else "      Competent: 0人")
    print(f"      Strong (≥80%): {len(strong)}人, 平均Gain={np.mean([r['best_learning_gain'] for r in strong])*100:.1f}%" if strong else "      Strong: 0人")
    
    print(f"\n💾 整体统计已保存至: {output_file}")
    
    return overall_stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TASA批量评估 - Best-of-2')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集')
    parser.add_argument('--num-students', type=int, default=9, help='测试学生数量')
    parser.add_argument('--max-workers', type=int, default=10, help='最大并行worker数')
    parser.add_argument('--all', action='store_true', help='评估所有符合条件的学生')
    parser.add_argument('--students-file', type=str, help='直接指定学生列表文件路径')
    parser.add_argument('--filtered', action='store_true', help='使用过滤后的列表（排除Pre-test=100%）')
    parser.add_argument('--lt60', action='store_true', help='使用<60%过滤（排除Pre-test≥60%）')
    parser.add_argument('--range20to60', action='store_true', help='使用20%-60%过滤（仅保留Pre-test在20%-60%）')
    
    args = parser.parse_args()
    
    # 选择学生列表文件（优先级：students-file > range20to60 > lt60 > filtered > 完整）
    if args.students_file:
        list_file = args.students_file
        print(f"📋 使用指定的学生列表: {list_file}")
    elif args.range20to60:
        list_file = '/mnt/localssd/qualified_students_20to60.json'
        print(f"📋 使用20%-60%过滤的学生列表（Pre-test在20%-60%之间）")
    elif args.lt60:
        list_file = '/mnt/localssd/qualified_students_lt60.json'
        print(f"📋 使用<60%过滤的学生列表（排除Pre-test≥60%）")
    elif args.filtered:
        list_file = '/mnt/localssd/qualified_students_filtered.json'
        print(f"📋 使用过滤后的学生列表（排除Pre-test=100%）")
    else:
        list_file = '/mnt/localssd/qualified_students_list.json'
        print(f"📋 使用完整的学生列表")
    
    # 加载符合条件的学生列表
    with open(list_file) as f:
        qualified_data = json.load(f)
    
    # 支持不同的键名格式
    if 'sampled_students' in qualified_data:
        # 新格式：采样后的学生ID列表
        all_student_ids = qualified_data['sampled_students']
    elif 'students' in qualified_data:
        # 旧格式：完整的学生对象列表
        all_student_ids = [s['student_id'] for s in qualified_data['students']]
    else:
        raise ValueError(f"Invalid student file format. Expected 'students' or 'sampled_students' key.")
    
    if args.all:
        student_ids = all_student_ids
    else:
        student_ids = all_student_ids[:args.num_students]
    
    total_count = qualified_data.get('total_students') or qualified_data.get('filtered_count') or qualified_data.get('qualified_count') or len(all_student_ids)
    print(f"\n将评估 {len(student_ids)} 个学生（共{total_count}个符合条件）")
    
    # 运行批量评估
    results = run_batch_evaluation(
        student_ids=student_ids,
        dataset=args.dataset,
        max_workers=args.max_workers
    )
    
    print(f"\n{'='*80}")
    print(f"✅ 全部完成！")
    print(f"{'='*80}")

