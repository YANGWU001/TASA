#!/usr/bin/env python3
"""
生成Vanilla-ICL-llama的28轮dialogue + 每4轮evaluation
格式参考Vanilla-ICL-qwen
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置环境变量
os.environ['TASA_CONFIG'] = 'llama'

from llm_client_unified import UnifiedLLMClient
from tasa_config_llama import TUTOR_MODEL, STUDENT_MODEL, GPT_ENDPOINT, API_KEY
from openai import OpenAI
from tasa_evaluation import TASAEvaluator

def generate_vanilla_icl_with_eval(student_id, concept_text, dataset):
    """生成28轮dialogue + 每4轮evaluation"""
    
    # 输出目录
    dialogue_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-llama/{dataset}'
    eval_dir = f'/mnt/localssd/bank/evaluation_results/Vanilla-ICL-llama-turns-ablation/{dataset}'
    os.makedirs(dialogue_dir, exist_ok=True)
    os.makedirs(eval_dir, exist_ok=True)
    
    dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
    
    # 如果已存在，跳过
    if os.path.exists(dialogue_file):
        return f"✅ 学生{student_id}已存在"
    
    try:
        # 加载persona
        persona_file = f'/mnt/localssd/bank/persona/{dataset}/data/{student_id}.json'
        with open(persona_file, 'r') as f:
            persona_list = json.load(f)
            matching = [p for p in persona_list if p.get('concept_text') == concept_text]
            if matching:
                persona = matching[0].get('description', '')
            else:
                descriptions = [p.get('description', '') for p in persona_list[:3]]
                persona = '\n'.join(descriptions)
        
        # 初始化clients
        tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        student_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
        
        # Dialogue
        dialogue = []
        
        # Round 0: 初始请求
        initial_query = f"I want to learn about {concept_text}"
        dialogue.append({
            "role": "user",
            "content": initial_query,
            "round": 0
        })
        
        # 系统prompts
        tutor_system = f"""You are a helpful math tutor for middle school students.
Topic: {concept_text}
- Ask clear questions
- Provide helpful feedback
- Guide the student step by step"""
        
        student_system = f"""You are a middle school student learning {concept_text}.

Your profile:
{persona}

Respond naturally based on your understanding."""
        
        # 14轮对话（round 1-14，共28 turns）
        conversation = []
        
        for round_num in range(1, 15):
            # Tutor turn
            if round_num == 1:
                tutor_prompt = initial_query
            else:
                tutor_prompt = f"Continue tutoring. This is round {round_num}/14."
            
            messages = [{"role": "system", "content": tutor_system}]
            messages.extend(conversation)
            messages.append({"role": "user", "content": tutor_prompt})
            
            tutor_response = tutor_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            dialogue.append({
                "role": "assistant",
                "content": tutor_response,
                "round": round_num
            })
            
            conversation.append({"role": "assistant", "content": tutor_response})
            
            # Student turn
            student_messages = [{"role": "system", "content": student_system}]
            student_messages.append({
                "role": "user",
                "content": f"Tutor: {tutor_response}\n\nRespond as the student."
            })
            
            student_response = student_client.chat.completions.create(
                model=STUDENT_MODEL,
                messages=student_messages,
                temperature=1.0,
                max_tokens=400
            ).choices[0].message.content
            
            dialogue.append({
                "role": "user",
                "content": student_response,
                "round": round_num + 1
            })
            
            conversation.append({"role": "user", "content": student_response})
        
        # 保存dialogue
        dialogue_data = {
            "student_id": student_id,
            "dataset": dataset,
            "concept": concept_text,
            "method": "Vanilla-ICL-llama",
            "total_rounds": 14,
            "dialogue": dialogue
        }
        
        with open(dialogue_file, 'w') as f:
            json.dump(dialogue_data, f, indent=2)
        
        # 每4轮evaluation（0, 4, 8, 12, 16, 20, 24, 28 turns）
        evaluator = TASAEvaluator()
        eval_results = {}
        
        for num_turns in [0, 4, 8, 12, 16, 20, 24, 28]:
            # 截取dialogue
            truncated_dialogue = [d for d in dialogue if d['round'] <= num_turns // 2]
            
            # Evaluation
            eval_result = evaluator.evaluate_learning_gain(
                student_id=student_id,
                dataset=dataset,
                concept_text=concept_text,
                dialogue=truncated_dialogue
            )
            
            eval_results[f"turns_{num_turns}"] = eval_result
        
        # 保存evaluation结果
        eval_file = f'{eval_dir}/{student_id}-{concept_text}.json'
        with open(eval_file, 'w') as f:
            json.dump(eval_results, f, indent=2)
        
        return f"✅ 学生{student_id}完成 ({len(dialogue)}轮 + eval)"
        
    except Exception as e:
        return f"❌ 学生{student_id}失败: {e}"

def main():
    dataset = 'assist2017'
    
    # 加载students
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    with open(students_file, 'r') as f:
        data = json.load(f)
        students = data.get('sampled_students', data.get('students', []))
    
    print('='*80)
    print('📝 生成Vanilla-ICL-llama 28轮Dialogue + Evaluation')
    print('='*80)
    print(f'Dataset: {dataset}')
    print(f'Students: {len(students)}')
    print(f'Tutor: {TUTOR_MODEL}, Student: {STUDENT_MODEL}')
    print(f'Evaluation points: 0, 4, 8, 12, 16, 20, 24, 28 turns')
    print('='*80)
    print()
    
    tasks = []
    for student_info in students:
        if isinstance(student_info, dict):
            student_id = student_info['student_id']
            concept = student_info['target_concept']
        else:
            student_id = student_info
            tasa_dir = f'/mnt/localssd/bank/dialogue/TASA/{dataset}'
            existing = [f for f in os.listdir(tasa_dir) if f.startswith(f'{student_id}-')]
            if existing:
                concept = existing[0].replace(f'{student_id}-', '').replace('.json', '')
            else:
                print(f"⚠️  学生{student_id}找不到concept")
                continue
        
        tasks.append((student_id, concept))
    
    print(f"🚀 开始生成{len(tasks)}个dialogue (max_workers=3, 因为需要evaluation)\n")
    
    completed = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_vanilla_icl_with_eval, sid, concept, dataset): (sid, concept)
            for sid, concept in tasks
        }
        
        for future in as_completed(futures):
            sid, concept = futures[future]
            try:
                result = future.result()
                print(f"[{completed+1}/{len(tasks)}] {result}")
                completed += 1
            except Exception as e:
                print(f"[{completed+1}/{len(tasks)}] ❌ 学生{sid}异常: {e}")
                completed += 1
    
    print()
    print('='*80)
    print('✅ 完成！')
    print(f'📁 Dialogue: /mnt/localssd/bank/dialogue/Vanilla-ICL-llama/{dataset}/')
    print(f'📁 Evaluation: /mnt/localssd/bank/evaluation_results/Vanilla-ICL-llama-turns-ablation/{dataset}/')
    print('='*80)

if __name__ == '__main__':
    main()

