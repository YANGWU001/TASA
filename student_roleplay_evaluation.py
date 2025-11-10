#!/usr/bin/env python3
"""
学生Role-Play评估系统
让LLM扮演学生回答问题，然后用另一个LLM打分
"""

import json
import os
from pathlib import Path
from openai import OpenAI
from typing import List, Dict, Tuple
from tqdm import tqdm
import time

# 导入配置
try:
    from roleplay_config import (
        ENDPOINT, API_KEY, STUDENT_MODEL, GRADER_MODEL,
        STUDENT_TEMPERATURE, GRADER_TEMPERATURE, SLEEP_BETWEEN_QUESTIONS
    )
except ImportError:
    print("⚠️  警告: 未找到roleplay_config.py，使用默认配置")
    print("   请复制roleplay_config.py并填写你的API凭证")
    ENDPOINT = "<Insert your endpoint>"
    API_KEY = "<Insert your key>"
    STUDENT_MODEL = "gpt-oss-120b"
    GRADER_MODEL = "gpt-4o-mini"
    STUDENT_TEMPERATURE = 0.7
    GRADER_TEMPERATURE = 0.3
    SLEEP_BETWEEN_QUESTIONS = 0.5

# 初始化客户端
client = OpenAI(
    api_key="Bearer " + API_KEY,
    base_url=ENDPOINT,
)

def load_concept_questions(filepath: str) -> Dict:
    """加载concept questions"""
    with open(filepath) as f:
        return json.load(f)

def load_session(filepath: str) -> Dict:
    """加载session数据"""
    with open(filepath) as f:
        return json.load(f)

def build_student_system_prompt(session: Dict) -> str:
    """构建学生的system prompt"""
    persona_desc = session['persona']['description']
    concept_text = session['concept_text']
    delta_t_minutes = session.get('delta_t_minutes', 0)
    accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total'] * 100
    total_attempts = session['persona']['stats']['total']
    correct_attempts = session['persona']['stats']['correct']
    
    # 提取记忆信息
    memory = session.get('memory', [])
    recent_performance = []
    if memory:
        for mem in memory[-5:]:  # 最近5次
            result = "correct" if mem['response'] == 1 else "incorrect"
            recent_performance.append(f"- {mem['description']} (Result: {result})")
    
    memory_context = "\n".join(recent_performance) if recent_performance else "No recent history available."
    
    # 动态计算期望正确率（更接近历史准确率）
    expected_correct_out_of_10 = round(accuracy / 10)  # 27% -> 3题, 65% -> 7题
    expected_wrong_out_of_10 = 10 - expected_correct_out_of_10
    
    # 根据准确率动态调整描述
    if accuracy < 40:
        level = "STRUGGLING"
        confidence = "very low confidence and frequent confusion"
        error_rate = "most of your answers (about 6-7 out of 10)"
    elif accuracy < 60:
        level = "DEVELOPING"
        confidence = "moderate uncertainty and occasional mistakes"
        error_rate = "many of your answers (about 4-5 out of 10)"
    elif accuracy < 80:
        level = "COMPETENT"
        confidence = "reasonable confidence with some gaps"
        error_rate = "some of your answers (about 2-3 out of 10)"
    else:
        level = "STRONG"
        confidence = "high confidence with minor errors"
        error_rate = "a few of your answers (about 1-2 out of 10)"
    
    system_prompt = f"""You are a {level} student with {accuracy:.1f}% accuracy on {concept_text}.

**YOUR ROLE:**
{persona_desc}

**Performance Profile:**
- Historical accuracy: {accuracy:.1f}% ({correct_attempts}/{total_attempts} attempts)
- Time since last attempt: {delta_t_minutes:.1f} minutes
- Expected performance: Get about {expected_correct_out_of_10} out of 10 questions correct

**Recent History:**
{memory_context}

**HOW TO ANSWER QUESTIONS:**

Your answers should reflect your {accuracy:.1f}% accuracy level:

1. **Answer Distribution (out of 10 questions):**
   - Correct: ~{expected_correct_out_of_10} questions (matching your {accuracy:.1f}% rate)
   - Wrong: ~{expected_wrong_out_of_10} questions

2. **Common Mistakes at Your Level:**"""
    
    # 根据水平添加具体的错误模式
    if accuracy < 40:
        system_prompt += f"""
   - Confuse basic concepts regularly
   - Mix up formulas and apply incorrectly
   - Make frequent calculation errors
   - Give incomplete or wrong explanations
   - Show {confidence}
   
3. **Your Answer Style:**
   Start with uncertainty: "Um...", "I think...", "Maybe...", "I'm not sure..."
   Often give wrong answers due to genuine confusion
   Sometimes second-guess yourself from right to wrong"""
    
    elif accuracy < 60:
        system_prompt += f"""
   - Occasionally confuse similar concepts
   - Sometimes apply formulas incorrectly
   - Make some calculation errors
   - Miss some key details
   - Show {confidence}
   
3. **Your Answer Style:**
   Sometimes show uncertainty: "I think...", "Probably..."
   Get harder questions wrong, easier questions right
   Show partial understanding with gaps"""
    
    elif accuracy < 80:
        system_prompt += f"""
   - Occasionally miss subtle details
   - Sometimes make minor calculation errors
   - Usually understand core concepts
   - May struggle with complex applications
   - Show {confidence}
   
3. **Your Answer Style:**
   Generally confident but acknowledge uncertainty when unsure
   Get most standard questions right
   May struggle with tricky or complex questions"""
    
    else:
        system_prompt += f"""
   - Rarely make mistakes
   - Strong understanding of concepts
   - Occasional minor errors on complex problems
   - Comprehensive explanations
   - Show {confidence}
   
3. **Your Answer Style:**
   Answer confidently and accurately
   Provide clear explanations
   Very rarely make mistakes"""
    
    system_prompt += f"""

**CRITICAL: Maintain ~{accuracy:.1f}% accuracy**
- This means {error_rate} should be WRONG
- Answer naturally based on your knowledge level
- Don't try to be perfect - make realistic mistakes for your level
- Match your historical performance pattern"""
    
    return system_prompt

