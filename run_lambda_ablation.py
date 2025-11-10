#!/usr/bin/env python3
"""
TASA Lambda Ablation Study
测试不同lambda值对TASA性能的影响
数据集：Assist2017
Backbones：Llama, Qwen, GPT-oss-120b
Lambda values：[0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
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
from tasa_rag_lambda import TASARAGLambda
from tasa_rewrite import MasteryRewriter
from tasa_evaluation_best_of_two import TASABestOfTwoEvaluator
from llm_client_unified import UnifiedLLMClient
from openai import OpenAI

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

def get_tutor_with_lambda(lambda_value, backbone):
    """获取线程本地的带指定lambda的Tutor实例"""
    tutor_key = f'tutor_lambda{lambda_value}_{backbone}'
    if not hasattr(thread_local, tutor_key):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化TASA Tutor (Lambda={lambda_value}, {backbone})...")
            
            # 动态导入对应backbone的config
            if backbone == 'llama':
                from tasa_config_llama import TUTOR_MODEL
            elif backbone == 'qwen':
                from tasa_config_qwen import TUTOR_MODEL
            elif backbone == 'gpt':
                from tasa_config_gpt import TUTOR_MODEL
            else:
                raise ValueError(f"Unknown backbone: {backbone}")
            
            # Student、Grader、Rewriter固定使用GPT（不随backbone变化）
            from tasa_config import API_KEY, GPT_ENDPOINT, STUDENT_MODEL as FIXED_STUDENT_MODEL
            
            # 创建自定义Tutor（带lambda参数）
            class TASATutorLambda:
                def __init__(self, lambda_value):
                    # Tutor使用指定backbone
                    self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
                    # Student固定使用GPT
                    self.openai_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
                    self.student_model = FIXED_STUDENT_MODEL
                    self.rag = TASARAGLambda(lambda_weight=lambda_value)
                    self.rewriter = MasteryRewriter()
                    self.lambda_value = lambda_value
                    self.backbone = backbone
                    self.tutor_model = TUTOR_MODEL
                
                def generate_first_question(self, rewritten_persona, rewritten_memory, concept_text):
                    from tasa_config import TUTOR_TEMPERATURE, MAX_TOKENS_TUTOR
                    system_message = "You are a personalized math tutor."
                    user_message = f"""[Student Profile]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Recent Learning Events]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Student Request]
The student wants to learn about: {concept_text}

[Task]
Generate an appropriate first practice question."""
                    
                    try:
                        content = self.tutor_client.chat_completion(
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_message}
                            ],
                            temperature=TUTOR_TEMPERATURE,
                            max_tokens=MAX_TOKENS_TUTOR
                        )
                        return content.strip() if content else "Let's start."
                    except Exception as e:
                        safe_print(f"⚠️ 生成问题失败: {e}")
                        return "Let's begin."
                
                def generate_explanation_and_question(self, rewritten_persona, rewritten_memory, conversation_history, concept_text):
                    from tasa_config import TUTOR_TEMPERATURE, MAX_TOKENS_TUTOR
                    system_message = "You are a personalized math tutor."
                    
                    history_text = "\n".join([
                        f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
                        for msg in conversation_history[-4:]
                    ])
                    
                    user_message = f"""[Student Profile]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Recent Learning Events]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Current Dialogue]
{history_text}

