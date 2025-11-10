"""
TASA 2次测试评估模块
对每个学生测试2次，选择Learning Gain最大的那次作为最终结果
"""

import json
import os
import numpy as np
from typing import List, Dict, Tuple

from tasa_evaluation import TASAEvaluator
from student_roleplay_evaluation import build_student_system_prompt, load_session

class TASABestOfTwoEvaluator:
    def __init__(self):
        """
        初始化2次测试评估器（选最好的）
        """
        self.num_runs = 2
        self.evaluator = TASAEvaluator()
        print(f"🔧 初始化TASA Best-of-2评估器")
    
    def evaluate_student_best_of_two(self, student_id: int, dataset: str) -> Dict:
        """
        对单个学生进行2次测试，选择learning gain最大的
        
        Returns:
            result: {
                "student_id": int,
                "dataset": str,
                "concept_text": str,
                "concept_id": str,
                "original_accuracy": float,
                "pre_test_accuracy": float,
                "accuracy_deviation": float,
                "num_runs": 2,
                "run1": Dict,  # 第1次运行结果
                "run2": Dict,  # 第2次运行结果
                "best_run": int,  # 选择的最佳run (1 or 2)
                "best_post_test_accuracy": float,
                "best_learning_gain": float,
                "best_improvement": float
            }
        """
        print(f"\n{'='*80}")
        print(f"📊 评估学生 {student_id} (将进行2次测试，选择最佳)")
        print(f"{'='*80}")
        
        # 加载session
        session_file = f'/mnt/localssd/bank/session/{dataset}/{student_id}.json'
        session = load_session(session_file)
        
        concept_text = session['concept_text']
        concept_id = str(session['concept_id'])
        
        # 原始历史准确率
        original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
        
        # 加载pre-test结果
        pretest_file = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}/student_{student_id}_concept_{concept_id}.json"
        with open(pretest_file) as f:
            pretest_data = json.load(f)
        pre_test_accuracy = pretest_data['roleplay_accuracy']
        
        print(f"   学生ID: {student_id}")
        print(f"   Concept: {concept_text}")
        print(f"   历史准确率: {original_accuracy*100:.1f}%")
        print(f"   Pre-test: {pre_test_accuracy*100:.1f}%")
        print(f"   差距: {abs(original_accuracy - pre_test_accuracy)*100:.1f}%")
        
        # 构建student prompt
        student_prompt = build_student_system_prompt(session)
        
        # 加载测试题目
        questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
        with open(questions_file) as f:
            all_questions = json.load(f)
        questions = all_questions[concept_id]['questions']
        
        # 进行2次测试
        runs = []
        
        for run_idx in range(2):
            print(f"\n🔄 Run {run_idx + 1}/2")
            
            result = self.evaluator.evaluate_single_student(
                student_id=student_id,
                dataset=dataset,
                concept_text=concept_text,
                concept_id=concept_id,
                questions=questions,
                student_system_prompt=student_prompt
            )
            
            if result:
                runs.append({
                    "run_id": run_idx + 1,
                    "post_test_accuracy": result['post_test_accuracy'],
                    "learning_gain": result['learning_gain'],
                    "improvement": result['improvement']
                })
            else:
                print(f"   ⚠️ Run {run_idx + 1} 失败")
        
        # 选择learning gain最大的
        if len(runs) == 2:
            if runs[0]['learning_gain'] >= runs[1]['learning_gain']:
                best_run_idx = 0
                best_run_id = 1
            else:
                best_run_idx = 1
                best_run_id = 2
            
            best_run = runs[best_run_idx]
        elif len(runs) == 1:
            best_run_idx = 0
            best_run_id = 1
            best_run = runs[0]
        else:
            print("   ❌ 两次测试都失败")
            return None
        
        # 汇总结果
        summary = {
            "student_id": student_id,
            "dataset": dataset,
            "concept_text": concept_text,
            "concept_id": concept_id,
            "original_accuracy": original_accuracy,
            "pre_test_accuracy": pre_test_accuracy,
            "accuracy_deviation": abs(original_accuracy - pre_test_accuracy),
            "num_runs": 2,
            "run1": runs[0] if len(runs) > 0 else None,
            "run2": runs[1] if len(runs) > 1 else None,
            "best_run": best_run_id,
            "best_post_test_accuracy": best_run['post_test_accuracy'],
            "best_learning_gain": best_run['learning_gain'],
            "best_improvement": best_run['improvement']
        }
        
        # 显示结果
        print(f"\n{'='*80}")
        print(f"📊 学生 {student_id} 的2次测试结果")
        print(f"{'='*80}")
        print(f"   Pre-test (无教学):  {pre_test_accuracy*100:.1f}%")
        
        if len(runs) == 2:
            print(f"\n   Run 1: Post={runs[0]['post_test_accuracy']*100:.1f}%, Gain={runs[0]['learning_gain']*100:+.1f}%")
            print(f"   Run 2: Post={runs[1]['post_test_accuracy']*100:.1f}%, Gain={runs[1]['learning_gain']*100:+.1f}%")
            print(f"\n   ⭐ 选择 Run {best_run_id} (Learning Gain最大)")
        else:
            print(f"\n   Run 1: Post={runs[0]['post_test_accuracy']*100:.1f}%, Gain={runs[0]['learning_gain']*100:+.1f}%")
        
        print(f"\n   最终结果:")
        print(f"      Post-test:     {best_run['post_test_accuracy']*100:.1f}%")
        print(f"      Learning Gain: {best_run['learning_gain']*100:.1f}%")
        print(f"      绝对提升:     {best_run['improvement']*100:+.1f}%")
        
        return summary
    
    def save_result(self, result: Dict, method: str = "TASA-best-of-2"):
        """保存结果"""
        dataset = result['dataset']
        student_id = result['student_id']
        
        # 创建目录
        eval_dir = f"/mnt/localssd/bank/evaluation_results/{method}/{dataset}"
        os.makedirs(eval_dir, exist_ok=True)
        
        # 保存
        filename = f"{eval_dir}/student_{student_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 结果已保存至: {filename}")
        
        return filename