def get_student_answers(system_prompt: str, questions: List[str], concept: str) -> List[Dict]:
    """让LLM role-play学生回答问题"""
    answers = []
    
    print(f"\n🎭 Student role-playing answers for '{concept}'...")
    
    for i, question in enumerate(tqdm(questions, desc="Answering", ncols=100)):
        try:
            response = client.chat.completions.create(
                model=STUDENT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}\n\nPlease provide your answer:"}
                ],
                temperature=STUDENT_TEMPERATURE,
            )
            
            # 安全地获取答案内容
            content = response.choices[0].message.content
            if content is None:
                answer = "[Error: API returned empty response]"
                print(f"\n⚠️  Warning: Question {i+1} returned None content")
            else:
                answer = content.strip()
            
            answers.append({
                "question_number": i + 1,
                "question": question,
                "student_answer": answer
            })
            
            # 避免rate limiting
            time.sleep(SLEEP_BETWEEN_QUESTIONS)
            
        except Exception as e:
            print(f"\n❌ Error answering question {i+1}: {e}")
            answers.append({
                "question_number": i + 1,
                "question": question,
                "student_answer": "[Error: Could not generate answer]"
            })
    
    return answers

def grade_answers(answers: List[Dict], concept: str) -> Tuple[float, str]:
    """使用LLM批改答案并给出分数"""
    print(f"\n📝 Grading answers...")
    
    # 构建批改prompt
    answers_text = "\n\n".join([
        f"Question {ans['question_number']}: {ans['question']}\nStudent Answer: {ans['student_answer']}"
        for ans in answers
    ])
    
    grading_prompt = f"""You are an expert teacher grading a student's answers on the topic: {concept}

Please evaluate the following {len(answers)} answers and provide:
1. A score for each answer: ONLY 1 (correct) or 0 (incorrect) - NO partial credit (no 0.5)
2. An overall score out of 10 (sum of individual scores, must be a whole number: 0, 1, 2, ..., 10)
3. Brief feedback on the student's understanding

**IMPORTANT GRADING RULES:**
- Each answer is either CORRECT (1 point) or INCORRECT (0 points)
- NO partial scores like 0.5 are allowed
- If an answer is mostly correct but has minor errors, you must decide: is it correct enough? If yes, give 1; if no, give 0
- The total score MUST be a whole number (integer)

**Answers to Grade:**

{answers_text}

**Output Format (JSON):**
{{
    "individual_scores": [score1, score2, ..., score{len(answers)}],
    "total_score": X,
    "feedback": "Brief overall assessment of student's understanding and common mistakes"
}}

Note: individual_scores must contain only 0 or 1, and total_score must be an integer.
Provide ONLY the JSON output, no other text."""
    
    try:
        response = client.chat.completions.create(
            model=GRADER_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert teacher grading student work. Be fair and thorough."},
                {"role": "user", "content": grading_prompt}
            ],
            temperature=GRADER_TEMPERATURE,
            max_tokens=1000
        )
        
        grading_result = response.choices[0].message.content.strip()
        
        # 尝试解析JSON
        # 移除可能的markdown代码块标记
        if "```json" in grading_result:
            grading_result = grading_result.split("```json")[1].split("```")[0].strip()
        elif "```" in grading_result:
            grading_result = grading_result.split("```")[1].split("```")[0].strip()
        
        grading_data = json.loads(grading_result)
        
        total_score = grading_data.get('total_score', 0.0)
        feedback = grading_data.get('feedback', '')
        individual_scores = grading_data.get('individual_scores', [])
        
        return total_score, feedback, individual_scores
        
    except Exception as e:
        print(f"\n❌ Error grading answers: {e}")
        return 0.0, "Error during grading", []

