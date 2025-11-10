#!/usr/bin/env python3
"""
为 Vanilla-ICL-turns28-llama 进行每4轮的evaluation
与 TutorLLM 的evaluation格式一致
"""

import json
import os
import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 设置环境
os.environ['TASA_CONFIG'] = 'llama'

from tasa_config_llama import FORGETTING_SCORE_METHOD
from tasa_evaluation import TASAEvaluator

# Thread-safe print
print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg)
        sys.stdout.flush()

def load_dialogue_from_file(dialogue_file, num_turns):
    """从文件加载dialogue并截取到指定轮数"""
    try:
        with open(dialogue_file, 'r') as f:
            dialogue = json.load(f)
        
        # 截取到指定轮数
        # round值从0开始，num_turns=4表示到round 2（0, 1, 2三个round，共4-6个turns）
        max_round = num_turns // 2
        truncated = [d for d in dialogue if d.get('round', 0) <= max_round]
        
        return truncated
    except Exception as e:
        safe_print(f"   ❌ 加载dialogue失败: {e}")
        return None

def evaluate_single_student(student_id, concept_text, dataset, num_dialogue_turns):
    """评估单个学生"""
    try:
        # 加载dialogue
        dialogue_file = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}/dkt/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   ⚠️  学生{student_id}的dialogue不存在")
            return None
        
        dialogue = load_dialogue_from_file(dialogue_file, num_dialogue_turns)
        if dialogue is None:
            return None
        
        safe_print(f"   📝 学生{student_id} | {len(dialogue)} turns")
        
        # 初始化evaluator
        evaluator = TASAEvaluator()
        
        # 加载session获取concept_id和persona
        from student_roleplay_evaluation import load_session, build_student_system_prompt
        
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        if not os.path.exists(session_file):
            safe_print(f"   ❌ Session文件不存在: {session_file}")
            return None
        
        session = load_session(session_file)
        concept_id = session['concept_id']
        
        # 构建student prompt
        student_system_prompt = build_student_system_prompt(session)
        
        # 加载post-test问题
        questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
        with open(questions_file) as f:
            all_questions = json.load(f)
        questions = all_questions[str(concept_id)]['questions']
        
        # Pre-test score - 从pretest文件读取
        pretest_file = f'/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json'
        if not os.path.exists(pretest_file):
            safe_print(f"   ❌ Pre-test文件不存在: {pretest_file}")
            return None
        
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        pre_test_score = pretest_data['roleplay_accuracy']
        safe_print(f"   📊 Pre-test: {pre_test_score*100:.1f}%")
        
        # Post-test (运行2次)
        safe_print(f"   📊 Post-test (2次)...")
        post_test_results = []
        
        for run_id in range(1, 3):
            post_acc, _ = evaluator.conduct_post_test(
                student_id, dataset, concept_text,
                dialogue, questions, student_system_prompt
            )
            post_test_results.append(post_acc)
            safe_print(f"   Run {run_id}: {post_acc*100:.1f}%")
        
        # 计算三种策略
        max_post_test = max(post_test_results)
        avg_post_test = np.mean(post_test_results)
        min_post_test = min(post_test_results)
        
        # 计算learning gain
        if pre_test_score >= 1.0:
            learning_gain_max = 0.0
            learning_gain_avg = 0.0
            learning_gain_min = 0.0
        else:
            learning_gain_max = (max_post_test - pre_test_score) / (1.0 - pre_test_score)
            learning_gain_avg = (avg_post_test - pre_test_score) / (1.0 - pre_test_score)
            learning_gain_min = (min_post_test - pre_test_score) / (1.0 - pre_test_score)
        
        result = {
            'student_id': student_id,
            'pre_test_score': pre_test_score,
            'dialogue_turns': num_dialogue_turns,
            'method': 'Vanilla-ICL',
            'post_test_run1': post_test_results[0],
            'post_test_run2': post_test_results[1],
            # Best策略
            'max_post_test_accuracy': max_post_test,
            'learning_gain_max': learning_gain_max,
            # Average策略
            'avg_post_test_accuracy': avg_post_test,
            'learning_gain_avg': learning_gain_avg,
            # Worst策略
            'min_post_test_accuracy': min_post_test,
            'learning_gain_min': learning_gain_min
        }
        
        safe_print(f"   ✅ 学生{student_id}完成 | Gain(Best): {learning_gain_max*100:.1f}%")
        return result
        
    except Exception as e:
        safe_print(f"   ❌ 学生{student_id}失败: {e}")
        import traceback
        safe_print(f"   {traceback.format_exc()}")
        return None

