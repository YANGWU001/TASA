"""
Baseline 3: TutorLLM
使用persona + 3条相关memory (RAG)，不考虑knowledge tracing
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

class TutorLLM:
    def __init__(self):
        """初始化TutorLLM"""
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=GPT_ENDPOINT)
        self.model = TUTOR_MODEL
        
        # 加载embedding模型用于RAG
        print("🔧 初始化TutorLLM...")
        print("   加载Embedding模型...")
        self.embed_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        print("   ✅ TutorLLM初始化完成")
    
    def retrieve_memory(self, student_id: int, dataset: str, query: str) -> List[str]:
        """
        从memory中检索最相关的3条
        
        Args:
            student_id: 学生ID
            dataset: 数据集
            query: 查询文本
        
        Returns:
            前3条最相关的memory descriptions
        """
        # 加载memory
        memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{student_id}.json'
        
        if not os.path.exists(memory_file):
            return []
        
        with open(memory_file) as f:
            memories = json.load(f)
        
        if not memories:
            return []
        
        # 加载memory embeddings
        memory_emb_file = f'/mnt/localssd/bank/memory/{dataset}/embeddings/{student_id}_description.npz'
        
        if not os.path.exists(memory_emb_file):
            return [m['description'] for m in memories[:3]]
        
        memory_embeddings = np.load(memory_emb_file)['embeddings']
        
        # 编码query
        query_embedding = self.embed_model.encode([query])['dense_vecs'][0]
        
        # 计算相似度
        similarities = np.dot(memory_embeddings, query_embedding)
        
        # 获取top 3
        top_3_indices = np.argsort(similarities)[-3:][::-1]
        
        return [memories[i]['description'] for i in top_3_indices if i < len(memories)]
    
    def conduct_tutoring_session(self, student_id: int, dataset: str,
                                concept_text: str, student_system_prompt: str) -> bool:
        """进行10轮教学对话"""
        print(f"\n🎓 TutorLLM Tutoring Session")
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        
        # 加载session获取persona
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        persona_description = session['persona']['description']
        
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
            
            # RAG: 检索相关memory
            if round_num == 1:
                query = f"learning {concept_text}"
            else:
                query = dialogue[-1]['content'][:200]  # 学生的回答
            
            relevant_memories = self.retrieve_memory(student_id, dataset, query)
            
            # 构建memory context
            memory_context = "\n".join([f"- {mem}" for mem in relevant_memories])
            
            # 构建dialogue context
            dialogue_context = "\n".join([
                f"{'Student' if msg['role']=='user' else 'Tutor'}: {msg['content'][:200]}..."
                for msg in dialogue[-4:]
            ])
            
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
        dialogue_dir = f'/mnt/localssd/bank/dialogue/TutorLLM{backbone_suffix}/{dataset}'
        os.makedirs(dialogue_dir, exist_ok=True)
        
        dialogue_file = f'{dialogue_dir}/{student_id}-{concept_text}.json'
        
        with open(dialogue_file, 'w') as f:
            json.dump({
                "student_id": student_id,
                "dataset": dataset,
                "concept": concept_text,
                "method": "TutorLLM",
                "total_rounds": 10,
                "dialogue": dialogue
            }, f, indent=2)
        
        print(f"   ✅ Dialogue已保存")
        return True

