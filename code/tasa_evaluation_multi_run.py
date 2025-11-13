"""
TASA多次测试评估模块
支持每个学生测试多次，计算平均Learning Gain和标准差
"""

import json
import os
import numpy as np
from typing import List, Dict, Tuple
from tqdm import tqdm

from tasa_evaluation import TASAEvaluator
from student_roleplay_evaluation import build_student_system_prompt, load_session

class TASAMultiRunEvaluator:
    def __init__(self, num_runs: int = 3):
        """
        初始化多次测试评估器
        
        Args:
            num_runs: 每个学生测试的次数
        """
        self.num_runs = num_runs
        self.evaluator = TASAEvaluator()
        print(f"🔧 初始化TASA多次测试评估器 (每个学生测试{num_runs}次)")
    
    def evaluate_student_multi_runs(self, student_id: int, dataset: str) -> Dict:
        """
        对单个学生进行多次测试
        
        Returns:
            result: {
                "student_id": int,
                "dataset": str,
                "concept_text": str,
                "concept_id": str,
                "original_accuracy": float,  # 历史准确率
                "pre_test_accuracy": float,  # Pre-test roleplay准确率
                "num_runs": int,
                "runs": List[Dict],  # 每次运行的详细结果
                "avg_post_test_accuracy": float,  # 平均post-test准确率
                "std_post_test_accuracy": float,  # post-test准确率标准差
                "avg_learning_gain": float,  # 平均learning gain
                "std_learning_gain": float,  # learning gain标准差
                "avg_improvement": float,  # 平均绝对提升
                "std_improvement": float   # 绝对提升标准差
            }
        """
        print(f"\n{'='*80}")
        print(f"📊 评估学生 {student_id} (将进行{self.num_runs}次测试)")
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
        print(f"   Pre-test准确率: {pre_test_accuracy*100:.1f}%")
        print(f"   差距: {abs(original_accuracy - pre_test_accuracy)*100:.1f}%")
        
        # 构建student prompt
        student_prompt = build_student_system_prompt(session)
        
        # 加载测试题目
        questions_file = f'/mnt/localssd/bank/test_data/{dataset}/concept_questions.json'
        with open(questions_file) as f:
            all_questions = json.load(f)
        questions = all_questions[concept_id]['questions']
        
        # 进行多次测试
        runs = []
        post_test_accuracies = []
        learning_gains = []
        improvements = []
        
        for run_idx in range(self.num_runs):
            print(f"\n🔄 Run {run_idx + 1}/{self.num_runs}")
            
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
                
                post_test_accuracies.append(result['post_test_accuracy'])
                learning_gains.append(result['learning_gain'])
                improvements.append(result['improvement'])
            else:
                print(f"   ⚠️ Run {run_idx + 1} 失败")
        
        # 计算统计量
        avg_post_test = np.mean(post_test_accuracies)
        std_post_test = np.std(post_test_accuracies, ddof=1) if len(post_test_accuracies) > 1 else 0
        
        avg_learning_gain = np.mean(learning_gains)
        std_learning_gain = np.std(learning_gains, ddof=1) if len(learning_gains) > 1 else 0
        
        avg_improvement = np.mean(improvements)
        std_improvement = np.std(improvements, ddof=1) if len(improvements) > 1 else 0
        
        # 汇总结果
        summary = {
            "student_id": student_id,
            "dataset": dataset,
            "concept_text": concept_text,
            "concept_id": concept_id,
            "original_accuracy": original_accuracy,
            "pre_test_accuracy": pre_test_accuracy,
            "accuracy_deviation": abs(original_accuracy - pre_test_accuracy),
            "num_runs": self.num_runs,
            "runs": runs,
            "avg_post_test_accuracy": avg_post_test,
            "std_post_test_accuracy": std_post_test,
            "avg_learning_gain": avg_learning_gain,
            "std_learning_gain": std_learning_gain,
            "avg_improvement": avg_improvement,
            "std_improvement": std_improvement
        }
        
        # 显示统计结果
        print(f"\n{'='*80}")
        print(f"📊 学生 {student_id} 的{self.num_runs}次测试统计结果")
        print(f"{'='*80}")
        print(f"   Pre-test (无教学):  {pre_test_accuracy*100:.1f}%")
        print(f"   Post-test 平均:     {avg_post_test*100:.1f}% ± {std_post_test*100:.1f}%")
        print(f"   Learning Gain:      {avg_learning_gain*100:.1f}% ± {std_learning_gain*100:.1f}%")
        print(f"   绝对提升:           {avg_improvement*100:+.1f}% ± {std_improvement*100:.1f}%")
        
        print(f"\n   每次运行详情:")
        for run in runs:
            print(f"      Run {run['run_id']}: Post={run['post_test_accuracy']*100:.1f}%, "
                  f"Gain={run['learning_gain']*100:.1f}%")
        
        return summary
    
    def save_multi_run_result(self, result: Dict, method: str = "TASA-multi"):
        """保存多次测试结果"""
        dataset = result['dataset']
        student_id = result['student_id']
        
        # 创建目录
        eval_dir = f"/mnt/localssd/bank/evaluation_results/{method}/{dataset}"
        os.makedirs(eval_dir, exist_ok=True)
        
        # 保存
        filename = f"{eval_dir}/student_{student_id}_multi_run.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 多次测试结果已保存至: {filename}")
        
        return filename