def batch_evaluate_turns(num_dialogue_turns, dataset='assist2017', max_workers=5):
    """批量评估指定轮数"""
    print(f"\n{'='*80}")
    print(f"📊 评估 Vanilla-ICL-turns{num_dialogue_turns}-llama")
    print(f"{'='*80}")
    
    # 加载学生列表
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    with open(students_file, 'r') as f:
        data = json.load(f)
        students = data.get('sampled_students', data.get('students', []))
    
    # 构建任务列表
    tasks = []
    for student_info in students:
        if isinstance(student_info, dict):
            student_id = student_info['student_id']
            concept = student_info['target_concept']
        else:
            student_id = student_info
            # 从dialogue文件名推断concept
            dialogue_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}/dkt'
            files = [f for f in os.listdir(dialogue_dir) if f.startswith(f'{student_id}-')]
            if files:
                concept = files[0].replace(f'{student_id}-', '').replace('.json', '')
            else:
                safe_print(f"⚠️  学生{student_id}找不到dialogue")
                continue
        
        tasks.append((student_id, concept))
    
    print(f"学生数: {len(tasks)}")
    print(f"Max workers: {max_workers}")
    print()
    
    # 并行评估
    all_results = []
    successful_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(evaluate_single_student, sid, concept, dataset, num_dialogue_turns): (sid, concept)
            for sid, concept in tasks
        }
        
        for future in as_completed(futures):
            sid, concept = futures[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    successful_count += 1
            except Exception as e:
                safe_print(f"❌ 学生{sid}异常: {e}")
    
    # 统计
    print(f"\n{'='*80}")
    print(f"📊 整体统计 (Vanilla-ICL, {num_dialogue_turns} turns):")
    print(f"{'='*80}")
    
    if all_results:
        learning_gains_max = [r['learning_gain_max'] for r in all_results]
        learning_gains_avg = [r['learning_gain_avg'] for r in all_results]
        learning_gains_min = [r['learning_gain_min'] for r in all_results]
        
        print(f"\n   Best策略   平均Learning Gain: {np.mean(learning_gains_max)*100:.1f}% ± {np.std(learning_gains_max)*100:.1f}%")
        print(f"   Average策略 平均Learning Gain: {np.mean(learning_gains_avg)*100:.1f}% ± {np.std(learning_gains_avg)*100:.1f}%")
        print(f"   Worst策略  平均Learning Gain: {np.mean(learning_gains_min)*100:.1f}% ± {np.std(learning_gains_min)*100:.1f}%")
    
    print(f"\n✅ 评估完成！")
    print(f"   成功: {successful_count}/{len(tasks)}")
    print(f"{'='*80}\n")
    
    # 保存结果
    result_dir = f'/mnt/localssd/bank/evaluation_results/Vanilla-ICL-turns{num_dialogue_turns}-llama/{dataset}/dkt'
    os.makedirs(result_dir, exist_ok=True)
    
    overall_result = {
        'dataset': dataset,
        'method': 'Vanilla-ICL',
        'dialogue_turns': num_dialogue_turns,
        'num_students': len(tasks),
        # Best策略
        'strategy_max': {
            'avg_learning_gain': float(np.mean(learning_gains_max)) if all_results else 0.0,
            'std_learning_gain': float(np.std(learning_gains_max)) if all_results else 0.0,
            'median_learning_gain': float(np.median(learning_gains_max)) if all_results else 0.0
        },
        # Average策略
        'strategy_avg': {
            'avg_learning_gain': float(np.mean(learning_gains_avg)) if all_results else 0.0,
            'std_learning_gain': float(np.std(learning_gains_avg)) if all_results else 0.0,
            'median_learning_gain': float(np.median(learning_gains_avg)) if all_results else 0.0
        },
        # Worst策略
        'strategy_min': {
            'avg_learning_gain': float(np.mean(learning_gains_min)) if all_results else 0.0,
            'std_learning_gain': float(np.std(learning_gains_min)) if all_results else 0.0,
            'median_learning_gain': float(np.median(learning_gains_min)) if all_results else 0.0
        },
        'students': all_results
    }
    
    with open(f'{result_dir}/overall.json', 'w') as f:
        json.dump(overall_result, f, indent=2)
    
    print(f"💾 结果已保存: {result_dir}/overall.json\n")
    
    return overall_result

def main():
    DIALOGUE_TURNS = [0, 4, 8, 12, 16, 20, 24, 28]
    DATASET = 'assist2017'
    MAX_WORKERS = 5  # 每个turns评估使用5个worker
    
    print('='*80)
    print('🔬 Vanilla-ICL Dialogue Turns Ablation Evaluation')
    print('='*80)
    print(f'Dialogue turns: {DIALOGUE_TURNS}')
    print(f'Dataset: {DATASET}')
    print(f'Max workers: {MAX_WORKERS}')
    print('='*80)
    print()
    
    all_results = {}
    
    for turns in DIALOGUE_TURNS:
        result = batch_evaluate_turns(turns, DATASET, MAX_WORKERS)
        if result:
            all_results[str(turns)] = result['strategy_max']['avg_learning_gain']
    
    # 打印汇总
    print('\n' + '='*80)
    print('📊 所有Turns的Learning Gain汇总（Best策略）')
    print('='*80)
    for turns in DIALOGUE_TURNS:
        if str(turns) in all_results:
            lg = all_results[str(turns)] * 100
            print(f'  {turns:2d} turns: {lg:6.1f}%')
    print('='*80)

if __name__ == '__main__':
    main()

