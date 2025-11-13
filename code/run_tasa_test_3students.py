#!/usr/bin/env python3
"""
对3个符合条件的学生进行TASA测试
每个学生: 1次tutoring + 3次post-test
"""

import json
import sys
from student_roleplay_evaluation import build_student_system_prompt, load_session
from tasa_tutoring import TASATutor
from tasa_evaluation_multi_run import TASAMultiRunEvaluator

def main():
    # 3个符合条件的学生
    student_ids = [1001, 1002, 1004]
    dataset = "assist2017"
    
    print("="*80)
    print("🚀 TASA测试: 3个学生 × (1次tutoring + 3次post-test)")
    print("="*80)
    
    # 初始化
    tutor = TASATutor()
    multi_evaluator = TASAMultiRunEvaluator(num_runs=3)
    
    all_results = []
    
    for idx, student_id in enumerate(student_ids, 1):
        print(f"\n\n{'#'*80}")
        print(f"# 学生 {idx}/3: ID={student_id}")
        print(f"{'#'*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        
        print(f"\n📋 学生信息:")
        print(f"   ID: {student_id}")
        print(f"   Concept: {concept_text}")
        
        # 构建student prompt
        student_prompt = build_student_system_prompt(session)
        
        # Step 1: 生成dialogue（如果还没有）
        dialogue_file = f'/mnt/localssd/bank/dialogue/TASA/{dataset}/{student_id}-{concept_text}.json'
        import os
        
        if not os.path.exists(dialogue_file):
            print(f"\n🎓 Step 1: 进行Tutoring (10轮教学)")
            
            try:
                dialogue = tutor.conduct_tutoring_session(
                    student_id=student_id,
                    dataset=dataset,
                    concept_text=concept_text,
                    student_system_prompt=student_prompt
                )
                
                # 保存dialogue
                tutor.save_dialogue(dialogue, student_id, concept_text, dataset)
                print(f"   ✅ Tutoring完成")
                
            except Exception as e:
                print(f"   ❌ Tutoring失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        else:
            print(f"\n✅ Dialogue已存在，跳过tutoring")
        
        # Step 2: 进行3次post-test评估
        print(f"\n📊 Step 2: 进行3次Post-test评估")
        
        try:
            result = multi_evaluator.evaluate_student_multi_runs(student_id, dataset)
            multi_evaluator.save_multi_run_result(result)
            all_results.append(result)
            
        except Exception as e:
            print(f"   ❌ 评估失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 汇总结果
    print(f"\n\n{'='*80}")
    print(f"📊 最终汇总: {len(all_results)}个学生的TASA测试结果")
    print(f"{'='*80}")
    
    for result in all_results:
        print(f"\n┌{'─'*78}┐")
        print(f"│ 学生{result['student_id']} - {result['concept_text']:<63} │")
        print(f"├{'─'*78}┤")
        print(f"│ 历史准确率:   {result['original_accuracy']*100:5.1f}%                                                │")
        print(f"│ Pre-test:     {result['pre_test_accuracy']*100:5.1f}%   (差距 {result['accuracy_deviation']*100:.1f}%)                              │")
        print(f"│ Post-test:    {result['avg_post_test_accuracy']*100:5.1f}% ± {result['std_post_test_accuracy']*100:4.1f}%                                       │")
        print(f"│                                                                              │")
        print(f"│ Learning Gain: {result['avg_learning_gain']*100:4.1f}% ± {result['std_learning_gain']*100:3.1f}%                                       │")
        print(f"│ 绝对提升:     {result['avg_improvement']*100:+5.1f}% ± {result['std_improvement']*100:4.1f}%                                       │")
        print(f"└{'─'*78}┘")
        
        # 显示每次运行详情
        print(f"   详细结果:")
        for run in result['runs']:
            print(f"      Run {run['run_id']}: Post={run['post_test_accuracy']*100:4.1f}%, "
                  f"Gain={run['learning_gain']*100:+5.1f}%")
    
    # 计算总体平均
    if all_results:
        import numpy as np
        
        all_gains = [r['avg_learning_gain'] for r in all_results]
        overall_avg_gain = np.mean(all_gains)
        overall_std_gain = np.std(all_gains, ddof=1) if len(all_gains) > 1 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 整体统计 (3个学生的平均)")
        print(f"{'='*80}")
        print(f"   平均Learning Gain: {overall_avg_gain*100:.1f}% ± {overall_std_gain*100:.1f}%")
        
        # 保存整体统计
        summary = {
            "num_students": len(all_results),
            "num_runs_per_student": 3,
            "overall_avg_learning_gain": overall_avg_gain,
            "overall_std_learning_gain": overall_std_gain,
            "students": all_results
        }
        
        summary_file = "/mnt/localssd/bank/evaluation_results/TASA-multi/assist2017/summary_3students.json"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 整体统计已保存至: {summary_file}")
    
    print(f"\n{'='*80}")
    print(f"✅ 测试完成！")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

