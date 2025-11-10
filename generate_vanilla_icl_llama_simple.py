#!/usr/bin/env python3
"""
直接生成Vanilla-ICL-llama的28轮dialogue（简化版）
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置环境变量指定使用llama配置
os.environ['TASA_CONFIG'] = 'llama'

from llm_client_unified import UnifiedLLMClient
from tasa_config_llama import TUTOR_MODEL, STUDENT_MODEL, GPT_ENDPOINT, API_KEY
from openai import OpenAI

def generate_vanilla_icl_dialogue_simple(student_id, concept_text, dataset):
    """直接生成28轮Vanilla-ICL dialogue"""
    
    output_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/{student_id}-{concept_text}.json'
    
    if os.path.exists(output_file):
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
        
        # 14轮对话（28 turns）
        dialogue = []
        
        tutor_system = f"""You are a helpful math tutor. Guide the student to learn about {concept_text}.
- Ask clear questions
- Provide hints when needed
- Give constructive feedback
- Be patient and encouraging"""
        
        student_system = f"""You are a middle school student learning {concept_text}.

Your profile:
{persona}

Respond naturally based on your understanding."""
        
        messages = []
        
        for round_num in range(1, 15):  # 14轮
            # Tutor生成问题/引导
            tutor_prompt = f"This is round {round_num}/14. " + (
                f"Teach the student about {concept_text}. Ask a question or provide guidance." 
                if round_num == 1 
                else "Continue the tutoring session based on the student's previous response."
            )
            
            messages.append({"role": "user", "content": tutor_prompt})
            
            tutor_response = tutor_client.chat_completion(
                messages=[{"role": "system", "content": tutor_system}] + messages,
                temperature=0.7,
                max_tokens=800
            )
            
            messages.append({"role": "assistant", "content": tutor_response})
            
            dialogue.append({
                "role": "tutor",
                "content": tutor_response,
                "round": round_num
            })
            
            # Student回答
            student_messages = [{"role": "system", "content": student_system}]
            student_messages.append({"role": "user", "content": f"Tutor: {tutor_response}\n\nPlease respond as the student."})
            
            student_response = student_client.chat.completions.create(
                model=STUDENT_MODEL,
                messages=student_messages,
                temperature=1.0,
                max_tokens=400
            ).choices[0].message.content
            
            messages.append({"role": "user", "content": f"Student: {student_response}"})
            
            dialogue.append({
                "role": "student",
                "content": student_response,
                "round": round_num
            })
        
        # 保存dialogue
        with open(output_file, 'w') as f:
            json.dump(dialogue, f, indent=2)
        
        return f"✅ 学生{student_id}完成 ({len(dialogue)}轮)"
        
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
    print('📝 生成Vanilla-ICL-llama 28轮Dialogue (简化版)')
    print('='*80)
    print(f'Dataset: {dataset}')
    print(f'Students: {len(students)}')
    print(f'Tutor: {TUTOR_MODEL}, Student: {STUDENT_MODEL}')
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
    
    print(f"🚀 开始生成{len(tasks)}个dialogue (max_workers=5)\n")
    
    completed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(generate_vanilla_icl_dialogue_simple, sid, concept, dataset): (sid, concept)
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
    print(f'📁 /mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}/')
    print('='*80)

if __name__ == '__main__':
    main()

