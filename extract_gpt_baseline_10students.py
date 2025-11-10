#!/opt/venv/bin/python3
"""
从现有的GPT-OSS-120B baseline结果中提取10人样本的结果
"""

import json
import os
from pathlib import Path

# 读取各数据集的10人样本ID
DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']
METHODS = ['Vanilla-ICL-conservative', 'MathChat-conservative', 'TutorLLM-conservative', 'PSS-MV-conservative']

def load_sampled_students(dataset):
    """加载指定数据集的10人样本ID"""
    file_path = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    with open(file_path, 'r') as f:
        data = json.load(f)
    return set(data['sampled_students'])

def extract_student_results(method, dataset, sampled_ids):
    """从现有结果中提取指定学生的结果"""
    source_dir = f'/mnt/localssd/bank/evaluation_results/{method}/{dataset}'
    
    if not os.path.exists(source_dir):
        print(f"   ⚠️  源目录不存在: {source_dir}")
        return None
    
    # 读取所有学生结果
    student_files = [f for f in os.listdir(source_dir) if f.startswith('student_') and f.endswith('.json')]
    
    extracted_results = []
    found_ids = set()
    
    for student_file in student_files:
        # 提取学生ID
        student_id = int(student_file.replace('student_', '').replace('.json', ''))
        
        if student_id in sampled_ids:
            with open(f'{source_dir}/{student_file}', 'r') as f:
                result = json.load(f)
            extracted_results.append(result)
            found_ids.add(student_id)
    
    missing_ids = sampled_ids - found_ids
    if missing_ids:
        print(f"   ⚠️  缺失学生: {sorted(missing_ids)}")
    
    return extracted_results, found_ids

def calculate_overall_stats(results):
    """计算整体统计"""
    if not results:
        return None
    
    import numpy as np
    
    # 提取learning gains (使用average strategy)
    gains_avg = []
    gains_min = []
    gains_max = []
    
    for r in results:
        if 'learning_gain_avg' in r:
            gains_avg.append(r['learning_gain_avg'])
        if 'learning_gain_min' in r:
            gains_min.append(r['learning_gain_min'])
        if 'learning_gain_max' in r:
            gains_max.append(r['learning_gain_max'])
    
    overall = {
        'num_students': len(results),
        'strategy_avg': {
            'avg_learning_gain': float(np.mean(gains_avg)) if gains_avg else 0,
            'std_learning_gain': float(np.std(gains_avg)) if gains_avg else 0,
            'positive_count': sum(1 for g in gains_avg if g > 0),
            'negative_count': sum(1 for g in gains_avg if g <= 0)
        },
        'strategy_min': {
            'avg_learning_gain': float(np.mean(gains_min)) if gains_min else 0,
            'std_learning_gain': float(np.std(gains_min)) if gains_min else 0,
            'positive_count': sum(1 for g in gains_min if g > 0),
            'negative_count': sum(1 for g in gains_min if g <= 0)
        },
        'strategy_max': {
            'avg_learning_gain': float(np.mean(gains_max)) if gains_max else 0,
            'std_learning_gain': float(np.std(gains_max)) if gains_max else 0,
            'positive_count': sum(1 for g in gains_max if g > 0),
            'negative_count': sum(1 for g in gains_max if g <= 0)
        }
    }
    
    return overall

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 提取GPT-OSS-120B Baseline结果 (10人样本)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    summary = {}
    
    for dataset in DATASETS:
        print(f"📁 数据集: {dataset}")
        
        # 加载10人样本ID
        sampled_ids = load_sampled_students(dataset)
        print(f"   • 样本学生数: {len(sampled_ids)}")
        print(f"   • 学生IDs: {sorted(sampled_ids)}\n")
        
        dataset_summary = {}
        
        for method in METHODS:
            print(f"   🔍 方法: {method}")
            
            results, found_ids = extract_student_results(method, dataset, sampled_ids)
            
            if results:
                print(f"      ✅ 找到 {len(results)}/{len(sampled_ids)} 个学生")
                
                # 计算统计
                overall = calculate_overall_stats(results)
                
                # 保存到新目录（带gpt标识）
                output_dir = f'/mnt/localssd/bank/evaluation_results/{method}-gpt/{dataset}'
                os.makedirs(output_dir, exist_ok=True)
                
                # 保存学生结果
                for result in results:
                    student_id = result['student_id']
                    output_file = f'{output_dir}/student_{student_id}.json'
                    with open(output_file, 'w') as f:
                        json.dump(result, f, indent=2)
                
                # 保存overall.json
                overall_data = {
                    'dataset': dataset,
                    'method': method,
                    'backbone': 'gpt-oss-120b',
                    'num_students': len(results),
                    'overall': overall,
                    'students': results
                }
                
                with open(f'{output_dir}/overall.json', 'w') as f:
                    json.dump(overall_data, f, indent=2)
                
                print(f"      📊 Average Gain: {overall['strategy_avg']['avg_learning_gain']*100:.1f}%")
                print(f"      📊 Min Gain:     {overall['strategy_min']['avg_learning_gain']*100:.1f}%")
                print(f"      📊 Max Gain:     {overall['strategy_max']['avg_learning_gain']*100:.1f}%")
                print(f"      💾 已保存到: {output_dir}/")
                
                dataset_summary[method] = overall
            else:
                print(f"      ❌ 未找到结果")
            
            print()
        
        summary[dataset] = dataset_summary
        print("─" * 80 + "\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ GPT-OSS-120B Baseline结果提取完成")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    main()

