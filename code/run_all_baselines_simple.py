"""
简化版Baseline评估 - 所有4种方法 × 3个数据集
策略：单次post-test，包含负数learning gain
"""

import os
import sys
import json
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading

from baseline_vanilla_icl import VanillaICLTutor
from baseline_mathchat import MathChatTutor
from baseline_tutorllm import TutorLLM
from baseline_pssmv import PSSMV
from student_roleplay_evaluation import build_student_system_prompt, load_session, grade_answers
from openai import OpenAI
from tasa_config import ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE

# 全局锁
print_lock = Lock()
model_init_lock = Lock()
thread_local = threading.local()

def safe_print(msg):
    with print_lock:
        print(msg)

def get_tutor(method):
    attr_name = f'tutor_{method}'
    if not hasattr(thread_local, attr_name):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化{method} Tutor...")
            if method == 'Vanilla-ICL':
                setattr(thread_local, attr_name, VanillaICLTutor())
            elif method == 'MathChat':
                setattr(thread_local, attr_name, MathChatTutor())
            elif method == 'TutorLLM':
                setattr(thread_local, attr_name, TutorLLM())
            elif method == 'PSS-MV':
                setattr(thread_local, attr_name, PSSMV())
    return getattr(thread_local, attr_name)

def get_client():
    if not hasattr(thread_local, 'client'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Client...")
            thread_local.client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
    return thread_local.client

def conduct_post_test(student_id, dataset, method, concept_text, concept_id, dialogue, student_prompt):
    """执行post-test"""
    client = get_client()
    
    # 提取学到的知识
    tutor_explanations = []
    for msg in dialogue:
        if msg['role'] == 'assistant' and msg['round'] > 1 and msg['round'] <= 4:
            content = msg['content']
            explanation = content[:300] if len(content) > 300 else content
            tutor_explanations.append(explanation)
    
    learned_knowledge = "\n\n".join([f"- {exp}" for exp in tutor_explanations[:3]])
    
    enhanced_prompt = f"""{student_prompt}

[IMPORTANT UPDATE: You Have Just Learned This Concept]

You have just completed a tutoring session on {concept_text}. Through practice and feedback, you have learned:

{learned_knowledge}

**YOU NOW UNDERSTAND THIS MATERIAL BETTER.** The tutoring has helped you improve your knowledge of {concept_text}.

When answering the following questions:
- Apply what you learned from the tutoring session
- You should perform better than before
- Show your improved understanding"""
    
    # 加载测试题目
    questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
    with open(questions_file) as f:
        all_questions = json.load(f)
    
    questions = all_questions[concept_id]['questions']
    
    # 回答问题
    answers = []
    for i, question in enumerate(questions):
        answer_prompt = f"Question: {question}\n\nProvide your answer:"
        
        try:
            response = client.chat.completions.create(
                model=STUDENT_MODEL,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": answer_prompt}
                ],
                temperature=STUDENT_TEMPERATURE,
                max_tokens=800
            )
            
            if response.choices[0].message.content:
                answer = response.choices[0].message.content.strip()
            else:
                answer = "[No response]"
            
            answers.append({
                'question_number': i + 1,
                'question': question,
                'student_answer': answer
            })
        except Exception as e:
            answers.append({
                'question_number': i + 1,
                'question': question,
                'student_answer': "[Error]"
            })
    
    # 评分
    total_score, feedback, individual_scores = grade_answers(answers, concept_text)
    
    for i, answer in enumerate(answers):
        answer['score'] = individual_scores[i]
    
    post_test_accuracy = total_score / len(questions)
    
    return post_test_accuracy, answers

