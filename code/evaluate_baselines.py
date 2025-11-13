"""
统一的Baseline评估脚本
支持所有4种baseline方法的评估
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading

# 导入baseline模块
from baseline_vanilla_icl import VanillaICLTutor
from baseline_mathchat import MathChatTutor
from baseline_tutorllm import TutorLLM
from baseline_pssmv import PSSMV

# 导入评估模块
from student_roleplay_evaluation import build_student_system_prompt, load_session, grade_answers
from openai import OpenAI
from tasa_config import ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE

# 全局锁和线程本地存储
print_lock = Lock()
model_init_lock = Lock()
thread_local = threading.local()

def safe_print(msg):
    """线程安全的打印"""
    with print_lock:
        print(msg)

def get_tutor(method):
    """获取线程本地的tutor实例"""
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
    """获取线程本地的OpenAI client"""
    if not hasattr(thread_local, 'client'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化OpenAI Client...")
            thread_local.client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
    return thread_local.client

def conduct_post_test(student_id: int, dataset: str, method: str) -> dict:
    """
    进行post-test评估
    
    Returns:
        {
            'post_test_accuracy': float,
            'learning_gain': float,
            'improvement': float
        }
    """
    # 加载session
    session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
    session = load_session(session_file)
    
    concept_text = session['concept_text']
    concept_id = str(session['concept_id'])
    
    # 加载dialogue
    dialogue_file = f'/mnt/localssd/bank/dialogue/{method}/{dataset}/{student_id}-{concept_text}.json'
    
    if not os.path.exists(dialogue_file):
        safe_print(f"   ❌ Dialogue不存在")
        return None
    
    with open(dialogue_file) as f:
        dialogue_data = json.load(f)
    
    dialogue = dialogue_data['dialogue']
    
    # 加载pre-test结果
    pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
    with open(pretest_file) as f:
        pretest_data = json.load(f)
    
    pre_test_accuracy = pretest_data['roleplay_accuracy']
    
    # 构建student prompt
    student_prompt = build_student_system_prompt(session)
    
    # 提取学到的知识（前3个tutor回复）
    tutor_explanations = []
    for msg in dialogue:
        if msg['role'] == 'assistant' and msg['round'] > 1 and msg['round'] <= 4:
            content = msg['content']
            explanation = content[:300] if len(content) > 300 else content
            tutor_explanations.append(explanation)
    
    learned_knowledge = "\n\n".join([f"- {exp}" for exp in tutor_explanations[:3]])
    
    # Post-test prompt
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
    
    # 获取client
    client = get_client()
    
    # 让学生回答问题
    answers = []
    for i, question in enumerate(questions):
        safe_print(f"   问题 {i+1}/{len(questions)}")
        
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
            safe_print(f"   ⚠️ 问题{i+1}回答失败: {e}")
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
    
    # 计算learning gain
    if pre_test_accuracy >= 1.0:
        learning_gain = 0.0
    else:
        learning_gain = (post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
    
    improvement = post_test_accuracy - pre_test_accuracy
    
    safe_print(f"   ✅ Post-test准确率: {post_test_accuracy*100:.1f}%")
    safe_print(f"   Post-test (有教学): {post_test_accuracy*100:.1f}%")
    
    return {
        'post_test_accuracy': post_test_accuracy,
        'learning_gain': learning_gain,
        'improvement': improvement,
        'answers': answers
    }

def evaluate_single_student(student_id: int, dataset: str, method: str) -> dict:
    """
    评估单个学生
    
    Returns:
        完整的评估结果
    """
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"📊 评估学生 {student_id} - {method}")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        student_prompt = build_student_system_prompt(session)
        
        # 检查dialogue是否存在
        dialogue_file = f'/mnt/localssd/bank/dialogue/{method}/{dataset}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   📝 生成dialogue...")
            tutor = get_tutor(method)
            success = tutor.conduct_tutoring_session(student_id, dataset, concept_text, student_prompt)
            
            if not success:
                safe_print(f"   ❌ Dialogue生成失败")
                return None
        else:
            safe_print(f"   ✅ Dialogue已存在")
        
        # 进行post-test
        safe_print(f"   📊 进行Post-test评估")
        
        result = conduct_post_test(student_id, dataset, method)
        
        if not result:
            return None
        
        # 加载pre-test结果
        pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        
        # 计算历史准确率
        original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        pre_test_accuracy = pretest_data['roleplay_accuracy']
        
        # 组合结果
        full_result = {
            'student_id': student_id,
            'dataset': dataset,
            'concept_text': concept_text,
            'concept_id': concept_id,
            'method': method,
            'original_accuracy': original_accuracy,
            'pre_test_accuracy': pre_test_accuracy,
            'post_test_accuracy': result['post_test_accuracy'],
            'learning_gain': result['learning_gain'],
            'improvement': result['improvement']
        }
        
        # 保存结果
        result_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
        os.makedirs(result_dir, exist_ok=True)
        
        result_file = f'{result_dir}/student_{student_id}.json'
        with open(result_file, 'w') as f:
            json.dump(full_result, f, indent=2)
        
        safe_print(f"   ✅ 学生{student_id}评估完成: Gain={result['learning_gain']*100:.1f}%")
        
        return full_result
        
    except Exception as e:
        safe_print(f"   ❌ 学生{student_id}评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_batch_evaluation(student_ids, dataset, method, max_workers=10):
    """批量评估"""
    print("="*80)
    print(f"🚀 {method} 批量评估")
    print("="*80)
    print(f"   数据集: {dataset}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers} workers")
    print("="*80)
    
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
                    print(f"\n📈 进度: {total_processed}/{len(student_ids)} ({progress:.1f}%) | 成功: {completed} | 失败: {failed}")
                
            except Exception as e:
                failed += 1
                with print_lock:
                    print(f"\n❌ 学生{student_id}处理异常: {e}")
    
    # 生成overall统计
    if all_results:
        generate_overall_stats(all_results, dataset, method)
    
    elapsed = time.time() - start_time
    print(f"\n✅ 批量评估完成！")
    print(f"   总用时: {elapsed/60:.1f}分钟")
    print(f"   成功: {completed}/{len(student_ids)}")
    
    return all_results

def generate_overall_stats(results, dataset, method):
    """生成overall统计"""
    print(f"\n{'='*80}")
    print(f"📊 生成整体统计")
    print(f"{'='*80}")
    
    # 计算统计
    learning_gains = [r['learning_gain'] for r in results]
    avg_gain = np.mean(learning_gains)
    std_gain = np.std(learning_gains, ddof=1) if len(learning_gains) > 1 else 0
    median_gain = np.median(learning_gains)
    
    overall_stats = {
        "dataset": dataset,
        "method": method,
        "num_students": len(results),
        "overall": {
            "avg_learning_gain": avg_gain,
            "std_learning_gain": std_gain,
            "median_learning_gain": median_gain,
            "min_gain": min(learning_gains),
            "max_gain": max(learning_gains)
        },
        "students": results
    }
    
    # 保存
    output_dir = f"/mnt/localssd/bank/evaluation_results/{method}/{dataset}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/overall.json"
    
    with open(output_file, 'w') as f:
        json.dump(overall_stats, f, indent=2)
    
    print(f"\n📊 整体统计:")
    print(f"   学生数: {len(results)}")
    print(f"   平均Learning Gain: {avg_gain*100:.1f}% ± {std_gain*100:.1f}%")
    print(f"   中位数: {median_gain*100:.1f}%")
    print(f"   范围: [{min(learning_gains)*100:.1f}%, {max(learning_gains)*100:.1f}%]")
    
    print(f"\n💾 结果已保存: {output_file}")
    
    return overall_stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='评估Baseline方法')
    parser.add_argument('--method', type=str, required=True,
                       choices=['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV'],
                       help='Baseline方法')
    parser.add_argument('--dataset', type=str, required=True,
                       help='数据集名称')
    parser.add_argument('--max-workers', type=int, default=10,
                       help='并行度')
    parser.add_argument('--test', action='store_true',
                       help='测试模式（只评估前3个学生）')
    
    args = parser.parse_args()
    
    # 读取符合条件的学生
    student_file = f'/mnt/localssd/qualified_students_{args.dataset}_20to60.json'
    
    if not os.path.exists(student_file):
        print(f"❌ 学生列表不存在: {student_file}")
        sys.exit(1)
    
    with open(student_file) as f:
        data = json.load(f)
    
    student_ids = [s['student_id'] for s in data['students']]
    
    if args.test:
        student_ids = student_ids[:3]
        print(f"🧪 测试模式：只评估前3个学生")
    
    print(f"将评估 {len(student_ids)} 个学生")
    
    # 运行评估
    results = run_batch_evaluation(student_ids, args.dataset, args.method, args.max_workers)
    
    print(f"\n✅ {args.method} 评估完成！")