def find_qualified_students(dataset: str = "assist2017", max_deviation: float = 0.1, num_students: int = 3) -> List[int]:
    """
    找到符合条件的学生（历史准确率和pre-test结果差距不超过threshold）
    
    Args:
        dataset: 数据集名称
        max_deviation: 最大允许偏差（默认0.1即10%）
        num_students: 需要找到的学生数量
    
    Returns:
        qualified_student_ids: 符合条件的学生ID列表
    """
    print(f"\n🔍 查找符合条件的学生...")
    print(f"   条件: 历史准确率 vs Pre-test准确率差距 ≤ {max_deviation*100:.0f}%")
    
    # 读取session目录获取所有学生
    session_dir = f"/mnt/localssd/bank/session/{dataset}"
    pretest_dir = f"/mnt/localssd/bank/evaluation_results/pre-test/{dataset}"
    
    qualified = []
    
    # 遍历session文件
    session_files = sorted([f for f in os.listdir(session_dir) if f.endswith('.json')])
    
    for session_file in session_files:
        student_id = int(session_file.replace('.json', ''))
        
        try:
            # 加载session
            with open(f"{session_dir}/{session_file}") as f:
                session = json.load(f)
            
            concept_id = str(session['concept_id'])
            original_accuracy = session['persona']['stats']['correct'] / session['persona']['stats']['total']
            
            # 加载pre-test结果
            pretest_file = f"{pretest_dir}/student_{student_id}_concept_{concept_id}.json"
            if not os.path.exists(pretest_file):
                continue
            
            with open(pretest_file) as f:
                pretest_data = json.load(f)
            
            pre_test_accuracy = pretest_data['roleplay_accuracy']
            
            # 检查偏差
            deviation = abs(original_accuracy - pre_test_accuracy)
            
            if deviation <= max_deviation:
                qualified.append({
                    'student_id': student_id,
                    'concept_text': session['concept_text'],
                    'original_accuracy': original_accuracy,
                    'pre_test_accuracy': pre_test_accuracy,
                    'deviation': deviation
                })
                
                if len(qualified) >= num_students:
                    break
        
        except Exception as e:
            continue
    
    print(f"\n✅ 找到 {len(qualified)} 个符合条件的学生:\n")
    for i, student in enumerate(qualified, 1):
        print(f"   {i}. 学生{student['student_id']} - {student['concept_text']}")
        print(f"      历史准确率: {student['original_accuracy']*100:.1f}%")
        print(f"      Pre-test:   {student['pre_test_accuracy']*100:.1f}%")
        print(f"      差距:       {student['deviation']*100:.1f}%")
    
    return [s['student_id'] for s in qualified]

# 测试脚本
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TASA多次测试评估')
    parser.add_argument('--dataset', type=str, default='assist2017', help='数据集')
    parser.add_argument('--num-runs', type=int, default=3, help='每个学生测试次数')
    parser.add_argument('--max-deviation', type=float, default=0.1, help='最大允许偏差(0.1=10%)')
    parser.add_argument('--num-students', type=int, default=3, help='测试学生数量')
    
    args = parser.parse_args()
    
    # 查找符合条件的学生
    qualified_students = find_qualified_students(
        dataset=args.dataset,
        max_deviation=args.max_deviation,
        num_students=args.num_students
    )
    
    if not qualified_students:
        print("\n❌ 未找到符合条件的学生")
        exit(1)
    
    # 创建评估器
    evaluator = TASAMultiRunEvaluator(num_runs=args.num_runs)
    
    # 对每个学生进行多次测试
    all_results = []
    
    for student_id in qualified_students:
        result = evaluator.evaluate_student_multi_runs(student_id, args.dataset)
        evaluator.save_multi_run_result(result)
        all_results.append(result)
    
    # 汇总所有学生的结果
    print(f"\n{'='*80}")
    print(f"📊 {len(all_results)}个学生的汇总统计")
    print(f"{'='*80}")
    
    for result in all_results:
        print(f"\n学生{result['student_id']} - {result['concept_text']}:")
        print(f"  Learning Gain: {result['avg_learning_gain']*100:.1f}% ± {result['std_learning_gain']*100:.1f}%")