def evaluate_session(session_file: str, concept_questions: Dict, output_dir: str):
    """评估单个session"""
    # 加载session
    session = load_session(session_file)
    
    student_id = session['student_id']
    concept_id = str(session['concept_id'])
    concept_text = session['concept_text']
    
    print(f"\n{'='*80}")
    print(f"评估学生: {student_id} | Concept: {concept_text}")
    print(f"{'='*80}")
    
    # 获取对应的问题
    if concept_id not in concept_questions:
        print(f"⚠️  Warning: No questions found for concept_id {concept_id}")
        return None
    
    questions_data = concept_questions[concept_id]
    questions = questions_data['questions']
    
    print(f"📚 Concept: {questions_data['concept_description']}")
    print(f"📊 Student Performance: {session['persona']['stats']['correct']}/{session['persona']['stats']['total']} correct")
    
    # 构建student prompt
    system_prompt = build_student_system_prompt(session)
    
    # 获取学生答案
    student_answers = get_student_answers(system_prompt, questions, concept_text)
    
    # 批改答案
    total_score, feedback, individual_scores = grade_answers(student_answers, concept_text)
    
    # 准备结果
    result = {
        "student_id": student_id,
        "concept_id": concept_id,
        "concept_text": concept_text,
        "concept_description": questions_data['concept_description'],
        "original_accuracy": session['persona']['stats']['correct'] / session['persona']['stats']['total'],
        "roleplay_score": total_score,
        "individual_scores": individual_scores,
        "feedback": feedback,
        "answers": student_answers,
        "session_info": {
            "delta_t_minutes": session.get('delta_t_minutes', 0),
            "num_attempts": session.get('num_attempts', 0),
            "last_response": session.get('last_response', None)
        }
    }
    
    # 保存结果
    output_file = Path(output_dir) / f"student_{student_id}_concept_{concept_id}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 评估完成!")
    print(f"   原始准确率: {result['original_accuracy']*100:.1f}%")
    print(f"   Role-play得分: {total_score}/10 ({total_score*10:.1f}%)")
    print(f"   结果已保存至: {output_file}")
    print(f"\n💬 反馈: {feedback}\n")
    
    return result

def main():
    """主函数"""
    print("="*80)
    print("学生Role-Play评估系统")
    print("="*80)
    
    # 加载concept questions
    concept_questions_file = '/mnt/localssd/bank/test_data/assist2017/concept_questions.json'
    print(f"\n📖 加载题库: {concept_questions_file}")
    concept_questions = load_concept_questions(concept_questions_file)
    print(f"   ✅ 加载了 {len(concept_questions)} 个concepts的题目")
    
    # 设置输出目录
    output_dir = '/mnt/localssd/bank/evaluation_results/assist2017'
    
    # 示例：评估单个session
    session_file = '/mnt/localssd/bank/session/assist2017/1.json'
    
    print(f"\n🎯 开始评估...")
    result = evaluate_session(session_file, concept_questions, output_dir)
    
    if result:
        print(f"\n{'='*80}")
        print("评估完成!")
        print(f"{'='*80}")

if __name__ == '__main__':
    main()

