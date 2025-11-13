"""
TASA Tutoring核心模块
管理个性化教学对话流程
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

class TASATutor:
    def __init__(self):
        """初始化TASA Tutor"""
        print("🔧 初始化TASA Tutor...")
        
        # 初始化统一LLM客户端（用于TUTOR_MODEL）
        self.tutor_client = UnifiedLLMClient(TUTOR_MODEL)
        
        # 初始化OpenAI客户端（用于其他模型：STUDENT_MODEL, GRADER_MODEL等）
        self.openai_client = OpenAI(
            api_key=API_KEY,
            base_url=ENDPOINT
        )
        
        # 初始化RAG和重写模块
        self.rag = TASARAG()
        self.rewriter = MasteryRewriter()
        
        print("✅ TASA Tutor初始化完成")
    
    def generate_first_question(self, rewritten_persona: List[str], 
                               rewritten_memory: List[str],
                               concept_text: str) -> str:
        """
        生成第一个问题（学生表达想学习某个concept后）
        """
        system_message = """You are a personalized math tutor. Generate the first practice question for a student who wants to learn a specific concept. The question should be calibrated to the student's current knowledge state."""
        
        user_message = f"""[Student Profile (Forgetting-Adjusted)]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Recent Learning Events (Forgetting-Adjusted)]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Student Request]
The student wants to learn about: {concept_text}

[Task]
Generate an appropriate first practice question for this concept, tailored to the student's current knowledge level. The question should help assess and build their understanding."""
        
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
                                         rewritten_memory: List[str],
                                         conversation_history: List[Dict],
                                         concept_text: str) -> str:
        """
        生成讲解+下一个问题（第2-10轮）
        
        Args:
            conversation_history: List of {"role": "user/assistant", "content": "..."}
        """
        system_message = """You are a personalized math tutor. Generate the next instructional content that first explains the student's most recent response and then provides the next practice question, calibrated to the current retention state."""
        
        # 构建对话历史文本
        history_text = "\n".join([
            f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
            for msg in conversation_history[-4:]  # 只取最近4轮对话
        ])
        
        user_message = f"""[Student Profile (Forgetting-Adjusted)]
{chr(10).join(f'- {p}' for p in rewritten_persona)}

[Recent Learning Events (Forgetting-Adjusted)]
{chr(10).join(f'- {m}' for m in rewritten_memory)}

[Current Dialogue Context]
{history_text}

[Task]
Produce a response that includes:
(1) A concise explanation of the student's last answer (whether it's correct or incorrect, and why)
(2) The next question tailored to the student's current knowledge state

Keep your response clear, encouraging, and pedagogically sound."""
        
        try:
            content = self.tutor_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=TUTOR_TEMPERATURE,
                max_tokens=MAX_TOKENS_TUTOR
            )
            
            return content.strip() if content else "Let's continue with the next question."
        
        except Exception as e:
            print(f"⚠️ 生成讲解+问题失败: {e}")
            return "Let's move on to the next question."
    
    def get_student_response(self, question: str, student_prompt: str) -> str:
        """
        模拟学生回答（使用role-play）
        
        Args:
            question: Tutor提出的问题
            student_prompt: 学生的system prompt（包含persona等信息）
        """
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
            return content.strip() if content else "I'm not sure how to answer this."
        
        except Exception as e:
            print(f"⚠️ 获取学生回答失败: {e}")
            return "I'm not sure."
    
    def conduct_tutoring_session(self, student_id: int, dataset: str, 
                                 concept_text: str,
                                 student_system_prompt: str) -> List[Dict]:
        """
        进行完整的tutoring session（10轮）
        
        Args:
            student_id: 学生ID
            dataset: 数据集名称
            concept_text: 学习的concept
            student_system_prompt: 学生role-play的system prompt
        
        Returns:
            dialogue: List of {"role": "user/assistant", "round": int, "content": str}
        """
        print(f"\n🎓 开始Tutoring Session")
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        print(f"   轮数: {NUM_TUTORING_ROUNDS}")
        
        dialogue = []
        
        # 第一轮：学生表达想学习
        initial_query = f"I want to learn about {concept_text}"
        dialogue.append({
            "role": "user",
            "round": 0,
            "content": initial_query
        })
        
        # RAG检索并重写
        print(f"\n📚 Round 1: 生成初始问题")
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
        
        # 生成第一个问题
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
        
        print(f"   ✅ 问题已生成")
        
        # 后续9轮：学生回答 -> RAG -> 讲解+问题
        for round_num in range(2, NUM_TUTORING_ROUNDS + 1):
            print(f"\n📚 Round {round_num}")
            
            # 学生回答上一轮的问题
            last_question = dialogue[-1]['content']
            student_answer = self.get_student_response(last_question, student_system_prompt)
            
            dialogue.append({
                "role": "user",
                "round": round_num,
                "content": student_answer
            })
            
            print(f"   📝 学生已回答")
            
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
            
            print(f"   ✅ 讲解+问题已生成")
        
        print(f"\n✅ Tutoring Session完成！共{len(dialogue)}条消息")
        
        return dialogue
    
    def save_dialogue(self, dialogue: List[Dict], student_id: int, concept_text: str, dataset: str, backbone_suffix: str = ''):
        """保存对话到文件，根据backbone使用不同目录"""
        # 创建目录 (加上backbone后缀以区分不同模型生成的dialogue，加上FS_METHOD以区分不同遗忘曲线方法)
        from tasa_config import FORGETTING_SCORE_METHOD
        dialogue_dir = f"{DIALOGUE_DIR}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}"
        os.makedirs(dialogue_dir, exist_ok=True)
        
        # 保存
        filename = f"{dialogue_dir}/{student_id}-{concept_text}.json"
        
        dialogue_data = {
            "student_id": student_id,
            "dataset": dataset,
            "concept_text": concept_text,
            "num_rounds": NUM_TUTORING_ROUNDS,
            "dialogue": dialogue
        }
        
        with open(filename, 'w') as f:
            json.dump(dialogue_data, f, indent=2)
        
        print(f"💾 对话已保存至: {filename}")
        return filename

# 测试
if __name__ == "__main__":
    from student_roleplay_evaluation import build_student_system_prompt, load_session
    
    # 初始化tutor
    tutor = TASATutor()
    
    # 加载学生session
    session = load_session('/mnt/localssd/bank/session/assist2017/1.json')
    
    # 构建学生的system prompt
    student_prompt = build_student_system_prompt(session)
    
    # 进行tutoring
    dialogue = tutor.conduct_tutoring_session(
        student_id=1,
        dataset="assist2017",
        concept_text=session['concept_text'],
        student_system_prompt=student_prompt
    )
    
    # 保存对话
    tutor.save_dialogue(dialogue, 1, session['concept_text'], "assist2017")
    
    # 显示对话摘要
    print(f"\n{'='*80}")
    print(f"对话摘要")
    print(f"{'='*80}")
    for msg in dialogue[:4]:  # 只显示前4条
        role = "学生" if msg["role"] == "user" else "Tutor"
        print(f"\n[Round {msg['round']}] {role}:")
        print(f"{msg['content'][:200]}...")

