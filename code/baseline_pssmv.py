"""
Baseline 4: PSS-MV (Personalized Student Style - Memory View)
先用LLM从memory总结learning style，然后根据style生成tutoring
"""

import json
import os
import numpy as np
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
from FlagEmbedding import BGEM3FlagModel

def get_backbone_suffix():
    """根据TUTOR_MODEL确定backbone后缀"""
    if 'llama' in TUTOR_MODEL.lower():
        return '-llama'
    elif 'qwen' in TUTOR_MODEL.lower():
        return '-qwen'
    else:
        return ''  # GPT默认无后缀

class PSSMV:
    def __init__(self):
        """初始化PSS-MV"""
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
        self.model = TUTOR_MODEL
        
        print("🔧 初始化PSS-MV...")
        print("   加载Embedding模型...")
        self.embed_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        print("   ✅ PSS-MV初始化完成")
    
    def retrieve_memory(self, student_id: int, dataset: str, query: str) -> List[str]:
        """检索3条相关memory"""
        memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{student_id}.json'
        
        if not os.path.exists(memory_file):
            return []
        
        with open(memory_file) as f:
            memories = json.load(f)
        
        if not memories:
            return []
        
        memory_emb_file = f'/mnt/localssd/bank/memory/{dataset}/embeddings/{student_id}_description.npz'
        
        if not os.path.exists(memory_emb_file):
            return [m['description'] for m in memories[:3]]
        
        memory_embeddings = np.load(memory_emb_file)['embeddings']
        query_embedding = self.embed_model.encode([query])['dense_vecs'][0]
        similarities = np.dot(memory_embeddings, query_embedding)
        top_3_indices = np.argsort(similarities)[-3:][::-1]
        
        return [memories[i]['description'] for i in top_3_indices if i < len(memories)]
    
    def infer_learning_style(self, student_id: int, dataset: str, concept_text: str) -> str:
        """
        从memory推断学习风格
        
        Returns:
            learning style描述
        """
        # 检索相关memory
        memories = self.retrieve_memory(student_id, dataset, f"learning {concept_text}")
        
        if not memories:
            return "a student who benefits from clear explanations and step-by-step guidance"
        
        # 使用LLM总结learning style
        memory_text = "\n".join([f"- {mem}" for mem in memories])
        
        prompt = f"""Based on the following student's past learning interactions, infer their learning style and preferences.

Past Learning Interactions:
{memory_text}

Provide a brief description of this student's learning style (e.g., "visual learner who prefers diagrams", "step-by-step learner who needs detailed explanations", "quick learner who prefers challenging problems", etc.)

Learning Style:"""
        
        try:
            content = self.tutor_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            learning_style = response.choices[0].message.content.strip()
            return learning_style
            
        except Exception as e:
            print(f"   ⚠️ Learning style推断失败: {e}")
            return "a student who needs personalized guidance"
    
    def conduct_tutoring_session(self, student_id: int, dataset: str,
                                concept_text: str, student_system_prompt: str) -> bool:
        """进行10轮教学对话"""
        print(f"\n🎓 PSS-MV Tutoring Session")
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        
        # 推断learning style
        print(f"   🔍 推断learning style...")
        learning_style = self.infer_learning_style(student_id, dataset, concept_text)
        print(f"   Learning Style: {learning_style}")
        
        dialogue = []
        
        # Round 1
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
                for msg in dialogue[-4:]
            ])
            
            if round_num == 1:
                prompt = f"""You are a personalized tutor.
                
Student's Learning Style: {learning_style}

The student wants to learn about {concept_text}.

Task: Adapt tutoring to student's learning preferences. Generate your first question suited to their learning style."""
            else:
                last_student_answer = dialogue[-1]['content']
                
                prompt = f"""You are a personalized tutor.

Student's Learning Style: {learning_style}

Dialogue: {dialogue_context}

Student's Last Answer:
{last_student_answer}

Task: Adapt tutoring to student's learning preferences.
1) Provide feedback suited to their learning style
2) Generate next question that matches their preferences"""
            
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
                
                dialogue.append({
                    "role": "assistant",
                    "content": tutor_response,
                    "round": round_num
                })
                
            except Exception as e:
                print(f"   ❌ Tutor生成失败: {e}")
                return False
            
            # 学生回答
            if round_num < 10:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=STUDENT_MODEL,  # Student roleplay固定使用GPT
                        messages=[
                            {"role": "system", "content": student_system_prompt},
                            {"role": "user", "content": f"Answer the tutor's question:\n{tutor_response}"}
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
        dialogue_dir = f'/mnt/localssd/bank/dialogue/PSS-MV{backbone_suffix}/{dataset}'
        os.makedirs(dialogue_dir, exist_ok=True)
        
        dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
        
        with open(dialogue_file, 'w') as f:
            json.dump({
                "student_id": student_id,
                "dataset": dataset,
                "concept": concept_text,
                "method": "PSS-MV",
                "learning_style": learning_style,
                "total_rounds": 10,
                "dialogue": dialogue
            }, f, indent=2)
        
        print(f"   ✅ Dialogue已保存")
        return True

