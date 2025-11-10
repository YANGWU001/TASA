"""
TASA Mastery Rewrite模块
基于forgetting curve重写persona和memory的描述
"""

import json
from typing import List, Dict, Tuple
from openai import OpenAI

from tasa_config import *

class MasteryRewriter:
    def __init__(self):
        """初始化Mastery重写模块"""
        print("🔧 初始化Mastery Rewriter...")
        
        self.client = OpenAI(
            api_key=API_KEY,
            base_url=ENDPOINT
        )
        
        print("✅ Mastery Rewriter初始化完成")
    
    def load_forgetting_info(self, student_id: int, dataset: str, concept_text: str) -> Dict:
        """加载学生的forgetting curve信息"""
        session_file = f"{SESSION_DIR}/{dataset}/{student_id}.json"
        
        with open(session_file) as f:
            session = json.load(f)
        
        # 提取forgetting信息
        delta_t_minutes = session.get('delta_t_minutes', 0)
        delta_t_days = delta_t_minutes / (24 * 60)  # 转换为天数
        
        # 计算forgetting score
        # 根据FORGETTING_SCORE_METHOD从session中提取对应method的FS
        from tasa_config import FORGETTING_SCORE_METHOD
        
        if FORGETTING_SCORE_METHOD == "simple_time":
            # 使用简单时间衰减公式：F(t) = 1 - 1/(1 + t/7)  (7天半遗忘)
            forgetting_score = 1 - 1 / (1 + delta_t_days / 7)
            forgetting_level = get_forgetting_level(forgetting_score)
        elif FORGETTING_SCORE_METHOD in ["history", "lpkt", "dkt", "akt", "simplekt"]:
            # 从session的methods中提取对应method的FS
            if 'methods' in session and FORGETTING_SCORE_METHOD in session['methods']:
                method_data = session['methods'][FORGETTING_SCORE_METHOD]
                forgetting_score = method_data.get('fs', 0.0)
                # 直接使用method中的level（映射：medium -> moderate, high -> high, low -> low）
                method_level = method_data.get('level', '')
                if method_level == 'medium':
                    forgetting_level = 'moderate'
                elif method_level == 'high':
                    forgetting_level = 'high'
                elif method_level == 'low':
                    forgetting_level = 'low'
                else:
                    # 如果level不存在，不使用get_forgetting_level，而是根据FS范围判断
                    # 根据methods的判断逻辑：high(>0.3), medium(0.15-0.3), low(<0.15)
                    if forgetting_score > 0.3:
                        forgetting_level = 'high'
                    elif forgetting_score > 0.15:
                        forgetting_level = 'moderate'
                    else:
                        forgetting_level = 'low'
            else:
                # 如果method不存在，fallback到simple_time
                print(f"   ⚠️  Method {FORGETTING_SCORE_METHOD} not found, fallback to simple_time")
                forgetting_score = 1 - 1 / (1 + delta_t_days / 7)
                forgetting_level = get_forgetting_level(forgetting_score)
        else:
            raise ValueError(f"Unknown FORGETTING_SCORE_METHOD: {FORGETTING_SCORE_METHOD}")
        
        # 获取mastery
        mastery = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        
        return {
            'concept': concept_text,
            'mastery': mastery,
            'delta_t_days': delta_t_days,
            'delta_t_minutes': delta_t_minutes,
            'forgetting_score': forgetting_score,
            'forgetting_level': forgetting_level  # 使用前面计算好的level，不要重新计算
        }
    
    def rewrite_description(self, description: str, concept: str, 
                           mastery: float, delta_t_days: float,
                           forgetting_score: float, forgetting_level: str) -> str:
        """
        使用LLM重写description，考虑forgetting curve
        """
        system_message = """You are a personalized math tutor. Given a student's original state for a concept, including mastery, last practice interval, and forgetting score, rewrite the description to reflect time-dependent forgetting. Output only the updated description, concise and specific to the concept."""
        
        user_message = f"""The student's original state: "{description}" for concept "{concept}", with mastery {mastery:.2f}.
This concept was last practiced {delta_t_days:.1f} days ago.

Forgetting Score: {forgetting_score:.4f} (range: 0-1, where higher values indicate more forgetting)
Forgetting Level: {forgetting_level} - {FORGETTING_LEVELS[forgetting_level]}

Rewrite the description to reflect the current knowledge state after forgetting."""
        
        try:
            response = self.client.chat.completions.create(
                model=REWRITE_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=REWRITE_TEMPERATURE,
                max_tokens=300
            )
            
            rewritten = response.choices[0].message.content
            if rewritten is None:
                return description  # 如果失败，返回原始描述
            
            return rewritten.strip()
        
        except Exception as e:
            print(f"⚠️ Rewrite失败: {e}")
            return description
    
    def rewrite_top_items(self, top_persona: List[Dict], top_memory: List[Dict],
                         student_id: int, dataset: str, concept_text: str) -> Tuple[List[str], List[str]]:
        """
        重写top persona和memory的描述
        
        Returns:
            rewritten_persona: List of 3 rewritten persona descriptions
            rewritten_memory: List of 3 rewritten memory descriptions
        """
        # 加载forgetting信息
        forgetting_info = self.load_forgetting_info(student_id, dataset, concept_text)
        
        # 重写persona
        rewritten_persona = []
        for item in top_persona:
            rewritten = self.rewrite_description(
                description=item['description'],
                concept=forgetting_info['concept'],
                mastery=forgetting_info['mastery'],
                delta_t_days=forgetting_info['delta_t_days'],
                forgetting_score=forgetting_info['forgetting_score'],
                forgetting_level=forgetting_info['forgetting_level']
            )
            rewritten_persona.append(rewritten)
        
        # 重写memory
        rewritten_memory = []
        for item in top_memory:
            rewritten = self.rewrite_description(
                description=item['description'],
                concept=forgetting_info['concept'],
                mastery=forgetting_info['mastery'],
                delta_t_days=forgetting_info['delta_t_days'],
                forgetting_score=forgetting_info['forgetting_score'],
                forgetting_level=forgetting_info['forgetting_level']
            )
            rewritten_memory.append(rewritten)
        
        return rewritten_persona, rewritten_memory

# 测试
if __name__ == "__main__":
    from tasa_rag import TASARAG
    
    # 初始化
    rag = TASARAG()
    rewriter = MasteryRewriter()
    
    # 检索
    query = "I want to learn about rotations"
    top_persona, top_memory = rag.retrieve_and_rerank(
        query=query,
        student_id=1,
        dataset="assist2017",
        concept_text="transformations-rotations"
    )
    
    # 重写
    rewritten_persona, rewritten_memory = rewriter.rewrite_top_items(
        top_persona, top_memory,
        student_id=1,
        dataset="assist2017",
        concept_text="transformations-rotations"
    )
    
    print("\n原始 Persona:")
    for i, item in enumerate(top_persona, 1):
        print(f"{i}. {item['description']}")
    
    print("\n重写后 Persona:")
    for i, desc in enumerate(rewritten_persona, 1):
        print(f"{i}. {desc}")
    
    print("\n原始 Memory:")
    for i, item in enumerate(top_memory, 1):
        print(f"{i}. {item['description']}")
    
    print("\n重写后 Memory:")
    for i, desc in enumerate(rewritten_memory, 1):
        print(f"{i}. {desc}")

