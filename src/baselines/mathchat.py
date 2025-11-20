"""
Baseline 2: MathChat
使用calculator功能，解释答案并生成问题
"""

import json
import os
import re
from openai import OpenAI
from typing import List, Dict
from student_roleplay_evaluation import load_session

# 根据环境变量选择配置文件
_config_module = os.environ.get('TASA_CONFIG', 'tasa_config')
if _config_module == 'tasa_config_llama':
    from tasa_config_llama import ENDPOINT, GPT_ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
elif _config_module == 'tasa_config_qwen':
    from tasa_config_qwen import ENDPOINT, GPT_ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
elif _config_module == 'tasa_config_gpt':
    from tasa_config_gpt import ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
    GPT_ENDPOINT = ENDPOINT
else:
    from tasa_config import ENDPOINT, API_KEY, TUTOR_MODEL, STUDENT_MODEL
    GPT_ENDPOINT = ENDPOINT

from llm_client_unified import UnifiedLLMClient

def get_backbone_suffix():
    """根据TUTOR_MODEL确定backbone后缀"""
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''  # GPT默认无后缀

class MathChatTutor:
    def __init__(self):
        """初始化MathChat Tutor"""
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
        self.model = TUTOR_MODEL
        print("🔧 初始化MathChat Tutor (with calculator)")
    
    def execute_calculations(self, text: str) -> str:
        """解析并执行<calculate>标签中的计算"""
        def replace_calc(match):
            expr = match.group(1)
            try:
                result = eval(expr, {"__builtins__": {}}, {})
                return f"{expr} = {result}"
            except:
                return f"{expr} = [计算错误]"
        
        return re.sub(r'<calculate>(.*?)</calculate>', replace_calc, text)
    
    def conduct_tutoring_session(self, student_id: int, dataset: str,
                                concept_text: str, student_system_prompt: str) -> bool:
        """进行10轮教学对话"""
        print(f"\n🎓 MathChat Tutoring Session")
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        
        dialogue = []
        
        # Round 1: 学生请求
        student_request = f"I want to learn about {concept_text}"
        dialogue.append({
            "role": "user",
            "content": student_request,
            "round": 0
        })
        
        # 进行10轮教学
        for round_num in range(1, 11):
            print(f"📚 Round {round_num}")
            
            # 构建dialogue context
            dialogue_context = "\n".join([
                f"{'Student' if msg['role']=='user' else 'Tutor'}: {msg['content'][:200]}..."
                for msg in dialogue[-6:]
            ])
            
            if round_num == 1:
                prompt = f"""You are a math tutor with access to a calculator.
The student wants to learn about {concept_text}.

Task:
1) Generate a clear practice question about {concept_text}
2) You can use <calculate>expression</calculate> for any computation you need

Provide an engaging question."""
            else:
                last_student_answer = dialogue[-1]['content']
                
                prompt = f"""You are a math tutor with access to a calculator.

Dialogue: {dialogue_context}

Student's Last Answer:
{last_student_answer}

Task:
1) Explain student's answer with step-by-step reasoning (use <calculate>expression</calculate> for computations)
2) Generate next question

Provide educational feedback and the next question."""
            
            try:
                content = self.tutor_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                
                if content:
                    tutor_response = content
                else:
                    print(f"   ⚠️ Tutor回复为None，跳过")
                    return False
                
                # 执行计算
                tutor_response_with_calc = self.execute_calculations(tutor_response)
                
                dialogue.append({
                    "role": "assistant",
                    "content": tutor_response_with_calc,
                    "round": round_num
                })
                
            except Exception as e:
                print(f"   ❌ Tutor生成失败: {e}")
                return False
            
            # 学生回答
            if round_num < 10:
                student_prompt_text = f"""Based on the tutor's question, provide your answer.

Tutor's Question:
{tutor_response_with_calc}

Provide your answer."""
                
                try:
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
                    else:
                        student_answer = "I don't know"
                    
                    dialogue.append({
                        "role": "user",
                        "content": student_answer,
                        "round": round_num + 1
                    })
                    
                except Exception as e:
                    print(f"   ❌ Student回答失败: {e}")
                    return False
        
        # 保存对话
        backbone_suffix = get_backbone_suffix()
        dialogue_dir = f'/mnt/localssd/bank/dialogue/MathChat{backbone_suffix}/{dataset}'
        os.makedirs(dialogue_dir, exist_ok=True)
        
        dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
        
        with open(dialogue_file, 'w') as f:
            json.dump({
                "student_id": student_id,
                "dataset": dataset,
                "concept": concept_text,
                "method": "MathChat",
                "total_rounds": 10,
                "dialogue": dialogue
            }, f, indent=2)
        
        print(f"   ✅ Dialogue已保存")
        return True

