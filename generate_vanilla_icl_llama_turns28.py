#!/usr/bin/env python3
"""
生成Vanilla-ICL-llama的28轮dialogue（14个QA对）
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置环境变量指定使用llama配置
os.environ['TASA_CONFIG'] = 'llama'

from baseline_vanilla_icl import VanillaICLTutor
from tasa_config_llama import TUTOR_MODEL, FORGETTING_SCORE_METHOD

def build_student_system_prompt(persona):
    """构建学生系统prompt"""
    return f"""You are a middle school student learning mathematics.

**Your Learning Profile:**
{persona}

**Instructions:**
- Answer questions naturally and honestly based on your understanding
- If you're unsure, express confusion or ask for clarification
- Show your work and reasoning when solving problems
- Don't pretend to understand if you're confused"""

def generate_vanilla_icl_dialogue(student_id, concept_text, dataset):
    """为一个学生生成28轮Vanilla-ICL dialogue"""
    
    # 输出目录
    output_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/{student_id}-{concept_text}.json'
    
    # 如果已存在，跳过
    if os.path.exists(output_file):
        return f"✅ 学生{student_id}已存在，跳过"
    
    try:
        # 加载学生persona
        persona_file = f'/mnt/localssd/bank/persona/{dataset}/data/{student_id}.json'
        with open(persona_file, 'r') as f:
            persona_list = json.load(f)
            # persona是一个列表，包含多个concept的描述
            # 我们组合所有描述或者找到对应concept的描述
            if isinstance(persona_list, list):
                # 尝试找到匹配的concept
                matching = [p for p in persona_list if p.get('concept_text') == concept_text]
                if matching:
                    persona = matching[0].get('description', '')
                else:
                    # 如果找不到匹配的，组合前3个concept的描述
                    descriptions = [p.get('description', '') for p in persona_list[:3]]
                    persona = '\n'.join(descriptions)
            else:
                persona = persona_list.get('description', '')
        
        # 初始化Vanilla-ICL tutor（使用llama）
        # VanillaICLTutor直接从config读取TUTOR_MODEL，不需要传参
        tutor = VanillaICLTutor()
        
        # 进行14轮对话（28 turns）
        dialogue = tutor.conduct_tutoring_session(
            concept_text=concept_text,
            max_rounds=14
        )
        
        if not dialogue:
            return f"❌ 学生{student_id}dialogue生成失败"
        
        # 保存dialogue
        with open(output_file, 'w') as f:
            json.dump(dialogue, f, indent=2)
        
        return f"✅ 学生{student_id}完成 ({len(dialogue)}轮)"
        
    except Exception as e:
        return f"❌ 学生{student_id}失败: {e}"

def main():
    """主函数"""
    
    # 只处理assist2017数据集（因为其他数据集样本少）
    dataset = 'assist2017'
    
    # 加载sampled students
    students_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    with open(students_file, 'r') as f:
        data = json.load(f)
        if 'sampled_students' in data:
            students = data['sampled_students']
        else:
            students = data.get('students', [])
    
    print('='*80)
    print(f'📝 生成Vanilla-ICL-llama 28轮Dialogue')
    print('='*80)
    print(f'Dataset: {dataset}')
    print(f'Students: {len(students)}')
    print(f'Tutor Model: {TUTOR_MODEL}')
    print('='*80)
    print()
    
    tasks = []
    for student_info in students:
        if isinstance(student_info, dict):
            student_id = student_info['student_id']
            concept = student_info['target_concept']
        else:
            # 如果是简单的student_id列表，需要从其他地方获取concept
            student_id = student_info
            # 尝试从现有dialogue文件推断concept
            tasa_dir = f'/mnt/localssd/bank/dialogue/TASA/{dataset}'
            existing_files = [f for f in os.listdir(tasa_dir) if f.startswith(f'{student_id}-')]
            if existing_files:
                concept = existing_files[0].replace(f'{student_id}-', '').replace('.json', '')
            else:
                print(f"⚠️  学生{student_id}找不到concept，跳过")
                continue
        
        tasks.append((student_id, concept))
    
    print(f"🚀 开始生成{len(tasks)}个dialogue（max_workers=10）\n")
    
    completed = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(generate_vanilla_icl_dialogue, sid, concept, dataset): (sid, concept)
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
    print(f'✅ Vanilla-ICL-llama 28轮dialogue生成完成！')
    print(f'📁 保存位置: /mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}/')
    print('='*80)

if __name__ == '__main__':
    main()

