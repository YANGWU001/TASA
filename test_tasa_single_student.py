#!/usr/bin/env python3
"""
测试单个学生的完整TASA流程
"""

import json
import sys
from student_roleplay_evaluation import build_student_system_prompt, load_session

# 确保导入路径正确
sys.path.insert(0, '/mnt/localssd')

from tasa_config import *
from tasa_tutoring import TASATutor
from tasa_evaluation import TASAEvaluator

def test_single_student(student_id: int = 1, dataset: str = "assist2017"):
    """
    测试单个学生的完整TASA流程
    """
    print("="*80)
    print(f"🧪 测试TASA流程 - 学生 {student_id}")
    print("="*80)
    
    # Step 1: 加载学生session
    print(f"\n📂 Step 1: 加载学生数据")
    session_file = f'{SESSION_DIR}/{dataset}/{student_id}.json'
    session = load_session(session_file)
    
    concept_text = session['concept_text']
    concept_id = str(session['concept_id'])
    
    print(f"   学生ID: {student_id}")
    print(f"   Concept: {concept_text} (ID: {concept_id})")
    print(f"   历史准确率: {session['persona']['stats']['correct']/session['persona']['stats']['total']*100:.1f}%")
    
    # Step 2: 构建学生的system prompt
    print(f"\n🎭 Step 2: 构建学生Role-play Prompt")
    student_prompt = build_student_system_prompt(session)
    print(f"   ✅ Student prompt已生成")
    
    # Step 3: 初始化Tutor并进行Tutoring
    print(f"\n🎓 Step 3: 进行Tutoring Session (10轮)")
    tutor = TASATutor()
    
    try:
        dialogue = tutor.conduct_tutoring_session(
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text,
            student_system_prompt=student_prompt
        )
        
        # 保存对话
        dialogue_file = tutor.save_dialogue(dialogue, student_id, concept_text, dataset)
        
        print(f"\n✅ Tutoring完成！")
        print(f"   对话轮数: {len([m for m in dialogue if m['role']=='assistant'])}轮")
        print(f"   总消息数: {len(dialogue)}条")
        
    except Exception as e:
        print(f"\n❌ Tutoring失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 4: 加载测试题目
    print(f"\n📝 Step 4: 准备Post-test")
    questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
    
    with open(questions_file) as f:
        all_questions = json.load(f)
    
    concept_data = all_questions.get(concept_id, {})
    questions = concept_data.get('questions', [])
    
    if not questions:
        print(f"   ❌ 未找到concept {concept_id} 的题目")
        return None
    
    print(f"   ✅ 找到 {len(questions)} 道题目")
    
    # Step 5: 进行Post-test评估
    print(f"\n📊 Step 5: 进行Post-test评估")
    evaluator = TASAEvaluator()
    
    try:
        result = evaluator.evaluate_single_student(
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text,
            concept_id=concept_id,
            questions=questions,
            student_system_prompt=student_prompt
        )
        
        # 保存评估结果
        eval_file = evaluator.save_evaluation_result(result, method="TASA")
        
        # Step 6: 显示结果
        print(f"\n{'='*80}")
        print(f"✅ TASA测试完成！")
        print(f"{'='*80}")
        
        print(f"\n📊 评估结果:")
        print(f"   Pre-test (无教学):  {result['pre_test_accuracy']*100:.1f}%")
        print(f"   Post-test (有教学): {result['post_test_accuracy']*100:.1f}%")
        print(f"   绝对提升:          {result['improvement']*100:+.1f}%")
        print(f"   Learning Gain:     {result['learning_gain']:.3f}")
        
        if result['learning_gain'] <= 0:
            print(f"\n⚠️  注意: Learning Gain ≤ 0，说明教学没有带来提升！")
        
        print(f"\n💾 文件已保存:")
        print(f"   对话: {dialogue_file}")
        print(f"   评估: {eval_file}")
        
        print(f"\n{'='*80}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Post-test失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试单个学生的TASA流程')
    parser.add_argument('--student-id', type=int, default=1, help='学生ID')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集名称')
    
    args = parser.parse_args()
    
    result = test_single_student(
        student_id=args.student_id,
        dataset=args.dataset
    )
    
    if result:
        print("\n✅ 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)