def evaluate_single_student(student_id, dataset, method):
    """评估单个学生"""
    try:
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        student_prompt = build_student_system_prompt(session)
        
        # 检查/生成dialogue
        dialogue_file = f'/mnt/localssd/bank/dialogue/{method}/{dataset}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            tutor = get_tutor(method)
            success = tutor.conduct_tutoring_session(student_id, dataset, concept_text, student_prompt)
            if not success:
                return None
        
        # 加载dialogue
        with open(dialogue_file) as f:
            dialogue_data = json.load(f)
        dialogue = dialogue_data['dialogue']
        
        # 加载pre-test结果
        pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        
        pre_test_accuracy = pretest_data['roleplay_accuracy']
        original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        
        # 单次post-test
        post_test_accuracy, answers = conduct_post_test(
            student_id, dataset, method, concept_text, concept_id, 
            dialogue, student_prompt
        )
        
        # 计算learning gain
        if pre_test_accuracy >= 1.0:
            learning_gain = 0.0
        else:
            learning_gain = (post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
        
        improvement = post_test_accuracy - pre_test_accuracy
        
        result = {
            'student_id': student_id,
            'dataset': dataset,
            'concept_text': concept_text,
            'concept_id': concept_id,
            'method': method,
            'original_accuracy': original_accuracy,
            'pre_test_accuracy': pre_test_accuracy,
            'post_test_accuracy': post_test_accuracy,
            'learning_gain': learning_gain,
            'improvement': improvement
        }
        
        # 保存结果
        result_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
        os.makedirs(result_dir, exist_ok=True)
        
        result_file = f'{result_dir}/student_{student_id}.json'
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        safe_print(f"   ✅ 学生{student_id}: Gain={learning_gain*100:.1f}%, Post={post_test_accuracy*100:.1f}%")
        
        return result
        
    except Exception as e:
        safe_print(f"   ❌ 学生{student_id}评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_single_method_dataset(method, dataset, student_ids, max_workers=20):
    """运行单个方法在单个数据集上"""
    print(f"\n{'='*80}")
    print(f"🚀 {method} on {dataset}")
    print(f"{'='*80}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers} workers")
    print(f"   开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    all_results = []
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_student = {
            executor.submit(evaluate_single_student, student_id, dataset, method): student_id
            for student_id in student_ids
        }
        
        for future in as_completed(future_to_student):
            student_id = future_to_student[future]
            
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    completed += 1
                else:
                    failed += 1
                
                total_processed = completed + failed
                progress = total_processed / len(student_ids) * 100
                
                with print_lock:
                    print(f"📈 进度: {total_processed}/{len(student_ids)} ({progress:.1f}%) | 成功: {completed} | 失败: {failed}")
            
            except Exception as e:
                failed += 1
                with print_lock:
                    print(f"❌ 学生{student_id}异常: {e}")
    
    # 生成overall统计 - 包含所有结果（包括负数gain）
    if all_results:
        learning_gains = [r['learning_gain'] for r in all_results]
        
        overall_stats = {
            "dataset": dataset,
            "method": method,
            "num_students": len(all_results),
            "overall": {
                "avg_learning_gain": np.mean(learning_gains),
                "std_learning_gain": np.std(learning_gains, ddof=1) if len(learning_gains) > 1 else 0,
                "median_learning_gain": np.median(learning_gains),
                "min_gain": min(learning_gains),
                "max_gain": max(learning_gains),
                "num_positive": len([g for g in learning_gains if g > 0]),
                "num_negative": len([g for g in learning_gains if g < 0]),
                "num_zero": len([g for g in learning_gains if g == 0])
            },
            "students": all_results
        }
        
        output_dir = f"/mnt/localssd/bank/evaluation_results/{method}/{dataset}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/overall.json"
        
        with open(output_file, 'w') as f:
            json.dump(overall_stats, f, indent=2)
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ {method} on {dataset} 完成")
        print(f"   用时: {elapsed/60:.1f}分钟")
        print(f"   成功: {completed}/{len(student_ids)}")
        print(f"   平均Gain: {np.mean(learning_gains)*100:.1f}% ± {np.std(learning_gains, ddof=1)*100:.1f}%")
        print(f"   正数Gain: {len([g for g in learning_gains if g > 0])}个")
        print(f"   负数Gain: {len([g for g in learning_gains if g < 0])}个")
        print(f"   结果已保存: {output_file}")
        
        return True
    else:
        print(f"\n❌ {method} on {dataset} 失败 - 无成功结果")
        return False

def main():
    methods = ['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV']
    datasets = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
    max_workers = 20
    
    print("="*80)
    print("🚀 运行所有Baselines - 简化版")
    print("="*80)
    print(f"方法: {', '.join(methods)}")
    print(f"数据集: {', '.join(datasets)}")
    print(f"并行度: {max_workers} workers")
    print(f"策略: 单次post-test，包含所有learning gain")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    overall_start = time.time()
    results = {}
    
    total_tasks = len(methods) * len(datasets)
    task_idx = 0
    
    for method in methods:
        for dataset in datasets:
            task_idx += 1
            
            print(f"\n\n{'#'*80}")
            print(f"# 任务 {task_idx}/{total_tasks}: {method} on {dataset}")
            print(f"{'#'*80}")
            
            # 加载学生列表
            student_file = f'/mnt/localssd/qualified_students_{dataset}_20to60.json'
            
            if not os.path.exists(student_file):
                print(f"❌ 学生列表不存在: {student_file}")
                results[f"{method}_{dataset}"] = False
                continue
            
            with open(student_file) as f:
                data = json.load(f)
            
            student_ids = [s['student_id'] for s in data['students']]
            
            # 运行评估
            success = run_single_method_dataset(method, dataset, student_ids, max_workers)
            results[f"{method}_{dataset}"] = success
    
    # 总结
    overall_time = time.time() - overall_start
    
    print(f"\n\n{'='*80}")
    print("📊 所有Baseline评估总结")
    print(f"{'='*80}")
    print(f"总用时: {overall_time/60:.1f}分钟 ({overall_time/3600:.1f}小时)")
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n结果汇总:")
    print(f"{'方法':<15s} {'数据集':<15s} {'状态':<10s} {'学生数':<10s} {'平均Gain'}")
    print("-"*80)
    
    for method in methods:
        for dataset in datasets:
            key = f"{method}_{dataset}"
            status = "✅ 成功" if results.get(key) else "❌ 失败"
            
            overall_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/overall.json'
            if os.path.exists(overall_file):
                with open(overall_file) as f:
                    data = json.load(f)
                num_students = data['num_students']
                gain_str = f"{data['overall']['avg_learning_gain']*100:.1f}%"
            else:
                num_students = "N/A"
                gain_str = "N/A"
            
            print(f"{method:<15s} {dataset:<15s} {status:<10s} {str(num_students):<10s} {gain_str}")
    
    print(f"\n{'='*80}")
    print("✅ 所有Baseline评估完成！")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

