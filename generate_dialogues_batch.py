#!/usr/bin/env python3
"""
批量生成TASA dialogue
为指定学生生成教学对话（串行处理，避免模型冲突）
"""

import json
import os
import time

from student_roleplay_evaluation import build_student_system_prompt, load_session
from tasa_tutoring import TASATutor

def generate_dialogue_for_student(student_id, dataset, tutor):
    """为单个学生生成dialogue"""
    try:
        print(f"\n{'='*80}")
        print(f"🎓 学生 {student_id}")
        print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        
        # 检查是否已存在
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA/{dataset}/{student_id}-{concept_text}.json'
        
        if os.path.exists(dialogue_file):
            print(f"   ✅ Dialogue已存在: {concept_text}")
            return True
        
        # 生成dialogue
        print(f"   📚 生成dialogue: {concept_text}")
        student_prompt = build_student_system_prompt(session)
        
        dialogue = tutor.conduct_tutoring_session(
            student_id=student_id,
            dataset=dataset,
            concept_text=concept_text,
            student_system_prompt=student_prompt
        )
        
        tutor.save_dialogue(dialogue, student_id, concept_text, dataset)
        print(f"   ✅ Dialogue生成完成")
        return True
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='批量生成TASA dialogue')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集')
    parser.add_argument('--num-students', type=int, default=9, help='学生数量')
    parser.add_argument('--all', action='store_true', help='生成所有符合条件学生的dialogue')
    
    args = parser.parse_args()
    
    # 加载符合条件的学生列表
    with open('/mnt/localssd/qualified_students_list.json') as f:
        qualified_data = json.load(f)
    
    if args.all:
        student_ids = [s['student_id'] for s in qualified_data['students']]
    else:
        student_ids = [s['student_id'] for s in qualified_data['students'][:args.num_students]]
    
    print("="*80)
    print("🚀 批量生成TASA Dialogue")
    print("="*80)
    print(f"   数据集: {args.dataset}")
    print(f"   学生数: {len(student_ids)}")
    print(f"   方式: 串行处理（避免模型冲突）")
    print("="*80)
    
    # 初始化tutor（只初始化一次）
    print("\n🔧 初始化TASA Tutor...")
    tutor = TASATutor()
    
    # 串行处理
    start_time = time.time()
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, student_id in enumerate(student_ids, 1):
        print(f"\n进度: {i}/{len(student_ids)}")
        
        # 先检查是否已存在
        session_file = f'/mnt/localssd/bank/session/{args.dataset}/{student_id}.json'
        session = load_session(session_file)
        concept_text = session['concept_text']
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA/{args.dataset}/{student_id}-{concept_text}.json'
        
        if os.path.exists(dialogue_file):
            skip_count += 1
            print(f"   ⏭️  学生{student_id}已有dialogue，跳过")
            continue
        
        result = generate_dialogue_for_student(student_id, args.dataset, tutor)
        
        if result:
            success_count += 1
        else:
            fail_count += 1
        
        # 显示预估时间
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = avg_time * (len(student_ids) - i)
        
        print(f"\n   ⏱️  已用时: {elapsed/60:.1f}分钟 | 预计剩余: {remaining/60:.1f}分钟")
    
    # 总结
    total_time = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ Dialogue生成完成！")
    print(f"{'='*80}")
    print(f"   总学生数: {len(student_ids)}")
    print(f"   新生成: {success_count}")
    print(f"   已存在: {skip_count}")
    print(f"   失败: {fail_count}")
    print(f"   总耗时: {total_time/60:.1f}分钟")
    print(f"   平均每个: {total_time/len(student_ids):.1f}秒")
    print(f"\n💡 下一步: 运行 python run_tasa_batch_best_of_two.py --num-students {len(student_ids)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