[Task]
Provide explanation and next question."""
                    
                    try:
                        content = self.tutor_client.chat_completion(
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_message}
                            ],
                            temperature=TUTOR_TEMPERATURE,
                            max_tokens=MAX_TOKENS_TUTOR
                        )
                        return content.strip() if content else "Let's continue."
                    except Exception as e:
                        safe_print(f"⚠️ 生成讲解失败: {e}")
                        return "Let's move on."
                
                def get_student_response(self, question, student_prompt):
                    # Student固定使用GPT，不随backbone变化
                    from tasa_config import STUDENT_TEMPERATURE, MAX_TOKENS_STUDENT
                    try:
                        response = self.openai_client.chat.completions.create(
                            model=self.student_model,  # 固定使用GPT
                            messages=[
                                {"role": "system", "content": student_prompt},
                                {"role": "user", "content": question}
                            ],
                            temperature=STUDENT_TEMPERATURE,
                            max_tokens=MAX_TOKENS_STUDENT
                        )
                        content = response.choices[0].message.content
                        return content.strip() if content else "I'm not sure."
                    except Exception as e:
                        safe_print(f"⚠️ 获取学生回答失败: {e}")
                        return "I'm not sure."
                
                def conduct_tutoring_session(self, student_id, dataset, concept_text, student_system_prompt):
                    from tasa_config import NUM_TUTORING_ROUNDS
                    dialogue = []
                    
                    initial_query = f"I want to learn about {concept_text}"
                    dialogue.append({"role": "user", "round": 0, "content": initial_query})
                    
                    # 使用自定义lambda的RAG检索
                    top_persona, top_memory = self.rag.retrieve_and_rerank(
                        query=initial_query,
                        student_id=student_id,
                        dataset=dataset,
                        concept_text=concept_text
                    )
                    
                    rewritten_persona, rewritten_memory = self.rewriter.rewrite_top_items(
                        top_persona, top_memory,
                        student_id=student_id,
                        dataset=dataset,
                        concept_text=concept_text
                    )
                    
                    first_question = self.generate_first_question(rewritten_persona, rewritten_memory, concept_text)
                    
                    dialogue.append({
                        "role": "assistant",
                        "round": 1,
                        "content": first_question,
                        "retrieved_persona": [p['description'] for p in top_persona],
                        "retrieved_memory": [m['description'] for m in top_memory],
                        "rewritten_persona": rewritten_persona,
                        "rewritten_memory": rewritten_memory,
                        "lambda_value": self.lambda_value
                    })
                    
                    for round_num in range(2, NUM_TUTORING_ROUNDS + 1):
                        last_question = dialogue[-1]['content']
                        student_answer = self.get_student_response(last_question, student_system_prompt)
                        
                        dialogue.append({"role": "user", "round": round_num, "content": student_answer})
                        
                        top_persona, top_memory = self.rag.retrieve_and_rerank(
                            query=student_answer,
                            student_id=student_id,
                            dataset=dataset,
                            concept_text=concept_text
                        )
                        
                        rewritten_persona, rewritten_memory = self.rewriter.rewrite_top_items(
                            top_persona, top_memory,
                            student_id=student_id,
                            dataset=dataset,
                            concept_text=concept_text
                        )
                        
                        conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                               for msg in dialogue]
                        
                        explanation_and_question = self.generate_explanation_and_question(
                            rewritten_persona, rewritten_memory, conversation_history, concept_text
                        )
                        
                        dialogue.append({
                            "role": "assistant",
                            "round": round_num,
                            "content": explanation_and_question,
                            "retrieved_persona": [p['description'] for p in top_persona],
                            "retrieved_memory": [m['description'] for m in top_memory],
                            "rewritten_persona": rewritten_persona,
                            "rewritten_memory": rewritten_memory,
                            "lambda_value": self.lambda_value
                        })
                    
                    return dialogue
                
                def save_dialogue(self, dialogue, student_id, concept_text, dataset, backbone_suffix=''):
                    from tasa_config import FORGETTING_SCORE_METHOD
                    save_dir = f'/mnt/localssd/bank/dialogue/TASA-lambda{self.lambda_value}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
                    os.makedirs(save_dir, exist_ok=True)
                    
                    save_file = f'{save_dir}/{student_id}-{concept_text}.json'
                    with open(save_file, 'w') as f:
                        json.dump(dialogue, f, indent=2)
            
            tutor = TASATutorLambda(lambda_value)
            setattr(thread_local, tutor_key, tutor)
    
    return getattr(thread_local, tutor_key)

def get_backbone_suffix(backbone):
    """获取backbone后缀"""
    if backbone == 'llama':
        return '-llama'
    elif backbone == 'qwen':
        return '-qwen'
    elif backbone == 'gpt':
        return '-gpt'
    else:
        return ''

def get_evaluator():
    """获取线程本地的Evaluator实例"""
    if not hasattr(thread_local, 'evaluator'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Evaluator...")
            thread_local.evaluator = TASABestOfTwoEvaluator()
    return thread_local.evaluator

def process_single_student(student_id, dataset, lambda_value, backbone):
    """处理单个学生"""
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🎓 开始处理学生 {student_id} (Lambda={lambda_value}, {backbone})")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        
        # 检查dialogue
        from tasa_config import FORGETTING_SCORE_METHOD
        backbone_suffix = get_backbone_suffix(backbone)
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA-lambda{lambda_value}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(dialogue_file):
            safe_print(f"   📚 正在生成dialogue (Lambda={lambda_value})...")
            student_prompt = build_student_system_prompt(session)
            
            tutor = get_tutor_with_lambda(lambda_value, backbone)
            
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
            safe_print(f"   ✅ Dialogue已存在")
        
        # Post-test评估
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

def batch_evaluate(lambda_value, backbone, dataset='assist2017', max_workers=10):
    """批量评估"""
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    
    with open(students_file) as f:
        students_data = json.load(f)
    
    if isinstance(students_data, list):
        student_ids = students_data
    elif isinstance(students_data, dict):
        # 尝试多个可能的key
        if 'student_ids' in students_data:
            student_ids = students_data['student_ids']
        elif 'sampled_students' in students_data:
            student_ids = students_data['sampled_students']
        else:
            print(f"❌ 无法解析students文件: 找不到student_ids或sampled_students")
            return None
    else:
        print(f"❌ 无法解析students文件: 未知格式")
        return None
    
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║     📊 Lambda Ablation: λ={lambda_value}, {backbone.upper()}, {dataset}       ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers}")
    print(f"{'='*80}\n")
    
    all_results = []
    successful_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_student, sid, dataset, lambda_value, backbone): sid 
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
                
                total_processed = successful_count + failed_count
                safe_print(f"\n📈 进度: {total_processed}/{len(student_ids)} ({total_processed*100/len(student_ids):.1f}%) | 成功: {successful_count} | 失败: {failed_count}")
                
            except Exception as e:
                safe_print(f"❌ 处理学生{sid}异常: {e}")
                failed_count += 1
    
    # 统计
    print(f"\n{'='*80}")
    print(f"\n📊 整体统计 (Lambda={lambda_value}, {backbone}):")
    
    if all_results:
        learning_gains_max = [r['best_learning_gain'] for r in all_results]
        print(f"\n   策略1: 最高分 (2次取最高)")
        print(f"      平均Learning Gain: {np.mean(learning_gains_max)*100:.1f}% ± {np.std(learning_gains_max)*100:.1f}%")
        print(f"      中位数: {np.median(learning_gains_max)*100:.1f}%")
    
    print(f"\n✅ 批量评估完成！")
    print(f"   成功: {successful_count}/{len(student_ids)}")
    print(f"{'='*80}\n")
    
    # 保存结果
    from tasa_config import FORGETTING_SCORE_METHOD
    backbone_suffix = get_backbone_suffix(backbone)
    result_dir = f'/mnt/localssd/bank/evaluation_results/TASA-lambda{lambda_value}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
    os.makedirs(result_dir, exist_ok=True)
    
    overall_result = {
        'dataset': dataset,
        'lambda_value': lambda_value,
        'backbone': backbone,
        'num_students': len(student_ids),
        'strategy_max': {
            'avg_learning_gain': float(np.mean(learning_gains_max)),
            'std_learning_gain': float(np.std(learning_gains_max)),
            'median_learning_gain': float(np.median(learning_gains_max))
        } if all_results else None,
        'students': all_results
    }
    
    with open(f'{result_dir}/overall.json', 'w') as f:
        json.dump(overall_result, f, indent=2)
    
    print(f"💾 结果已保存: {result_dir}/overall.json")
    
    return overall_result

def main():
    LAMBDA_VALUES = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    BACKBONES = ['llama', 'qwen', 'gpt']
    DATASET = 'assist2017'
    MAX_WORKERS = 10
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🔬 TASA Lambda Ablation Study                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 配置:")
    print(f"  • Lambda values: {LAMBDA_VALUES}")
    print(f"  • Backbones: {BACKBONES}")
    print(f"  • Dataset: {DATASET}")
    print(f"  • Total experiments: {len(LAMBDA_VALUES)} × {len(BACKBONES)} = {len(LAMBDA_VALUES) * len(BACKBONES)}")
    print(f"  • Max workers: {MAX_WORKERS}")
    print(f"\n⏱️  预计总时间: ~3-4小时")
    print(f"\n{'='*80}\n")
    
    start_time = time.time()
    all_results = {}
    
    # Backbone在最外层循环
    for backbone in BACKBONES:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  🎯 BACKBONE: {backbone.upper():^66} ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        # 设置对应的config
        os.environ['TASA_CONFIG'] = f'tasa_config_{backbone}'
        
        backbone_results = {}
        
        for lambda_value in LAMBDA_VALUES:
            result = batch_evaluate(lambda_value, backbone, DATASET, MAX_WORKERS)
            if result:
                backbone_results[str(lambda_value)] = result['strategy_max']['avg_learning_gain']
        
        all_results[backbone] = backbone_results
        
        print(f"\n{'─'*80}")
        print(f"📊 {backbone.upper()} 完成所有Lambda测试")
        print(f"{'─'*80}\n")
    
    total_elapsed = time.time() - start_time
    
    # 打印汇总
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║                     📊 Lambda Ablation完成汇总                              ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    print("结果矩阵 (Lambda × Backbone):\n")
    print(f"{'Lambda':<10} | {' | '.join([f'{b.upper():^12}' for b in BACKBONES])}")
    print(f"{'-'*10}-+-{'-+-'.join(['-'*12]*len(BACKBONES))}")
    
    for lv in LAMBDA_VALUES:
        row = [f"{lv:<10}"]
        for backbone in BACKBONES:
            if str(lv) in all_results.get(backbone, {}):
                lg = all_results[backbone][str(lv)] * 100
                row.append(f"{lg:>11.1f}%")
            else:
                row.append("     -")
        print(" | ".join(row))
    
    print(f"\n{'='*80}")
    print(f"⏱️  总耗时: {total_elapsed/3600:.2f} 小时 ({total_elapsed/60:.1f} 分钟)")
    print(f"{'='*80}\n")
    
    # 保存结果
    results_file = '/mnt/localssd/logs/lambda_ablation_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'lambda_values': LAMBDA_VALUES,
            'backbones': BACKBONES,
            'dataset': DATASET,
            'results': all_results,
            'elapsed_hours': total_elapsed/3600
        }, f, indent=2)
    print(f"📄 结果已保存至: {results_file}\n")

if __name__ == '__main__':
    main()

