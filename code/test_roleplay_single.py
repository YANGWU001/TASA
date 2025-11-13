#!/usr/bin/env python3
"""
快速测试单个学生的Role-Play评估
"""

from student_roleplay_evaluation import (
    load_concept_questions,
    load_session,
    build_student_system_prompt,
    get_student_answers,
    grade_answers
)
import json

def test_single_student():
    """测试单个学生的role-play"""
    
    # 配置
    session_file = '/mnt/localssd/bank/session/assist2017/1.json'
    concept_questions_file = '/mnt/localssd/bank/test_data/assist2017/concept_questions.json'
    
    print("="*80)
    print("学生Role-Play快速测试")
    print("="*80)
    
    # 加载数据
    print("\n📖 加载数据...")
    session = load_session(session_file)
    concept_questions = load_concept_questions(concept_questions_file)
    
    # 显示学生信息
    print(f"\n👤 学生信息:")
    print(f"   学生ID: {session['student_id']}")
    print(f"   Concept: {session['concept_text']}")
    print(f"   准确率: {session['persona']['stats']['correct']}/{session['persona']['stats']['total']} = {session['persona']['stats']['correct']/session['persona']['stats']['total']*100:.1f}%")
    print(f"   距离上次: {session['delta_t_minutes']:.1f} 分钟")
    
    # 获取问题
    concept_id = str(session['concept_id'])
    questions = concept_questions[concept_id]['questions']
    
    print(f"\n📝 问题数量: {len(questions)}")
    print(f"\n示例问题:")
    for i, q in enumerate(questions[:3], 1):
        print(f"   {i}. {q}")
    
    # 构建system prompt
    print(f"\n🎭 构建学生人设...")
    system_prompt = build_student_system_prompt(session)
    print(f"\nSystem Prompt预览:")
    print("-" * 80)
    print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
    print("-" * 80)
    
    # 询问是否继续
    print(f"\n⚠️  注意: 这将调用LLM API，会产生费用。")
    user_input = input("是否继续? (y/n): ")
    
    if user_input.lower() != 'y':
        print("已取消。")
        return
    
    # 获取学生答案（只测试前3题）
    print(f"\n🎭 学生开始回答（测试前3题）...")
    test_questions = questions[:3]
    student_answers = get_student_answers(system_prompt, test_questions, session['concept_text'])
    
    # 显示答案
    print(f"\n📄 学生答案:")
    for ans in student_answers:
        print(f"\n问题 {ans['question_number']}: {ans['question']}")
        print(f"答案: {ans['student_answer']}")
        print("-" * 80)
    
    # 批改
    print(f"\n📝 批改答案...")
    total_score, feedback, individual_scores = grade_answers(student_answers, session['concept_text'])
    
    # 显示结果
    print(f"\n{'='*80}")
    print(f"评估结果")
    print(f"{'='*80}")
    print(f"\n总分: {total_score}/3 ({total_score/3*100:.1f}%)")
    print(f"\n各题得分:")
    for i, score in enumerate(individual_scores, 1):
        print(f"   问题{i}: {score}/1")
    print(f"\n反馈: {feedback}")
    
    # 对比
    original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
    roleplay_accuracy = total_score / 3
    
    print(f"\n📊 对比:")
    print(f"   原始准确率: {original_accuracy*100:.1f}%")
    print(f"   Role-play准确率: {roleplay_accuracy*100:.1f}%")
    print(f"   差异: {(roleplay_accuracy - original_accuracy)*100:.1f} 百分点")

if __name__ == '__main__':
    test_single_student()

