#!/usr/bin/env python3
"""
Dialogue Turns Ablation Study
比较TASA、Vanilla-ICL、TutorLLM在不同dialogue轮数下的表现

Dialogue turns: [0, 4, 8, 12, 16, 20, 24, 28]
Dataset: Assist2017
Backbone: Llama-3.1-8B
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
from baseline_vanilla_icl import VanillaICLTutor
from baseline_tutorllm import TutorLLM
from tasa_evaluation import TASAEvaluator
from openai import OpenAI
from tasa_config_llama import STUDENT_MODEL

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

def get_tutor(method, num_rounds):
    """获取线程本地的Tutor实例"""
    tutor_key = f'tutor_{method}_rounds{num_rounds}'
    if not hasattr(thread_local, tutor_key):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化{method} Tutor (rounds={num_rounds})...")
            
            if method == 'Vanilla-ICL':
                # Vanilla-ICL支持可变轮数
                class VanillaICLConfigurable(VanillaICLTutor):
                    def __init__(self, num_rounds):
                        super().__init__()
                        self.num_rounds = num_rounds
                    
                    def conduct_tutoring_session(self, student_id, dataset, concept_text, student_system_prompt):
                        """可配置轮数的tutoring session"""
                        dialogue = []
                        
                        initial_query = f"I want to learn about {concept_text}"
                        dialogue.append({"role": "user", "round": 0, "content": initial_query})
                        
                        # 特殊处理：如果num_rounds=0，直接返回空dialogue
                        if self.num_rounds == 0:
                            return dialogue
                        
                        # 第一轮
                        first_question = self.generate_question(initial_query, [], student_id, dataset, concept_text)
                        dialogue.append({"role": "assistant", "round": 1, "content": first_question})
                        
                        # 后续轮次
                        for round_num in range(2, self.num_rounds + 1):
                            last_question = dialogue[-1]['content']
                            student_answer = self.get_student_response(last_question, student_system_prompt)
                            dialogue.append({"role": "user", "round": round_num, "content": student_answer})
                            
                            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                                   for msg in dialogue]
                            
                            next_question = self.generate_question(
                                student_answer, conversation_history, student_id, dataset, concept_text
                            )
                            dialogue.append({"role": "assistant", "round": round_num, "content": next_question})
                        
                        return dialogue
                
                tutor = VanillaICLConfigurable(num_rounds)
                
            elif method == 'TutorLLM':
                class TutorLLMConfigurable(TutorLLM):
                    def __init__(self, num_rounds):
                        super().__init__()
                        self.num_rounds = num_rounds
                    
                    def conduct_tutoring_session(self, student_id, dataset, concept_text, student_system_prompt):
                        from student_roleplay_evaluation import load_session
                        
                        # 加载session获取persona
                        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
                        session = load_session(session_file)
                        persona_description = session['persona']['description']
                        
                        dialogue = []
                        
                        # Round 0
                        student_request = f"I want to learn about {concept_text}"
                        dialogue.append({
                            "role": "user",
                            "content": student_request,
                            "round": 0
                        })
                        
                        if self.num_rounds == 0:
                            return dialogue
                        
                        # 进行num_rounds轮教学
                        for round_num in range(1, self.num_rounds + 1):
                            # RAG: 检索相关memory
                            if round_num == 1:
                                query = f"learning {concept_text}"
                            else:
                                query = dialogue[-1]['content'][:200]
                            
                            relevant_memories = self.retrieve_memory(student_id, dataset, query)
                            memory_context = "\n".join([f"- {mem}" for mem in relevant_memories])
                            
                            # 构建dialogue context
                            dialogue_context = "\n".join([
                                f"{'Student' if msg['role']=='user' else 'Tutor'}: {msg['content'][:200]}..."
                                for msg in dialogue[-4:]
                            ])
                            
                            # 生成tutor回复
                            if round_num == 1:
                                prompt = f"""You are a personalized math tutor.

Student Profile:
{persona_description}

Relevant Past Learning:
{memory_context}

The student wants to learn about {concept_text}. Generate your first practice question.

Make it appropriate for their level based on their profile and past learning."""
                            else:
                                last_student_answer = dialogue[-1]['content']
                                prompt = f"""You are a personalized math tutor.

Student Profile:
{persona_description}

Relevant Past Learning:
{memory_context}

Recent Dialogue:
{dialogue_context}

Student's Last Answer:
{last_student_answer}

Task:
1) Provide feedback on their answer
2) Generate the next practice question

