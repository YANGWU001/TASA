"""
TASA Tutoring Ablation Variants
提供3个ablation变体用于消融实验
"""

import json
import os
from typing import List, Dict, Tuple
from openai import OpenAI
from tqdm import tqdm

from tasa_config import *
from tasa_rag import TASARAG
from tasa_rewrite import MasteryRewriter
from llm_client_unified import UnifiedLLMClient

class TASATutorWithoutPersona:
    """
    TASA Tutor Ablation: w/o Persona
    不使用persona信息，只使用memory
    """
    def __init__(self):
        """初始化TASA Tutor (w/o Persona)"""
        print("🔧 初始化TASA Tutor (w/o Persona)...")
        
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
        self.rag = TASARAG()
        self.rewriter = MasteryRewriter()
        
        print("✅ TASA Tutor (w/o Persona)初始化完成")
    
    def generate_first_question(self, rewritten_memory: List[str], concept_text: str) -> str:
        """生成第一个问题（不使用persona）"""
        system_message = """You are a personalized math tutor. Generate the first practice question for a student who wants to learn a specific concept."""
        
        user_message = f"""[Recent Learning Events (Forgetting-Adjusted)]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Student Request]
The student wants to learn about: {concept_text}

[Task]
Generate an appropriate first practice question for this concept."""
        
        try:
            content = self.tutor_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=TUTOR_TEMPERATURE,
                max_tokens=MAX_TOKENS_TUTOR
            )
            return content.strip() if content else "Let's start with a basic question about this concept."
        except Exception as e:
            print(f"⚠️ 生成第一个问题失败: {e}")
            return "Let's begin. Can you explain what you know about this concept?"
    
    def generate_explanation_and_question(self, rewritten_memory: List[str],
                                         conversation_history: List[Dict],
                                         concept_text: str) -> str:
        """生成讲解+下一个问题（不使用persona）"""
        system_message = """You are a personalized math tutor. Generate the next instructional content."""
        
        history_text = "\n".join([
            f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
            for msg in conversation_history[-4:]
        ])
        
        user_message = f"""[Recent Learning Events (Forgetting-Adjusted)]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Current Dialogue Context]
{history_text}

[Task]
Produce a response that includes:
(1) A concise explanation of the student's last answer
(2) The next question tailored to the student's current knowledge state"""
        
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
            print(f"⚠️ 生成讲解+问题失败: {e}")
            return "Let's move on."
    
    def get_student_response(self, question: str, student_prompt: str) -> str:
        """模拟学生回答"""
        try:
            response = self.openai_client.chat.completions.create(
                model=STUDENT_MODEL,
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
            print(f"⚠️ 获取学生回答失败: {e}")
            return "I'm not sure."
    
    def conduct_tutoring_session(self, student_id: int, dataset: str, 
                                 concept_text: str,
                                 student_system_prompt: str) -> List[Dict]:
        """进行完整的tutoring session（10轮，不使用persona）"""
        print(f"\n🎓 开始Tutoring Session (w/o Persona)")
        dialogue = []
        
        initial_query = f"I want to learn about {concept_text}"
        dialogue.append({"role": "user", "round": 0, "content": initial_query})
        
        # 检索但只使用memory
        top_persona, top_memory = self.rag.retrieve_and_rerank(
            query=initial_query,
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text
        )
        
        # 重写memory（persona不使用）
        _, rewritten_memory = self.rewriter.rewrite_top_items(
            top_persona, top_memory,
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text
        )
        
        first_question = self.generate_first_question(rewritten_memory, concept_text)
        
        dialogue.append({
            "role": "assistant",
            "round": 1,
            "content": first_question,
            "retrieved_memory": [m['description'] for m in top_memory],
            "rewritten_memory": rewritten_memory
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
            
            _, rewritten_memory = self.rewriter.rewrite_top_items(
                top_persona, top_memory,
                student_id=student_id,
                dataset=dataset,
                concept_text=concept_text
            )
            
            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                   for msg in dialogue]
            
            explanation_and_question = self.generate_explanation_and_question(
                rewritten_memory, conversation_history, concept_text
            )
            
            dialogue.append({
                "role": "assistant",
                "round": round_num,
                "content": explanation_and_question,
                "retrieved_memory": [m['description'] for m in top_memory],
                "rewritten_memory": rewritten_memory
            })
        
        return dialogue
    
    def save_dialogue(self, dialogue: List[Dict], student_id: int, 
                     concept_text: str, dataset: str, backbone_suffix: str = ''):
        """保存dialogue"""
        from tasa_config import FORGETTING_SCORE_METHOD
        save_dir = f'/mnt/localssd/bank/dialogue/TASA-woPersona{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
        os.makedirs(save_dir, exist_ok=True)
        
        save_file = f'{save_dir}/{student_id}-{concept_text}.json'
        with open(save_file, 'w') as f:
            json.dump(dialogue, f, indent=2)


class TASATutorWithoutMemory:
    """
    TASA Tutor Ablation: w/o Memory
    不使用memory信息，只使用persona
    """
    def __init__(self):
        """初始化TASA Tutor (w/o Memory)"""
        print("🔧 初始化TASA Tutor (w/o Memory)...")
        
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
        self.rag = TASARAG()
        self.rewriter = MasteryRewriter()
        
        print("✅ TASA Tutor (w/o Memory)初始化完成")
    
    def generate_first_question(self, rewritten_persona: List[str], concept_text: str) -> str:
        """生成第一个问题（不使用memory）"""
        system_message = """You are a personalized math tutor. Generate the first practice question for a student who wants to learn a specific concept."""
        
        user_message = f"""[Student Profile (Forgetting-Adjusted)]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Student Request]
The student wants to learn about: {concept_text}

[Task]
Generate an appropriate first practice question for this concept, tailored to the student's profile."""
        
        try:
            content = self.tutor_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=TUTOR_TEMPERATURE,
                max_tokens=MAX_TOKENS_TUTOR
            )
            return content.strip() if content else "Let's start with a basic question about this concept."
        except Exception as e:
            print(f"⚠️ 生成第一个问题失败: {e}")
            return "Let's begin. Can you explain what you know about this concept?"
    
    def generate_explanation_and_question(self, rewritten_persona: List[str],
                                         conversation_history: List[Dict],
                                         concept_text: str) -> str:
        """生成讲解+下一个问题（不使用memory）"""
        system_message = """You are a personalized math tutor. Generate the next instructional content."""
        
        history_text = "\n".join([
            f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
            for msg in conversation_history[-4:]
        ])
        
        user_message = f"""[Student Profile (Forgetting-Adjusted)]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Current Dialogue Context]
{history_text}

[Task]
Produce a response that includes:
(1) A concise explanation of the student's last answer
(2) The next question tailored to the student's profile"""
        
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
            print(f"⚠️ 生成讲解+问题失败: {e}")
            return "Let's move on."
    
    def get_student_response(self, question: str, student_prompt: str) -> str:
        """模拟学生回答"""
        try:
            response = self.openai_client.chat.completions.create(
                model=STUDENT_MODEL,
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
            print(f"⚠️ 获取学生回答失败: {e}")
            return "I'm not sure."
    
    def conduct_tutoring_session(self, student_id: int, dataset: str, 
                                 concept_text: str,
                                 student_system_prompt: str) -> List[Dict]:
        """进行完整的tutoring session（10轮，不使用memory）"""
        print(f"\n🎓 开始Tutoring Session (w/o Memory)")
        dialogue = []
        
        initial_query = f"I want to learn about {concept_text}"
        dialogue.append({"role": "user", "round": 0, "content": initial_query})
        
        # 检索但只使用persona
        top_persona, top_memory = self.rag.retrieve_and_rerank(
            query=initial_query,
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text
        )
        
        # 重写persona（memory不使用）
        rewritten_persona, _ = self.rewriter.rewrite_top_items(
            top_persona, top_memory,
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text
        )
        
        first_question = self.generate_first_question(rewritten_persona, concept_text)
        
        dialogue.append({
            "role": "assistant",
            "round": 1,
            "content": first_question,
            "retrieved_persona": [p['description'] for p in top_persona],
            "rewritten_persona": rewritten_persona
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
            
            rewritten_persona, _ = self.rewriter.rewrite_top_items(
                top_persona, top_memory,
                student_id=student_id,
                dataset=dataset,
                concept_text=concept_text
            )
            
            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                   for msg in dialogue]
            
            explanation_and_question = self.generate_explanation_and_question(
                rewritten_persona, conversation_history, concept_text
            )
            
            dialogue.append({
                "role": "assistant",
                "round": round_num,
                "content": explanation_and_question,
                "retrieved_persona": [p['description'] for p in top_persona],
                "rewritten_persona": rewritten_persona
            })
        
        return dialogue
    
    def save_dialogue(self, dialogue: List[Dict], student_id: int, 
                     concept_text: str, dataset: str, backbone_suffix: str = ''):
        """保存dialogue"""
        from tasa_config import FORGETTING_SCORE_METHOD
        save_dir = f'/mnt/localssd/bank/dialogue/TASA-woMemory{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
        os.makedirs(save_dir, exist_ok=True)
        
        save_file = f'{save_dir}/{student_id}-{concept_text}.json'
        with open(save_file, 'w') as f:
            json.dump(dialogue, f, indent=2)


class TASATutorWithoutForgetting:
    """
    TASA Tutor Ablation: w/o Forgetting Score
    使用persona和memory，但不进行forgetting-based重写
    """
    def __init__(self):
        """初始化TASA Tutor (w/o Forgetting)"""
        print("🔧 初始化TASA Tutor (w/o Forgetting)...")
        
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
        self.rag = TASARAG()
        # 不使用rewriter
        
        print("✅ TASA Tutor (w/o Forgetting)初始化完成")
    
    def generate_first_question(self, persona_desc: List[str], memory_desc: List[str], 
                               concept_text: str) -> str:
        """生成第一个问题（使用原始描述，不重写）"""
        system_message = """You are a personalized math tutor. Generate the first practice question for a student who wants to learn a specific concept."""
        
        user_message = f"""[Student Profile]
{chr(10).join(f'- {p}' for p in persona_desc)}

[Recent Learning Events]
{chr(10).join(f'- {m}' for m in memory_desc)}

[Student Request]
The student wants to learn about: {concept_text}

[Task]
Generate an appropriate first practice question for this concept."""
        
        try:
            content = self.tutor_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=TUTOR_TEMPERATURE,
                max_tokens=MAX_TOKENS_TUTOR
            )
            return content.strip() if content else "Let's start with a basic question about this concept."
        except Exception as e:
            print(f"⚠️ 生成第一个问题失败: {e}")
            return "Let's begin. Can you explain what you know about this concept?"
    
    def generate_explanation_and_question(self, persona_desc: List[str], 
                                         memory_desc: List[str],
                                         conversation_history: List[Dict],
                                         concept_text: str) -> str:
        """生成讲解+下一个问题（使用原始描述，不重写）"""
        system_message = """You are a personalized math tutor. Generate the next instructional content."""
        
        history_text = "\n".join([
            f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
            for msg in conversation_history[-4:]
        ])
        
        user_message = f"""[Student Profile]
{chr(10).join(f'- {p}' for p in persona_desc)}

[Recent Learning Events]
{chr(10).join(f'- {m}' for m in memory_desc)}

[Current Dialogue Context]
{history_text}

[Task]
Produce a response that includes:
(1) A concise explanation of the student's last answer
(2) The next question tailored to the student's knowledge state"""
        
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
            print(f"⚠️ 生成讲解+问题失败: {e}")
            return "Let's move on."
    
    def get_student_response(self, question: str, student_prompt: str) -> str:
        """模拟学生回答"""
        try:
            response = self.openai_client.chat.completions.create(
                model=STUDENT_MODEL,
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
            print(f"⚠️ 获取学生回答失败: {e}")
            return "I'm not sure."
    
    def conduct_tutoring_session(self, student_id: int, dataset: str, 
                                 concept_text: str,
                                 student_system_prompt: str) -> List[Dict]:
        """进行完整的tutoring session（10轮，不进行forgetting重写）"""
        print(f"\n🎓 开始Tutoring Session (w/o Forgetting)")
        dialogue = []
        
        initial_query = f"I want to learn about {concept_text}"
        dialogue.append({"role": "user", "round": 0, "content": initial_query})
        
        # 检索，直接使用原始描述
        top_persona, top_memory = self.rag.retrieve_and_rerank(
            query=initial_query,
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text
        )
        
        # 不重写，直接使用原始描述
        persona_desc = [p['description'] for p in top_persona]
        memory_desc = [m['description'] for m in top_memory]
        
        first_question = self.generate_first_question(persona_desc, memory_desc, concept_text)
        
        dialogue.append({
            "role": "assistant",
            "round": 1,
            "content": first_question,
            "retrieved_persona": persona_desc,
            "retrieved_memory": memory_desc
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
            
            persona_desc = [p['description'] for p in top_persona]
            memory_desc = [m['description'] for m in top_memory]
            
            conversation_history = [{"role": msg["role"], "content": msg["content"]} 
                                   for msg in dialogue]
            
            explanation_and_question = self.generate_explanation_and_question(
                persona_desc, memory_desc, conversation_history, concept_text
            )
            
            dialogue.append({
                "role": "assistant",
                "round": round_num,
                "content": explanation_and_question,
                "retrieved_persona": persona_desc,
                "retrieved_memory": memory_desc
            })
        
        return dialogue
    
    def save_dialogue(self, dialogue: List[Dict], student_id: int, 
                     concept_text: str, dataset: str, backbone_suffix: str = ''):
        """保存dialogue"""
        from tasa_config import FORGETTING_SCORE_METHOD
        save_dir = f'/mnt/localssd/bank/dialogue/TASA-woForgetting{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}'
        os.makedirs(save_dir, exist_ok=True)
        
        save_file = f'{save_dir}/{student_id}-{concept_text}.json'
        with open(save_file, 'w') as f:
            json.dump(dialogue, f, indent=2)

