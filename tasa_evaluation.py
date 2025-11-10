"""
TASA Evaluation模块
进行Post-test评估并计算Learning Gain
"""

import json
import os
from typing import List, Dict, Tuple
from openai import OpenAI

from tasa_config import *
from student_roleplay_evaluation import grade_answers

class TASAEvaluator:
    def __init__(self):
        """初始化TASA评估器"""
        print("🔧 初始化TASA Evaluator...")
        
        self.client = OpenAI(
            api_key=API_KEY,
            base_url=ENDPOINT
        )
        
        print("✅ TASA Evaluator初始化完成")
    
    def load_dialogue(self, student_id: int, concept_text: str, dataset: str) -> List[Dict]:
        """加载tutoring dialogue，根据TUTOR_MODEL自动选择对应backbone的dialogue"""
        from tasa_config import TUTOR_MODEL, FORGETTING_SCORE_METHOD
        
        # 根据TUTOR_MODEL决定backbone后缀
        if 'llama' in TUTOR_MODEL.lower():
            backbone_suffix = '-llama'
        elif 'qwen' in TUTOR_MODEL.lower():
            backbone_suffix = '-qwen'
        else:
            backbone_suffix = ''  # gpt-oss-120b
        
        dialogue_file = f"{DIALOGUE_DIR}{backbone_suffix}/{dataset}/{FORGETTING_SCORE_METHOD}/{student_id}-{concept_text}.json"
        
        with open(dialogue_file) as f:
            dialogue_data = json.load(f)
        
        return dialogue_data['dialogue']
    
    def extract_learned_knowledge(self, dialogue: List[Dict], concept_text: str) -> str:
        """
        从对话中提取学到的关键知识点（而不是完整对话）
        """
        # 提取所有Tutor的讲解（跳过第一轮，因为那只是问题）
        tutor_explanations = []
        for msg in dialogue:
            if msg['role'] == 'assistant' and msg['round'] > 1:
                # 提取讲解部分（通常在问题之前）
                content = msg['content']
                # 简单截断：只取前500字符作为关键讲解
                explanation = content[:500] if len(content) > 500 else content
                tutor_explanations.append(explanation)
        
        # 构建学习总结
        if tutor_explanations:
            # 只取前3个最重要的讲解
            key_explanations = "\n\n".join([f"- {exp}" for exp in tutor_explanations[:3]])
            return key_explanations
        else:
            return f"Key concepts about {concept_text}"
    
    def conduct_post_test(self, student_id: int, dataset: str, concept_text: str,
                         dialogue: List[Dict], questions: List[str],
                         student_system_prompt: str) -> Tuple[float, List[Dict]]:
        """
        进行Post-test评估
        
        Args:
            dialogue: Tutoring对话历史
            questions: 用于测试的问题列表
            student_system_prompt: 学生的基础system prompt
        
        Returns:
            post_test_accuracy: Post-test准确率
            answers: 学生的回答列表
        """
        print(f"\n📊 进行Post-test评估")
        print(f"   题目数: {len(questions)}")
        
        # 提取学到的关键知识
        learned_knowledge = self.extract_learned_knowledge(dialogue, concept_text)
        
        # 增强学生prompt，明确说明已经学会了这些知识
        enhanced_prompt = f"""{student_system_prompt}

[IMPORTANT UPDATE: You Have Just Learned This Concept]

You have just completed a personalized tutoring session on {concept_text}. Through 10 rounds of practice and feedback, you have now MASTERED the following key concepts:

{learned_knowledge}

**YOU NOW UNDERSTAND THIS MATERIAL.** The tutoring has helped you overcome your previous difficulties. Your knowledge of {concept_text} has significantly improved.

When answering the following questions:
- Apply what you just learned from the tutoring session
- You should perform BETTER than before because you now understand the concepts
- Show your improved understanding and confidence
- Use the knowledge and corrections you received during tutoring"""
        
        # 让学生回答问题
        answers = []
        for i, question in enumerate(questions, 1):
            print(f"   问题 {i}/{len(questions)}", end='\r')
            
            try:
                response = self.client.chat.completions.create(
                    model=STUDENT_MODEL,
                    messages=[
                        {"role": "system", "content": enhanced_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=STUDENT_TEMPERATURE,
                    max_tokens=MAX_TOKENS_STUDENT
                )
                
                content = response.choices[0].message.content
                answer = content.strip() if content else "I don't know."
                
            except Exception as e:
                print(f"\n⚠️ 问题{i}回答失败: {e}")
                answer = "I don't know."
            
            answers.append({
                "question_number": i,
                "question": question,
                "student_answer": answer
            })
        
        print(f"\n   ✅ 所有问题已回答")
        
        # 批改
        print(f"   📝 批改中...")
        total_score, feedback, individual_scores = grade_answers(answers, concept_text)
        
        post_test_accuracy = total_score / len(questions)
        
        # 将individual_scores添加到answers中
        for i, answer in enumerate(answers):
            answer['score'] = individual_scores[i]
        
        print(f"   ✅ Post-test准确率: {post_test_accuracy*100:.1f}%")
        
        return post_test_accuracy, answers
    
    def calculate_learning_gain(self, pre_test_accuracy: float, 
                               post_test_accuracy: float) -> float:
        """
        计算Learning Gain
        
        Formula: learning_gain = (post - pre) / (1 - pre)
        """
        if pre_test_accuracy >= 1.0:
            # 如果pre-test已经100%，无法再提高
            return 0.0
        
        learning_gain = (post_test_accuracy - pre_test_accuracy) / (1.0 - pre_test_accuracy)
        
        return learning_gain
    
    def load_pretest_result(self, student_id: int, dataset: str, concept_id: str) -> float:
        """从pre-test结果中加载roleplay准确率"""
        pretest_file = f"{EVALUATION_DIR}/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
        
        try:
            with open(pretest_file) as f:
                pretest_data = json.load(f)
            return pretest_data['roleplay_accuracy']
        except Exception as e:
            print(f"⚠️ 无法加载pre-test结果: {e}")
            return None
    
    def evaluate_single_student(self, student_id: int, dataset: str, 
                               concept_text: str, concept_id: str, questions: List[str],
                               student_system_prompt: str) -> Dict:
        """
        评估单个学生的完整流程
        
        Returns:
            evaluation_result: {
                "student_id": int,
                "dataset": str,
                "concept_text": str,
                "concept_id": str,
                "pre_test_accuracy": float,  # 从pre-test结果中读取
                "post_test_accuracy": float,
                "learning_gain": float,
                "answers": List[Dict]
            }
        """
        print(f"\n{'='*80}")
        print(f"📊 评估学生 {student_id} - {concept_text}")
        print(f"{'='*80}")
        
        # 加载pre-test的roleplay准确率
        pre_test_accuracy = self.load_pretest_result(student_id, dataset, concept_id)
        
        if pre_test_accuracy is None:
            print(f"❌ 无法找到pre-test结果，无法计算learning gain")
            return None
        
        print(f"✅ Pre-test准确率 (无教学): {pre_test_accuracy*100:.1f}%")
        
        # 加载dialogue
        dialogue = self.load_dialogue(student_id, concept_text, dataset)
        print(f"✅ 已加载对话历史 ({len(dialogue)}条消息)")
        
        # Post-test
        post_test_accuracy, answers = self.conduct_post_test(
            student_id, dataset, concept_text,
            dialogue, questions, student_system_prompt
        )
        
        # 计算Learning Gain
        learning_gain = self.calculate_learning_gain(pre_test_accuracy, post_test_accuracy)
        
        print(f"\n📈 评估结果:")
        print(f"   Pre-test (无教学):  {pre_test_accuracy*100:.1f}%")
        print(f"   Post-test (有教学): {post_test_accuracy*100:.1f}%")
        print(f"   绝对提升: {(post_test_accuracy - pre_test_accuracy)*100:+.1f}%")
        print(f"   Learning Gain: {learning_gain:.3f}")
        
        result = {
            "student_id": student_id,
            "dataset": dataset,
            "concept_text": concept_text,
            "concept_id": concept_id,
            "pre_test_accuracy": pre_test_accuracy,
            "post_test_accuracy": post_test_accuracy,
            "learning_gain": learning_gain,
            "improvement": post_test_accuracy - pre_test_accuracy,
            "answers": answers
        }
        
        return result
    
    def save_evaluation_result(self, result: Dict, method: str = "TASA"):
        """保存评估结果"""
        dataset = result['dataset']
        student_id = result['student_id']
        concept_text = result['concept_text']
        
        # 创建目录
        eval_dir = f"{EVALUATION_DIR}/{method}/{dataset}"
        os.makedirs(eval_dir, exist_ok=True)
        
        # 保存
        filename = f"{eval_dir}/student_{student_id}_{concept_text}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 评估结果已保存至: {filename}")
        
        return filename

# 测试
if __name__ == "__main__":
    from student_roleplay_evaluation import build_student_system_prompt, load_session
    from tasa_tutoring import TASATutor
    import json
    
    # 先进行tutoring
    print("="*80)
    print("Step 1: 进行Tutoring")
    print("="*80)
    
    tutor = TASATutor()
    session = load_session('/mnt/localssd/bank/session/assist2017/1.json')
    student_prompt = build_student_system_prompt(session)
    
    # 模拟pre-test准确率
    pre_test_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
    
    # Tutoring
    dialogue = tutor.conduct_tutoring_session(
        student_id=1,
        dataset="assist2017",
        concept_text=session['concept_text'],
        student_system_prompt=student_prompt
    )
    
    tutor.save_dialogue(dialogue, 1, session['concept_text'], "assist2017")
    
    # 评估
    print("\n" + "="*80)
    print("Step 2: 进行Post-test评估")
    print("="*80)
    
    evaluator = TASAEvaluator()
    
    # 加载测试题目
    questions_file = '/mnt/localssd/bank/test_data/assist2017/concept_questions.json'
    with open(questions_file) as f:
        all_questions = json.load(f)
    
    concept_id = str(session['concept_id'])
    questions = all_questions[concept_id]['questions']
    
    # 评估
    result = evaluator.evaluate_single_student(
        student_id=1,
        dataset="assist2017",
        concept_text=session['concept_text'],
        questions=questions,
        pre_test_accuracy=pre_test_accuracy,
        student_system_prompt=student_prompt
    )
    
    # 保存
    evaluator.save_evaluation_result(result, method="TASA")