Use their profile and past learning to personalize your tutoring."""
                            
                            content = self.tutor_client.chat_completion(
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.7,
                                max_tokens=500
                            )
                            
                            tutor_response = content if content else "Let's continue."
                            dialogue.append({
                                "role": "assistant",
                                "content": tutor_response,
                                "round": round_num
                            })
                            
                            # 学生回答（最后一轮不需要）
                            if round_num < self.num_rounds:
                                response = self.openai_client.chat.completions.create(
                                    model=STUDENT_MODEL,
                                    messages=[
                                        {"role": "system", "content": student_system_prompt},
                                        {"role": "user", "content": f"Answer the tutor's question:\n{tutor_response}"}
                                    ],
                                    temperature=0.7,
                                    max_tokens=300
                                )
                                
                                student_answer = response.choices[0].message.content if response.choices[0].message.content else "I don't know"
                                dialogue.append({
                                    "role": "user",
                                    "content": student_answer,
                                    "round": round_num + 1
                                })
                        
                        return dialogue
                
                tutor = TutorLLMConfigurable(num_rounds)
                
            elif method == 'Vanilla-ICL':
                class VanillaICLConfigurable(VanillaICLTutor):
                    def __init__(self, num_rounds):
                        super().__init__()
                        self.num_rounds = num_rounds
                    
                    def conduct_tutoring_session(self, student_id, dataset, concept_text, student_system_prompt):
                        dialogue = []
                        
                        initial_query = f"I want to learn about {concept_text}"
                        dialogue.append({"role": "user", "round": 0, "content": initial_query})
                        
                        if self.num_rounds == 0:
                            return dialogue
                        
                        # 第一轮
                        first_question = self.generate_question(initial_query, [], student_id, dataset, concept_text)
                        dialogue.append({"role": "assistant", "round": 1, "content": first_question})
                        
                        # 后续轮次
                        for round_num in range(2, self.num_rounds + 1):
                            last_question = dialogue[-1]['content']
                            student_answer = self.get_student_response(last_question, student_system_prompt)
                            dialogue.append({"role": "user", "round": round_num, "content": student_answer})
                            
                            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                                   for msg in dialogue]
                            
                            next_question = self.generate_question(
                                student_answer, conversation_history, student_id, dataset, concept_text
                            )
                            dialogue.append({"role": "assistant", "round": round_num, "content": next_question})
                        
                        return dialogue
                
                tutor = VanillaICLConfigurable(num_rounds)
                
            elif method == 'TASA':
                class TASAConfigurable(TASATutor):
                    def __init__(self, num_rounds):
                        super().__init__()
                        self.num_rounds = num_rounds
                    
                    def conduct_tutoring_session(self, student_id, dataset, concept_text, student_system_prompt):
                        """可配置轮数的TASA tutoring session - 完全按照原版流程"""
                        dialogue = []
                        
                        # Round 0: 学生表达想学习
                        initial_query = f"I want to learn about {concept_text}"
                        dialogue.append({
                            "role": "user",
                            "round": 0,
                            "content": initial_query
                        })
                        
                        if self.num_rounds == 0:
                            return dialogue
                        
                        # Round 1: RAG + 生成第一个问题
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
                        
                        first_question = self.generate_first_question(
                            rewritten_persona, rewritten_memory, concept_text
                        )
                        
                        dialogue.append({
                            "role": "assistant",
                            "round": 1,
                            "content": first_question,
                            "retrieved_persona": [p['description'] for p in top_persona],
                            "retrieved_memory": [m['description'] for m in top_memory],
                            "rewritten_persona": rewritten_persona,
                            "rewritten_memory": rewritten_memory
                        })
                        
                        # 后续轮次：学生回答 -> RAG -> 讲解+问题
                        for round_num in range(2, self.num_rounds + 1):
                            # 学生回答上一轮的问题
                            last_question = dialogue[-1]['content']
                            student_answer = self.get_student_response(last_question, student_system_prompt)
                            
                            dialogue.append({
                                "role": "user",
                                "round": round_num,
                                "content": student_answer
                            })
                            
                            # RAG检索当前query（学生的回答）
                            top_persona, top_memory = self.rag.retrieve_and_rerank(
                                query=student_answer,
                                student_id=student_id,
                                dataset=dataset,
                                concept_text=concept_text
                            )
                            
                            # 重写
                            rewritten_persona, rewritten_memory = self.rewriter.rewrite_top_items(
                                top_persona, top_memory,
                                student_id=student_id,
                                dataset=dataset,
                                concept_text=concept_text
                            )
                            
                            # 生成讲解+下一个问题
                            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                                   for msg in dialogue]
                            
                            explanation_and_question = self.generate_explanation_and_question(
                                rewritten_persona, rewritten_memory,
                                conversation_history, concept_text
                            )
                            
                            dialogue.append({
                                "role": "assistant",
                                "round": round_num,
                                "content": explanation_and_question,
                                "retrieved_persona": [p['description'] for p in top_persona],
                                "retrieved_memory": [m['description'] for m in top_memory],
                                "rewritten_persona": rewritten_persona,
                                "rewritten_memory": rewritten_memory
                            })
                        
                        return dialogue
                
                tutor = TASAConfigurable(num_rounds)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            setattr(thread_local, tutor_key, tutor)
    
    return getattr(thread_local, tutor_key)

def get_evaluator():
    """获取线程本地的Evaluator实例"""
    if not hasattr(thread_local, 'evaluator'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Evaluator...")
            thread_local.evaluator = TASAEvaluator()
    return thread_local.evaluator

def process_single_student(student_id, dataset, method, num_dialogue_turns):
    """
    处理单个学生
    num_dialogue_turns: 总的dialogue轮数（student + tutor）
    实际tutor轮数 = num_dialogue_turns // 2
    """
    num_tutor_rounds = num_dialogue_turns // 2
    
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🎓 学生 {student_id} | {method} | {num_dialogue_turns} turns")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        concept_id = session['concept_id']
        
        # Pre-test score - 从pretest文件读取
        pretest_file = f'/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json'
        if not os.path.exists(pretest_file):
            safe_print(f"   ❌ Pre-test文件不存在: {pretest_file}")
            return None
        
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        pre_test_score = pretest_data['roleplay_accuracy']
        
        # 特殊处理: turns=0直接返回pre-test结果
        if num_dialogue_turns == 0:
            safe_print(f"   📊 Turns=0: 直接使用pre-test结果")
            
            # TASA: 只返回learning_gain
            if method == 'TASA':
                result = {
                    'student_id': student_id,
                    'pre_test_score': pre_test_score,
                    'post_test_score': pre_test_score,
                    'learning_gain': 0.0,
                    'dialogue_turns': 0,
                    'method': method
                }
            # Baseline: 返回best/avg/worst三种（都是0）
            else:
                result = {
                    'student_id': student_id,
                    'pre_test_score': pre_test_score,
                    'dialogue_turns': 0,
                    'method': method,
                    'post_test_run1': pre_test_score,
                    'post_test_run2': pre_test_score,
                    'max_post_test_accuracy': pre_test_score,
                    'learning_gain_max': 0.0,
                    'avg_post_test_accuracy': pre_test_score,
                    'learning_gain_avg': 0.0,
                    'min_post_test_accuracy': pre_test_score,
                    'learning_gain_min': 0.0
                }
            
            safe_print(f"   ✅ Pre-test: {pre_test_score*100:.1f}% | Learning Gain: 0.0%")
            return result
        
        # 检查28轮完整dialogue是否存在（只生成一次）
        from tasa_config_llama import FORGETTING_SCORE_METHOD
        full_dialogue_dir = f'/mnt/localssd/bank/dialogue/{method}-turns28-llama/{dataset}/{FORGETTING_SCORE_METHOD}'
        full_dialogue_file = f'{full_dialogue_dir}/{student_id}-{concept_text}.json'
        
        if not os.path.exists(full_dialogue_file):
            safe_print(f"   📚 生成完整28轮dialogue（仅生成一次）...")
            student_prompt = build_student_system_prompt(session)
            
            # 固定生成14个tutor rounds（=28 dialogue turns）
            tutor = get_tutor(method, 14)
            
            try:
                dialogue = tutor.conduct_tutoring_session(
                    student_id=student_id,
                    dataset=dataset,
                    concept_text=concept_text,
                    student_system_prompt=student_prompt
                )
                
                # 保存28轮完整dialogue
                os.makedirs(full_dialogue_dir, exist_ok=True)
                with open(full_dialogue_file, 'w') as f:
                    json.dump(dialogue, f, indent=2)
                
                safe_print(f"   ✅ 完整28轮dialogue生成完成")
            except Exception as e:
                safe_print(f"   ❌ Dialogue生成失败: {e}")
                return None
        else:
            safe_print(f"   ✅ 完整28轮dialogue已存在")
        
        # 指向完整dialogue文件，后面会截取
        dialogue_file = full_dialogue_file
        
        # Post-test评估
        safe_print(f"   📝 开始post-test评估...")
        
        # 加载post-test问题
        questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
        with open(questions_file) as f:
            all_questions = json.load(f)
        # concept_id可能是int，需要转为str
        questions = all_questions[str(concept_id)]['questions']
        
        # 构建student prompt
        student_prompt = build_student_system_prompt(session)
        
        # 加载完整28轮dialogue
        with open(dialogue_file) as f:
            dialogue_data = json.load(f)
        full_dialogue = dialogue_data if isinstance(dialogue_data, list) else dialogue_data.get('dialogue', [])
        
        # 根据num_dialogue_turns截取dialogue
        # dialogue格式：[{"role": "user", "round": 0}, {"role": "assistant", "round": 1}, ...]
        # num_dialogue_turns包括student和tutor的所有消息
        safe_print(f"   ✂️  从28轮dialogue中截取前{num_dialogue_turns}轮...")
        
        if num_dialogue_turns >= 28:
            # 使用完整dialogue
            dialogue = full_dialogue
        else:
            # 截取指定轮数：保留round <= num_dialogue_turns的消息
            dialogue = []
            for msg in full_dialogue:
                if 'round' in msg and msg['round'] <= num_dialogue_turns:
                    dialogue.append(msg)
                else:
                    break  # 一旦超过就停止
        
        safe_print(f"   ✅ 截取完成：使用{len(dialogue)}条消息 (目标{num_dialogue_turns}轮)")
        
        evaluator = get_evaluator()
        
        try:
            # TASA: 使用best-of-two策略
            if method == 'TASA':
                safe_print(f"   📊 进行2次Post-test (取最好)")
                post_test_results = []
                
                for run_id in range(1, 3):
                    safe_print(f"   Run {run_id}/2")
                    post_acc, _ = evaluator.conduct_post_test(
                        student_id, dataset, concept_text,
                        dialogue, questions, student_prompt
                    )
                    post_test_results.append(post_acc)
                    safe_print(f"   Run {run_id} 准确率: {post_acc*100:.1f}%")
                
                # 取最好的结果
                best_post_test = max(post_test_results)
                
                if pre_test_score >= 1.0:
                    learning_gain = 0.0
                else:
                    learning_gain = (best_post_test - pre_test_score) / (1.0 - pre_test_score)
                
                result = {
                    'student_id': student_id,
                    'pre_test_score': pre_test_score,
                    'post_test_score': best_post_test,
                    'learning_gain': learning_gain,
                    'dialogue_turns': num_dialogue_turns,
                    'method': method,
                    'post_test_run1': post_test_results[0],
                    'post_test_run2': post_test_results[1]
                }
                
                safe_print(f"   ✅ 评估完成 (Best-of-Two)")
                safe_print(f"      Pre: {pre_test_score*100:.1f}% | Best Post: {best_post_test*100:.1f}% | Gain: {learning_gain*100:.1f}%")
            
            # Vanilla-ICL和TutorLLM: 保存best/average/worst三种结果
            else:
                safe_print(f"   📊 进行2次Post-test (保存Best/Avg/Worst)")
                post_test_results = []
                
                for run_id in range(1, 3):
                    safe_print(f"   Run {run_id}/2")
                    post_acc, _ = evaluator.conduct_post_test(
                        student_id, dataset, concept_text,
                        dialogue, questions, student_prompt
                    )
                    post_test_results.append(post_acc)
                    safe_print(f"   Run {run_id} 准确率: {post_acc*100:.1f}%")
                
                # 计算三种策略
                max_post_test = max(post_test_results)
                avg_post_test = np.mean(post_test_results)
                min_post_test = min(post_test_results)
                
                # 计算learning gain - 基于最高分（Best策略）
                if pre_test_score >= 1.0:
                    learning_gain_max = 0.0
                else:
                    learning_gain_max = (max_post_test - pre_test_score) / (1.0 - pre_test_score)
                
                # 计算learning gain - 基于平均分（Average策略）
                if pre_test_score >= 1.0:
                    learning_gain_avg = 0.0
                else:
                    learning_gain_avg = (avg_post_test - pre_test_score) / (1.0 - pre_test_score)
                
                # 计算learning gain - 基于最低分（Worst策略）
                if pre_test_score >= 1.0:
                    learning_gain_min = 0.0
                else:
                    learning_gain_min = (min_post_test - pre_test_score) / (1.0 - pre_test_score)
                
                result = {
                    'student_id': student_id,
                    'pre_test_score': pre_test_score,
                    'dialogue_turns': num_dialogue_turns,
                    'method': method,
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
                
                safe_print(f"   ✅ 评估完成")
                safe_print(f"      Pre: {pre_test_score*100:.1f}%")
                safe_print(f"      Best Post: {max_post_test*100:.1f}% (Gain={learning_gain_max*100:.1f}%)")
                safe_print(f"      Avg Post: {avg_post_test*100:.1f}% (Gain={learning_gain_avg*100:.1f}%)")
                safe_print(f"      Worst Post: {min_post_test*100:.1f}% (Gain={learning_gain_min*100:.1f}%)")
            
            return result
            
        except Exception as e:
            safe_print(f"   ❌ 评估失败: {e}")
            import traceback
            safe_print(f"   {traceback.format_exc()}")
            return None
    
    except Exception as e:
        safe_print(f"❌ 处理学生{student_id}时出错: {e}")
        return None

def batch_evaluate(method, num_dialogue_turns, dataset='assist2017', max_workers=10):
    """批量评估"""
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    
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
            print(f"❌ 无法解析students文件")
            return None
    
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║   📊 {method} | {num_dialogue_turns} turns | {dataset}                        ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: {max_workers}")
    print(f"{'='*80}\n")
    
    all_results = []
    successful_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_student, sid, dataset, method, num_dialogue_turns): sid 
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
    print(f"\n📊 整体统计 ({method}, {num_dialogue_turns} turns):")
    
    if all_results:
        # TASA: 使用learning_gain（best-of-two）
        if method == 'TASA':
            learning_gains = [r['learning_gain'] for r in all_results]
            print(f"\n   平均Learning Gain (Best-of-Two): {np.mean(learning_gains)*100:.1f}% ± {np.std(learning_gains)*100:.1f}%")
            print(f"   中位数: {np.median(learning_gains)*100:.1f}%")
            print(f"   范围: [{np.min(learning_gains)*100:.1f}%, {np.max(learning_gains)*100:.1f}%]")
        # Baseline: 显示best/average/worst三种策略
        else:
            learning_gains_max = [r['learning_gain_max'] for r in all_results]
            learning_gains_avg = [r['learning_gain_avg'] for r in all_results]
            learning_gains_min = [r['learning_gain_min'] for r in all_results]
            
            print(f"\n   Best策略   平均Learning Gain: {np.mean(learning_gains_max)*100:.1f}% ± {np.std(learning_gains_max)*100:.1f}%")
            print(f"   Average策略 平均Learning Gain: {np.mean(learning_gains_avg)*100:.1f}% ± {np.std(learning_gains_avg)*100:.1f}%")
            print(f"   Worst策略  平均Learning Gain: {np.mean(learning_gains_min)*100:.1f}% ± {np.std(learning_gains_min)*100:.1f}%")
    
    print(f"\n✅ 批量评估完成！")
    print(f"   成功: {successful_count}/{len(student_ids)}")
    print(f"{'='*80}\n")
    
    # 保存结果
    from tasa_config_llama import FORGETTING_SCORE_METHOD
    result_dir = f'/mnt/localssd/bank/evaluation_results/{method}-turns{num_dialogue_turns}-llama/{dataset}/{FORGETTING_SCORE_METHOD}'
    os.makedirs(result_dir, exist_ok=True)
    
    # TASA: 只保存best结果
    if method == 'TASA':
        learning_gains = [r['learning_gain'] for r in all_results] if all_results else []
        overall_result = {
            'dataset': dataset,
            'method': method,
            'dialogue_turns': num_dialogue_turns,
            'num_students': len(student_ids),
            'avg_learning_gain': float(np.mean(learning_gains)) if all_results else 0.0,
            'std_learning_gain': float(np.std(learning_gains)) if all_results else 0.0,
            'median_learning_gain': float(np.median(learning_gains)) if all_results else 0.0,
            'students': all_results
        }
    # Baseline: 保存best/average/worst三种策略的结果
    else:
        learning_gains_max = [r['learning_gain_max'] for r in all_results] if all_results else []
        learning_gains_avg = [r['learning_gain_avg'] for r in all_results] if all_results else []
        learning_gains_min = [r['learning_gain_min'] for r in all_results] if all_results else []
        
        overall_result = {
            'dataset': dataset,
            'method': method,
            'dialogue_turns': num_dialogue_turns,
            'num_students': len(student_ids),
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
    
    print(f"💾 结果已保存: {result_dir}/overall.json")
    
    return overall_result

def main():
    DIALOGUE_TURNS = [0, 4, 8, 12, 16, 20, 24, 28]
    METHODS = ['TASA', 'Vanilla-ICL', 'TutorLLM']
    DATASET = 'assist2017'
    MAX_WORKERS = 10
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                 🔬 Dialogue Turns Ablation Study                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 配置:")
    print(f"  • Methods: {', '.join(METHODS)}")
    print(f"  • Dialogue turns: {DIALOGUE_TURNS}")
    print(f"  • Dataset: {DATASET}")
    print(f"  • Backbone: Llama-3.1-8B")
    print(f"  • Total experiments: {len(METHODS)} × {len(DIALOGUE_TURNS)} = {len(METHODS) * len(DIALOGUE_TURNS)}")
    print(f"  • Max workers: {MAX_WORKERS}")
    print(f"\n⏱️  预计总时间: ~4-5小时")
    print(f"\n{'='*80}\n")
    
    # 设置环境
    os.environ['TASA_CONFIG'] = 'tasa_config_llama'
    
    start_time = time.time()
    all_results = {}
    
    # Dialogue Turns在最外层循环
    for turns in DIALOGUE_TURNS:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  📊 DIALOGUE TURNS: {turns:^56} ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        for method in METHODS:
            # 跳过已存在的20轮实验（已经做过）
            if turns == 20:
                print(f"\n⏭️  跳过 {method} - {turns} turns (已完成)")
                # 尝试读取已有结果
                from tasa_config_llama import FORGETTING_SCORE_METHOD
                existing_result_file = f'/mnt/localssd/bank/evaluation_results/{method}-turns20-llama/{DATASET}/{FORGETTING_SCORE_METHOD}/overall.json'
                if os.path.exists(existing_result_file):
                    with open(existing_result_file) as f:
                        existing_data = json.load(f)
                        if method not in all_results:
                            all_results[method] = {}
                        # 根据method类型提取learning gain
                        if method == 'TASA':
                            all_results[method][str(turns)] = existing_data['avg_learning_gain']
                        else:  # Baseline: 使用strategy_max (Best策略)
                            all_results[method][str(turns)] = existing_data['strategy_max']['avg_learning_gain']
                continue
            
            result = batch_evaluate(method, turns, DATASET, MAX_WORKERS)
            if result:
                if method not in all_results:
                    all_results[method] = {}
                # 根据method类型提取learning gain
                if method == 'TASA':
                    all_results[method][str(turns)] = result['avg_learning_gain']
                else:  # Baseline: 使用strategy_max (Best策略)
                    all_results[method][str(turns)] = result['strategy_max']['avg_learning_gain']
        
        print(f"\n{'─'*80}")
        print(f"📊 Turns={turns} 完成所有Method测试")
        print(f"{'─'*80}\n")
    
    total_elapsed = time.time() - start_time
    
    # 打印汇总
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║                   📊 Dialogue Turns Ablation完成汇总                        ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    print("结果矩阵 (Turns × Method):\n")
    print(f"{'Turns':<10} | {' | '.join([f'{m:^12}' for m in METHODS])}")
    print(f"{'-'*10}-+-{'-+-'.join(['-'*12]*len(METHODS))}")
    
    for turns in DIALOGUE_TURNS:
        row = [f"{turns:<10}"]
        for method in METHODS:
            if str(turns) in all_results.get(method, {}):
                lg = all_results[method][str(turns)] * 100
                row.append(f"{lg:>11.1f}%")
            else:
                row.append("     -")
        print(" | ".join(row))
    
    print(f"\n{'='*80}")
    print(f"⏱️  总耗时: {total_elapsed/3600:.2f} 小时 ({total_elapsed/60:.1f} 分钟)")
    print(f"{'='*80}\n")
    
    # 保存结果
    results_file = '/mnt/localssd/logs/dialogue_turns_ablation_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'methods': METHODS,
            'dialogue_turns': DIALOGUE_TURNS,
            'dataset': DATASET,
            'backbone': 'Llama-3.1-8B',
            'results': all_results,
            'elapsed_hours': total_elapsed/3600
        }, f, indent=2)
    print(f"📄 结果已保存至: {results_file}\n")

if __name__ == '__main__':
    main()