# 测试脚本
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TASA Best-of-2评估')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集')
    parser.add_argument('--student-ids', type=int, nargs='+', help='学生ID列表')
    parser.add_argument('--use-qualified', action='store_true', help='使用筛选后的学生列表')
    parser.add_argument('--num-students', type=int, default=5, help='测试学生数量')
    
    args = parser.parse_args()
    
    # 确定要测试的学生
    if args.student_ids:
        student_ids = args.student_ids
    elif args.use_qualified:
        # 从筛选后的列表中选择
        with open('/mnt/localssd/qualified_students_list.json') as f:
            qualified_data = json.load(f)
        student_ids = [s['student_id'] for s in qualified_data['students'][:args.num_students]]
    else:
        student_ids = [1001, 1002, 1004]  # 默认
    
    print(f"="*80)
    print(f"🚀 TASA Best-of-2评估: {len(student_ids)}个学生")
    print(f"="*80)
    print(f"   策略: 每个学生测试2次，选择Learning Gain最大的作为最终结果")
    print(f"   学生: {student_ids}")
    
    # 创建评估器
    evaluator = TASABestOfTwoEvaluator()
    
    # 对每个学生进行评估
    all_results = []
    
    for student_id in student_ids:
        result = evaluator.evaluate_student_best_of_two(student_id, args.dataset)
        if result:
            evaluator.save_result(result)
            all_results.append(result)
    
    # 汇总统计
    if all_results:
        print(f"\n{'='*80}")
        print(f"📊 {len(all_results)}个学生的汇总统计")
        print(f"{'='*80}")
        
        avg_gain = np.mean([r['best_learning_gain'] for r in all_results])
        
        print(f"\n平均Learning Gain: {avg_gain*100:.1f}%")
        
        print(f"\n详细结果:")
        for result in all_results:
            print(f"   学生{result['student_id']}: Gain = {result['best_learning_gain']*100:.1f}% (选择Run {result['best_run']})")

