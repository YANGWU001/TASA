"""
Baseline 1: Vanilla ICL (In-Context Learning)
只使用persona description，不涉及knowledge tracing和memory
"""

import json
import os
from openai import OpenAI
from typing import List, Dict
from student_roleplay_evaluation import load_session

# 从tasa_config导入API配置（根据环境变量选择）
import os
import sys

# 根据环境变量选择配置文件
_config_module = os.environ.get('TASA_CONFIG', 'tasa_config')
if _config_module == 'tasa_config_llama':
    from tasa_config_llama import ENDPOINT, GPT_ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
elif _config_module == 'tasa_config_qwen':
    from tasa_config_qwen import ENDPOINT, GPT_ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
elif _config_module == 'tasa_config_gpt':
    from tasa_config_gpt import ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
    GPT_ENDPOINT = ENDPOINT  # GPT config uses same endpoint
else:
    from tasa_config import ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
    GPT_ENDPOINT = ENDPOINT  # Default uses same endpoint

from llm_client_unified import UnifiedLLMClient

def get_backbone_suffix():
    """根据TUTOR_MODEL确定backbone后缀"""
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''  # GPT默认无后缀

class VanillaICLTutor:
    def __init__(self):
        """初始化Vanilla ICL Tutor"""
        # Tutor使用统一客户端支持不同backbone (llama/qwen/gpt)
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        # Student roleplay固定使用GPT endpoint
        print(f"   🔍 DEBUG: GPT_ENDPOINT={GPT_ENDPOINT}")
        print(f"   🔍 DEBUG: STUDENT_MODEL={STUDENT_MODEL}")
        self.openai_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
        print(f"   🔍 DEBUG: OpenAI client base_url={self.openai_client.base_url}")
        self.model = TUTOR_MODEL
        print("🔧 初始化Vanilla ICL Tutor")
    
    def conduct_tutoring_session(self, student_id: int, dataset: str, 
                                concept_text: str, student_system_prompt: str) -> bool:
        """
        进行10轮教学对话
        
        Args:
            student_id: 学生ID
            dataset: 数据集
            concept_text: 概念名称
            student_system_prompt: 学生的system prompt
        """
        print(f"\n🎓 Vanilla ICL Tutoring Session")
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        
        # 加载session获取persona
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        # 提取persona description
        persona_description = session['persona']['description']
        
        # 初始化对话历史
        dialogue = []
        
        # Round 1: 学生请求学习
        student_request = f"I want to learn about {concept_text}"
        dialogue.append({
            "role": "user",
            "content": student_request,
            "round": 0
        })
        
        # 进行10轮教学
        for round_num in range(1, 11):
            print(f"📚 Round {round_num}")
            
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
                # 获取学生的上一次回答
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
            try:
                tutor_response = self.tutor_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                
                if not tutor_response:
                    print(f"   ⚠️ Tutor回复为空，跳过")
                    return False
                
                dialogue.append({
                    "role": "assistant",
                    "content": tutor_response,
                    "round": round_num
                })
                
            except Exception as e:
                print(f"   ❌ Tutor生成失败: {e}")
                return False
            
            # 学生回答（如果不是最后一轮）
            if round_num < 10:
                student_prompt_text = f"""Based on the tutor's question, provide your answer.

Student Profile: {persona_description}

Tutor's Question:
{tutor_response}

Provide your answer as this student would."""
                
                try:
                    print(f"   🔍 DEBUG: Calling OpenAI with model={STUDENT_MODEL}, base_url={self.openai_client.base_url}")
                    response = self.openai_client.chat.completions.create(
                        model=STUDENT_MODEL,  # Student roleplay固定使用GPT
                        messages=[
                            {"role": "system", "content": student_system_prompt},
                            {"role": "user", "content": student_prompt_text}
                        ],
                        temperature=0.7,
                        max_tokens=300
                    )
                    
                    if response.choices[0].message.content:
                        student_answer = response.choices[0].message.content
                        print(f"   ✅ Student回答成功")
                    else:
                        print(f"   ⚠️ Student回复为None，使用默认回答")
                        student_answer = "I don't know"
                    
                    dialogue.append({
                        "role": "user",
                        "content": student_answer,
                        "round": round_num + 1
                    })
                    
                except Exception as e:
                    print(f"   ❌ Student回答失败: {e}")
                    print(f"   🔍 DEBUG: Exception type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
                    return False
        
        # 保存对话
        backbone_suffix = get_backbone_suffix()
        dialogue_dir = f'/mnt/localssd/bank/dialogue/Vanilla-ICL{backbone_suffix}/{dataset}'
        os.makedirs(dialogue_dir, exist_ok=True)
        
        dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
        
        dialogue_data = {
            "student_id": student_id,
            "dataset": dataset,
            "concept": concept_text,
            "method": "Vanilla-ICL",
            "total_rounds": 10,
            "dialogue": dialogue
        }
        
        with open(dialogue_file, 'w') as f:
            json.dump(dialogue_data, f, indent=2)
        
        print(f"   ✅ Dialogue已保存: {dialogue_file}")
        return True

if __name__ == "__main__":
    # 测试
    tutor = VanillaICLTutor()
    from student_roleplay_evaluation import build_student_system_prompt, load_session
    
    student_id = 1
    dataset = 'assist2017'
    
    session = load_session(f'/mnt/localssd/bank/session/{dataset}/{student_id}.json')
    concept_text = session['concept_text']
    student_prompt = build_student_system_prompt(session)
    
    tutor.conduct_tutoring_session(student_id, dataset, concept_text, student_prompt)

