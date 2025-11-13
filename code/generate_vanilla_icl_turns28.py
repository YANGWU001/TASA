#!/usr/bin/env python3
"""
为Vanilla-ICL生成28轮完整dialogue
修复之前的实现问题
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading

from student_roleplay_evaluation import build_student_system_prompt, load_session
from baseline_vanilla_icl import VanillaICLTutor
from tasa_config_llama import STUDENT_MODEL, FORGETTING_SCORE_METHOD
from openai import OpenAI
from llm_client_unified import UnifiedLLMClient

# 全局锁
print_lock = Lock()
model_init_lock = Lock()

# 线程本地存储
thread_local = threading.local()

def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with print_lock:
        print(*args, **kwargs)

def get_tutor():
    """获取线程本地的Tutor实例"""
    if not hasattr(thread_local, 'tutor'):
        with model_init_lock:
            safe_print(f"   [Thread-{threading.current_thread().ident}] 初始化Vanilla-ICL Tutor...")
            thread_local.tutor = VanillaICLTutor()
    return thread_local.tutor

def generate_vanilla_icl_dialogue(student_id, dataset, concept_text, student_system_prompt, num_rounds=14):
    """
    生成Vanilla-ICL的dialogue
    num_rounds: tutor轮数（14轮 = 28个dialogue turns）
    """
    tutor = get_tutor()
    
    # 加载session获取persona
    session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
    session = load_session(session_file)
    persona_description = session['persona']['description']
    
    dialogue = []
    
    # Round 0: 学生请求
    student_request = f"I want to learn about {concept_text}"
    dialogue.append({
        "role": "user",
        "content": student_request,
        "round": 0
    })
    
    # 进行num_rounds轮教学
    for round_num in range(1, num_rounds + 1):
        # 构建tutor prompt
        if round_num == 1:
            # 第一轮：直接生成问题
            prompt = f"""You are a math tutor helping a student learn {concept_text}.

Student Profile:
{persona_description}

The student wants to learn about {concept_text}. Generate your first practice question for them.

Format:
- Provide a clear question appropriate for their level
- Make it engaging and educational"""
        else:
            # 后续轮次：解释上一题 + 生成新问题
            last_student_answer = dialogue[-1]['content']
            
            # 构建对话上下文
            dialogue_context = "\n".join([
                f"{'Student' if msg['role']=='user' else 'Tutor'}: {msg['content'][:200]}..."
                for msg in dialogue[-4:]  # 最近2轮对话
            ])
            
            prompt = f"""You are a math tutor helping a student learn {concept_text}.

Student Profile:
{persona_description}

Recent Dialogue:
{dialogue_context}

Student's Last Answer:
{last_student_answer}

Task:
1) Provide feedback on the student's answer (correct/incorrect with explanation)
2) Generate the next practice question to help them learn

Keep your response focused and educational."""
        
        # 调用LLM生成tutor回复
        tutor_response = tutor.tutor_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        if not tutor_response:
            raise Exception("Tutor回复为空")
        
        dialogue.append({
            "role": "assistant",
            "content": tutor_response,
            "round": round_num
        })
        
        # 学生回答（最后一轮不需要）
        if round_num < num_rounds:
            response = tutor.openai_client.chat.completions.create(
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

def process_single_student(student_id, dataset):
    """处理单个学生"""
    try:
        safe_print(f"\n{'='*80}")
        safe_print(f"🎓 学生 {student_id}")
        safe_print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        
        # 检查dialogue是否已存在
        dialogue_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL-turns28-llama/{dataset}/{FORGETTING_SCORE_METHOD}'
        dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
        
        if os.path.exists(dialogue_file):
            safe_print(f"   ✅ Dialogue已存在，跳过")
            return True, None
        
        # 生成dialogue
        safe_print(f"   📚 开始生成28轮dialogue...")
        student_prompt = build_student_system_prompt(session)
        
        dialogue = generate_vanilla_icl_dialogue(
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text,
            student_system_prompt=student_prompt,
            num_rounds=14  # 14轮 tutor = 28 dialogue turns
        )
        
        # 保存dialogue
        os.makedirs(dialogue_dir, exist_ok=True)
        with open(dialogue_file, 'w') as f:
            json.dump(dialogue, f, indent=2)
        
        safe_print(f"   ✅ Dialogue生成完成：{len(dialogue)}条消息")
        return True, None
        
    except Exception as e:
        safe_print(f"   ❌ 生成失败: {e}")
        import traceback
        safe_print(f"   {traceback.format_exc()}")
        return False, str(e)

def main():
    """主函数"""
    dataset = 'assist2017'
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
            return
    
    print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║          生成Vanilla-ICL 28轮完整dialogue                                   ║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"   数据集: {dataset}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   并行度: 10")
    print(f"{'='*80}\n")
    
    # 设置环境
    os.environ['TASA_CONFIG'] = 'tasa_config_llama'
    
    successful_count = 0
    failed_count = 0
    skipped_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(process_single_student, sid, dataset): sid 
            for sid in student_ids
        }
        
        for future in as_completed(futures):
            sid = futures[future]
            try:
                success, error = future.result()
                if success:
                    if error is None:
                        skipped_count += 1
                    else:
                        successful_count += 1
                else:
                    failed_count += 1
                
                total_processed = successful_count + failed_count + skipped_count
                print(f"\n📈 进度: {total_processed}/{len(student_ids)} ({total_processed*100/len(student_ids):.1f}%) | 成功: {successful_count} | 跳过: {skipped_count} | 失败: {failed_count}")
                
            except Exception as e:
                print(f"❌ 处理学生{sid}异常: {e}")
                failed_count += 1
    
    print(f"\n{'='*80}")
    print(f"\n✅ Vanilla-ICL 28轮dialogue生成完成！")
    print(f"   成功: {successful_count}")
    print(f"   跳过: {skipped_count}")
    print(f"   失败: {failed_count}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

