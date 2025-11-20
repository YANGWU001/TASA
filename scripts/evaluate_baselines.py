"""
保守版本的Baseline评估
- 运行2次post-test，使用平均分（不是最高分）
- 包含负数learning gain（不排除）
- 支持多线程并行
"""

import os
import sys
import json
import time
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

# 根据环境变量选择配置文件
_config_module = os.environ.get('TASA_CONFIG', 'tasa_config')
if _config_module == 'tasa_config_llama':
    from tasa_config_llama import ENDPOINT, GPT_ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE, TUTOR_MODEL
elif _config_module == 'tasa_config_qwen':
    from tasa_config_qwen import ENDPOINT, GPT_ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE, TUTOR_MODEL
elif _config_module == 'tasa_config_gpt':
    from tasa_config_gpt import ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE, TUTOR_MODEL
    GPT_ENDPOINT = ENDPOINT
else:
    from tasa_config import ENDPOINT, API_KEY, STUDENT_MODEL, STUDENT_TEMPERATURE, TUTOR_MODEL
    GPT_ENDPOINT = ENDPOINT

def get_backbone_suffix():
    """根据TUTOR_MODEL确定backbone后缀"""
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''  # GPT默认无后缀

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
    """获取线程本地的OpenAI client (用于Student roleplay，固定使用GPT)"""
    if not hasattr(thread_local, 'client'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化OpenAI Client (GPT)...")
            safe_print(f"   [Thread-{threading.current_thread().ident}] GPT_ENDPOINT={GPT_ENDPOINT}")
            safe_print(f"   [Thread-{threading.current_thread().ident}] STUDENT_MODEL={STUDENT_MODEL}")
            thread_local.client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
    return thread_local.client

def conduct_post_test_single_run(student_id: int, dataset: str, method: str, 
                                  dialogue: list, concept_text: str, 
                                  concept_id: str, student_prompt: str) -> float:
    """
    进行单次post-test评估
    
    Returns:
        post_test_accuracy: float
    """
    # 获取client
    client = get_client()
    
    # 提取学到的知识（前3个tutor回复）
    tutor_explanations = []
    for msg in dialogue:
        if msg['role'] == 'assistant' and msg['round'] > 1 and msg['round'] <= 4:
            content = msg['content']
            explanation = content[:300] if len(content) > 300 else content
            tutor_explanations.append(explanation)
    
    learned_knowledge = "\n\n".join([f"- {exp}" for exp in tutor_explanations[:3]])
    
    # Post-test prompt (平衡版本：有进步但未完全掌握)
    enhanced_prompt = f"""{student_prompt}

[IMPORTANT UPDATE: You Have Just Had a Tutoring Session]

You have just completed a tutoring session on {concept_text}. The tutor covered:

{learned_knowledge}

**Your understanding has IMPROVED, but is NOT complete.** The tutoring session was helpful:
- You learned some of the key concepts
- You can now solve SOME problems better than before
- However, you still struggle with certain aspects
- Your mastery is MODERATE, not full

When answering the following questions:
- Apply what you learned from the tutoring session
- You should perform SOMEWHAT better than before
- You may get some questions right that you couldn't before
- But you will still make mistakes on harder questions
- Show moderate improvement with continued uncertainty on complex problems"""
    
    # 加载测试题目
    questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
    with open(questions_file) as f:
        all_questions = json.load(f)
    
    questions = all_questions[concept_id]['questions']
    
    # 让学生回答问题
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
    post_test_accuracy = total_score / len(questions)
    
    return post_test_accuracy

def evaluate_single_student_conservative(student_id: int, dataset: str, method: str) -> dict:
    """
    评估单个学生（保守版本：2次post-test取平均）
    """
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"📊 评估学生 {student_id} - {method} - {dataset}")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        student_prompt = build_student_system_prompt(session)
        
        # 检查dialogue是否存在（根据backbone确定路径）
        backbone_suffix = get_backbone_suffix()
        dialogue_file = f'/mnt/localssd/bank/dialogue/{method}{backbone_suffix}/{dataset}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   📝 生成dialogue...")
            tutor = get_tutor(method)
            success = tutor.conduct_tutoring_session(student_id, dataset, concept_text, student_prompt)
            
            if not success:
                safe_print(f"   ❌ Dialogue生成失败")
                return None
        else:
            safe_print(f"   ✅ Dialogue已存在")
        
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
        
        # 进行2次post-test
        safe_print(f"   📊 进行Post-test评估 (2次)")
        
        post_test_results = []
        for run_id in range(1, 3):
            safe_print(f"   Run {run_id}/2")
            post_acc = conduct_post_test_single_run(
                student_id, dataset, method, dialogue, 
                concept_text, concept_id, student_prompt
            )
            post_test_results.append(post_acc)
            safe_print(f"   Run {run_id} 准确率: {post_acc*100:.1f}%")
        
        # 计算平均post-test准确率
        avg_post_test_accuracy = np.mean(post_test_results)
        
        # 计算最低post-test准确率（最保守策略）
        min_post_test_accuracy = min(post_test_results)
        
        # 计算最高post-test准确率（最激进策略）
        max_post_test_accuracy = max(post_test_results)
        
        # 计算learning gain（包含负数）- 基于平均分
        if pre_test_accuracy >= 1.0:
            learning_gain_avg = 0.0
        else:
            learning_gain_avg = (avg_post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
        
        # 计算learning gain（包含负数）- 基于最低分
        if pre_test_accuracy >= 1.0:
            learning_gain_min = 0.0
        else:
            learning_gain_min = (min_post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
        
        # 计算learning gain（包含负数）- 基于最高分
        if pre_test_accuracy >= 1.0:
            learning_gain_max = 0.0
        else:
            learning_gain_max = (max_post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
        
        improvement_avg = avg_post_test_accuracy - pre_test_accuracy
        improvement_min = min_post_test_accuracy - pre_test_accuracy
        improvement_max = max_post_test_accuracy - pre_test_accuracy
        
        safe_print(f"   ✅ 最高Post-test: {max_post_test_accuracy*100:.1f}% (Gain={learning_gain_max*100:.1f}%)")
        safe_print(f"   ✅ 平均Post-test: {avg_post_test_accuracy*100:.1f}% (Gain={learning_gain_avg*100:.1f}%)")
        safe_print(f"   ✅ 最低Post-test: {min_post_test_accuracy*100:.1f}% (Gain={learning_gain_min*100:.1f}%)")
        
        # 组合结果
        full_result = {
            'student_id': student_id,
            'dataset': dataset,
            'concept_text': concept_text,
            'concept_id': concept_id,
            'method': method,
            'original_accuracy': original_accuracy,
            'pre_test_accuracy': pre_test_accuracy,
            'post_test_run1': post_test_results[0],
            'post_test_run2': post_test_results[1],
            'max_post_test_accuracy': max_post_test_accuracy,
            'avg_post_test_accuracy': avg_post_test_accuracy,
            'min_post_test_accuracy': min_post_test_accuracy,
            'learning_gain_max': learning_gain_max,
            'learning_gain_avg': learning_gain_avg,
            'learning_gain_min': learning_gain_min,
            'improvement_max': improvement_max,
            'improvement_avg': improvement_avg,
            'improvement_min': improvement_min
        }
        
        # 保存结果（支持backbone后缀）
        backbone_suffix = globals().get('BACKBONE_SUFFIX', '')
        result_dir = f'/mnt/localssd/bank/evaluation_results/{method}-conservative{backbone_suffix}/{dataset}'
        os.makedirs(result_dir, exist_ok=True)
        
        result_file = f'{result_dir}/student_{student_id}.json'
        with open(result_file, 'w') as f:
            json.dump(full_result, f, indent=2)
        
        safe_print(f"   ✅ 学生{student_id}评估完成")
        
        return full_result
        
    except Exception as e:
        safe_print(f"   ❌ 学生{student_id}评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_batch_evaluation(student_ids, dataset, method, max_workers=20):
    """批量评估"""
    print("="*80)
    print(f"🚀 {method} 批量评估 (保守版本)")
    print("="*80)
    print(f"   数据集: {dataset}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers} workers")
    print(f"   策略: 2次post-test取平均，包含负数gain")
    print("="*80)
    
    start_time = time.time()
    
    all_results = []
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_student = {
            executor.submit(evaluate_single_student_conservative, student_id, dataset, method): student_id
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
    """生成overall统计（包含所有learning gain，不排除负数）"""
    print(f"\n{'='*80}")
    print(f"📊 生成整体统计")
    print(f"{'='*80}")
    
    # 计算统计（包含所有gain，不排除负数）
    # 基于最高分的统计
    all_learning_gains_max = [r['learning_gain_max'] for r in results]
    
    avg_gain_max = np.mean(all_learning_gains_max)
    std_gain_max = np.std(all_learning_gains_max, ddof=1) if len(all_learning_gains_max) > 1 else 0
    median_gain_max = np.median(all_learning_gains_max)
    
    negative_count_max = len([g for g in all_learning_gains_max if g < 0])
    positive_count_max = len([g for g in all_learning_gains_max if g >= 0])
    
    # 基于平均分的统计
    all_learning_gains_avg = [r['learning_gain_avg'] for r in results]
    
    avg_gain_avg = np.mean(all_learning_gains_avg)
    std_gain_avg = np.std(all_learning_gains_avg, ddof=1) if len(all_learning_gains_avg) > 1 else 0
    median_gain_avg = np.median(all_learning_gains_avg)
    
    negative_count_avg = len([g for g in all_learning_gains_avg if g < 0])
    positive_count_avg = len([g for g in all_learning_gains_avg if g >= 0])
    
    # 基于最低分的统计
    all_learning_gains_min = [r['learning_gain_min'] for r in results]
    
    avg_gain_min = np.mean(all_learning_gains_min)
    std_gain_min = np.std(all_learning_gains_min, ddof=1) if len(all_learning_gains_min) > 1 else 0
    median_gain_min = np.median(all_learning_gains_min)
    
    negative_count_min = len([g for g in all_learning_gains_min if g < 0])
    positive_count_min = len([g for g in all_learning_gains_min if g >= 0])
    
    overall_stats = {
        "dataset": dataset,
        "method": f"{method}-conservative",
        "num_students": len(results),
        "strategy_max": {
            "name": "最高分策略 (2次取最高)",
            "avg_learning_gain": avg_gain_max,
            "std_learning_gain": std_gain_max,
            "median_learning_gain": median_gain_max,
            "min_gain": min(all_learning_gains_max),
            "max_gain": max(all_learning_gains_max),
            "num_positive_gain": positive_count_max,
            "num_negative_gain": negative_count_max
        },
        "strategy_avg": {
            "name": "平均分策略 (2次取平均)",
            "avg_learning_gain": avg_gain_avg,
            "std_learning_gain": std_gain_avg,
            "median_learning_gain": median_gain_avg,
            "min_gain": min(all_learning_gains_avg),
            "max_gain": max(all_learning_gains_avg),
            "num_positive_gain": positive_count_avg,
            "num_negative_gain": negative_count_avg
        },
        "strategy_min": {
            "name": "最低分策略 (2次取最低)",
            "avg_learning_gain": avg_gain_min,
            "std_learning_gain": std_gain_min,
            "median_learning_gain": median_gain_min,
            "min_gain": min(all_learning_gains_min),
            "max_gain": max(all_learning_gains_min),
            "num_positive_gain": positive_count_min,
            "num_negative_gain": negative_count_min
        },
        "note": "包含三种策略：1) 2次最高分 2) 2次平均分 3) 2次最低分，均包含所有learning gain（含负数）",
        "students": results
    }
    
    # 保存（支持backbone后缀）
    backbone_suffix = globals().get('BACKBONE_SUFFIX', '')
    output_dir = f"/mnt/localssd/bank/evaluation_results/{method}-conservative{backbone_suffix}/{dataset}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/overall.json"
    
    with open(output_file, 'w') as f:
        json.dump(overall_stats, f, indent=2)
    
    print(f"\n📊 整体统计 (包含所有数据):")
    print(f"   学生数: {len(results)}")
    print(f"\n   🔹 策略1: 最高分 (2次取最高) - 最激进")
    print(f"      平均Learning Gain: {avg_gain_max*100:.1f}% ± {std_gain_max*100:.1f}%")
    print(f"      中位数: {median_gain_max*100:.1f}%")
    print(f"      范围: [{min(all_learning_gains_max)*100:.1f}%, {max(all_learning_gains_max)*100:.1f}%]")
    print(f"      正增长: {positive_count_max}个 | 负增长: {negative_count_max}个")
    
    print(f"\n   🔹 策略2: 平均分 (2次取平均)")
    print(f"      平均Learning Gain: {avg_gain_avg*100:.1f}% ± {std_gain_avg*100:.1f}%")
    print(f"      中位数: {median_gain_avg*100:.1f}%")
    print(f"      范围: [{min(all_learning_gains_avg)*100:.1f}%, {max(all_learning_gains_avg)*100:.1f}%]")
    print(f"      正增长: {positive_count_avg}个 | 负增长: {negative_count_avg}个")
    
    print(f"\n   🔹 策略3: 最低分 (2次取最低) - 最保守")
    print(f"      平均Learning Gain: {avg_gain_min*100:.1f}% ± {std_gain_min*100:.1f}%")
    print(f"      中位数: {median_gain_min*100:.1f}%")
    print(f"      范围: [{min(all_learning_gains_min)*100:.1f}%, {max(all_learning_gains_min)*100:.1f}%]")
    print(f"      正增长: {positive_count_min}个 | 负增长: {negative_count_min}个")
    
    print(f"\n💾 结果已保存: {output_file}")
    
    return overall_stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='保守版本Baseline评估')
    parser.add_argument('--method', type=str, required=True,
                       choices=['Vanilla-ICL', 'MathChat', 'TutorLLM', 'PSS-MV'],
                       help='Baseline方法')
    parser.add_argument('--dataset', type=str, required=True,
                       help='数据集名称')
    parser.add_argument('--max-workers', type=int, default=20,
                       help='并行度')
    parser.add_argument('--students-file', type=str, default=None,
                       help='学生文件路径（可选，默认使用20to60文件）')
    parser.add_argument('--backbone-suffix', type=str, default='',
                       help='Backbone后缀（如-llama, -qwen），用于区分不同LLM的结果')
    
    args = parser.parse_args()
    
    # 设置全局变量供evaluate_single_student_conservative使用
    globals()['BACKBONE_SUFFIX'] = args.backbone_suffix
    
    # 读取符合条件的学生
    if args.students_file:
        student_file = args.students_file
    else:
        student_file = f'/mnt/localssd/qualified_students_{args.dataset}_20to60.json'
    
    if not os.path.exists(student_file):
        print(f"❌ 学生列表不存在: {student_file}")
        sys.exit(1)
    
    with open(student_file) as f:
        data = json.load(f)
    
    # 兼容不同格式的学生文件
    if 'sampled_students' in data:
        student_ids = data['sampled_students']
    elif 'students' in data:
        if isinstance(data['students'][0], dict):
            student_ids = [s['student_id'] for s in data['students']]
        else:
            student_ids = data['students']
    else:
        print(f"❌ 无法读取学生ID from {student_file}")
        sys.exit(1)
    
    print(f"将评估 {len(student_ids)} 个学生")
    
    # 运行评估
    results = run_batch_evaluation(student_ids, args.dataset, args.method, args.max_workers)
    
    print(f"\n✅ {args.method}-conservative 评估完成！")

