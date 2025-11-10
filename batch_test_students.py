#!/usr/bin/env python3
"""
多线程批量测试学生Role-Play系统
在5个不同准确率的学生身上测试灵活prompt的效果
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List
import time

from student_roleplay_evaluation import (
    load_session,
    load_concept_questions,
    build_student_system_prompt,
    get_student_answers,
    grade_answers
)

def evaluate_single_student(student_id: int, dataset: str = "assist2017", method: str = "pre-test") -> Dict:
    """评估单个学生"""
    try:
        print(f"\n{'='*80}")
        print(f"🎯 开始评估学生: {student_id} (Dataset: {dataset})")
        print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total'] * 100
        
        print(f"📚 Concept: {concept_text} (ID: {concept_id})")
        print(f"📊 Historical Accuracy: {accuracy:.1f}%")
        
        # 加载题目
        questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
        questions = load_concept_questions(questions_file)
        
        # 对于assist2017，使用concept_id查找题目
        concept_data = questions.get(concept_id, {})
        if not concept_data or 'questions' not in concept_data:
            print(f"❌ 未找到concept ID '{concept_id}' ({concept_text}) 的题目")
            return None
        
        concept_questions = concept_data['questions']
        print(f"✅ 找到 {len(concept_questions)} 道题目")
        
        # 构建prompt
        system_prompt = build_student_system_prompt(session)
        
        # 学生回答
        print(f"🎭 Student role-playing...")
        start_time = time.time()
        answers = get_student_answers(system_prompt, concept_questions, concept_text)
        answer_time = time.time() - start_time
        
        # 批改
        print(f"📝 Grading...")
        total_score, feedback, individual_scores = grade_answers(answers, concept_text)
        total_time = time.time() - start_time
        
        # 计算准确率（注意：只有2道题，所以满分是2而不是10）
        max_score = len(answers)
        roleplay_accuracy = (total_score / max_score) * 100
        
        print(f"\n✅ 评估完成!")
        print(f"   原始准确率: {accuracy:.1f}%")
        print(f"   Role-play准确率: {roleplay_accuracy:.1f}%")
        print(f"   偏差: {roleplay_accuracy - accuracy:+.1f}%")
        print(f"   用时: {total_time:.1f}s")
        
        # 保存结果
        result = {
            "student_id": str(student_id),
            "dataset": dataset,
            "method": method,
            "concept_text": concept_text,
            "concept_id": concept_id,
            "original_accuracy": accuracy / 100,
            "roleplay_accuracy": roleplay_accuracy / 100,
            "deviation": (roleplay_accuracy - accuracy) / 100,
            "roleplay_score": total_score,
            "max_score": max_score,
            "individual_scores": individual_scores,
            "feedback": feedback,
            "answers": answers,
            "session_info": {
                "delta_t_minutes": session.get('delta_t_minutes', 0),
                "num_attempts": session['persona']['stats']['total'],
                "last_response": session.get('memory', [{}])[-1].get('response') if session.get('memory') else None
            },
            "timing": {
                "answer_time": answer_time,
                "total_time": total_time
            }
        }
        
        # 保存到文件（新的目录结构：method/dataset/）
        output_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
        os.makedirs(output_dir, exist_ok=True)
        output_file = f'{output_dir}/student_{student_id}_concept_{session["concept_id"]}.json'
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 结果已保存至: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ 学生 {student_id} 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def batch_evaluate_students(student_ids: List[int], dataset: str = "assist2017", method: str = "pre-test", max_workers: int = 5):
    """批量评估多个学生（多线程）"""
    print(f"\n{'='*80}")
    print(f"🚀 批量评估系统 - 测试灵活Prompt")
    print(f"{'='*80}")
    print(f"Method: {method}")
    print(f"Dataset: {dataset}")
    print(f"Students: {student_ids}")
    print(f"Max Workers: {max_workers}")
    print(f"{'='*80}\n")
    
    results = []
    
    # 使用线程池并行评估
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_student = {
            executor.submit(evaluate_single_student, student_id, dataset, method): student_id 
            for student_id in student_ids
        }
        
        # 收集结果
        for future in as_completed(future_to_student):
            student_id = future_to_student[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"❌ 学生 {student_id} 执行失败: {e}")
    
    # 生成汇总报告
    print(f"\n\n{'='*80}")
    print(f"📊 汇总报告")
    print(f"{'='*80}\n")
    
    if not results:
        print("❌ 没有成功的评估结果")
        return
    
    print(f"成功评估: {len(results)}/{len(student_ids)} 个学生\n")
    
    print(f"{'学生ID':<10} {'原始准确率':<12} {'Role-Play':<12} {'偏差':<10} {'得分':<10} {'Concept'}")
    print(f"{'-'*80}")
    
    total_deviation = 0
    for r in sorted(results, key=lambda x: x['original_accuracy']):
        original = r['original_accuracy'] * 100
        roleplay = r['roleplay_accuracy'] * 100
        deviation = r['deviation'] * 100
        score = r['roleplay_score']
        max_score = r['max_score']
        concept = r['concept_text'][:20]
        
        total_deviation += abs(deviation)
        
        print(f"{r['student_id']:<10} {original:>6.1f}%{'':<5} {roleplay:>6.1f}%{'':<5} {deviation:>+6.1f}%{'':<3} {score}/{max_score}{'':<7} {concept}")
    
    avg_deviation = total_deviation / len(results)
    print(f"\n平均绝对偏差: {avg_deviation:.1f}%")
    
    # 先定义水平分组（用于后续统计）
    struggling = [r for r in results if r['original_accuracy'] < 0.4]
    developing = [r for r in results if 0.4 <= r['original_accuracy'] < 0.6]
    competent = [r for r in results if 0.6 <= r['original_accuracy'] < 0.8]
    strong = [r for r in results if r['original_accuracy'] >= 0.8]
    
    # 计算overall统计
    avg_original = sum(r['original_accuracy'] for r in results) / len(results)
    avg_roleplay = sum(r['roleplay_accuracy'] for r in results) / len(results)
    
    # 保存汇总结果（batch_summary.json - 本次批量测试的详细信息）
    summary = {
        "method": method,
        "dataset": dataset,
        "num_students": len(results),
        "average_deviation": avg_deviation,
        "average_original_accuracy": avg_original,
        "average_roleplay_accuracy": avg_roleplay,
        "results": [
            {
                "student_id": r['student_id'],
                "concept": r['concept_text'],
                "original_accuracy": r['original_accuracy'],
                "roleplay_accuracy": r['roleplay_accuracy'],
                "deviation": r['deviation']
            }
            for r in results
        ]
    }
    
    summary_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/batch_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 汇总结果已保存至: {summary_file}")
    
    # 生成overall.json（该method下该dataset的整体统计）
    overall = {
        "method": method,
        "dataset": dataset,
        "num_students_evaluated": len(results),
        "average_original_accuracy": avg_original,
        "average_roleplay_accuracy": avg_roleplay,
        "average_absolute_deviation": avg_deviation / 100,
        "performance_by_level": {
            "struggling": {
                "range": "<40%",
                "num_students": len(struggling),
                "avg_deviation": sum(abs(r['deviation']) for r in struggling) / len(struggling) if struggling else 0
            },
            "developing": {
                "range": "40-60%",
                "num_students": len(developing),
                "avg_deviation": sum(abs(r['deviation']) for r in developing) / len(developing) if developing else 0
            },
            "competent": {
                "range": "60-80%",
                "num_students": len(competent),
                "avg_deviation": sum(abs(r['deviation']) for r in competent) / len(competent) if competent else 0
            },
            "strong": {
                "range": "≥80%",
                "num_students": len(strong),
                "avg_deviation": sum(abs(r['deviation']) for r in strong) / len(strong) if strong else 0
            }
        }
    }
    
    overall_file = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}/overall.json'
    with open(overall_file, 'w') as f:
        json.dump(overall, f, indent=2)
    
    print(f"💾 Overall统计已保存至: {overall_file}")
    
    # 分析不同水平学生的表现
    print(f"\n{'='*80}")
    print(f"📈 按水平分析")
    print(f"{'='*80}\n")
    
    for level_name, level_results in [
        ("STRUGGLING (<40%)", struggling),
        ("DEVELOPING (40-60%)", developing),
        ("COMPETENT (60-80%)", competent),
        ("STRONG (≥80%)", strong)
    ]:
        if level_results:
            avg_dev = sum(abs(r['deviation']) for r in level_results) / len(level_results) * 100
            print(f"{level_name}: {len(level_results)}个学生, 平均偏差 {avg_dev:.1f}%")

if __name__ == "__main__":
    # 测试5个不同准确率的学生，覆盖从0%到85.7%
    student_ids = [
        1264,  # 0.0% - STRUGGLING
        793,   # 35.3% - DEVELOPING  
        565,   # 55.6% - COMPETENT
        398,   # 70.0% - STRONG
        1355   # 85.7% - EXPERT
    ]
    
    print(f"\n测试学生分布:")
    print(f"  1264: 0.0% (STRUGGLING)")
    print(f"  793: 35.3% (DEVELOPING)")
    print(f"  565: 55.6% (COMPETENT)")
    print(f"  398: 70.0% (STRONG)")
    print(f"  1355: 85.7% (EXPERT)")
    print()
    
    batch_evaluate_students(
        student_ids=student_ids,
        dataset="assist2017",
        method="pre-test",
        max_workers=5
    )

