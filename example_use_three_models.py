#!/usr/bin/env python
"""
示例：如何使用完整的三模型Forgetting Score数据 (LPKT + DKT + AKT)

现在所有4个数据集都有3个模型的完整预测！
"""

import json
import numpy as np
from collections import defaultdict

def load_forgetting_scores(dataset, models=['lpkt', 'dkt', 'akt']):
    """
    加载指定数据集的所有模型预测
    
    Args:
        dataset: 数据集名称 (assist2017, nips_task34, algebra2005, bridge2006)
        models: 模型列表
        
    Returns:
        dict: {model_name: forgetting_score_data}
    """
    fs_data = {}
    for model in models:
        path = f'/mnt/localssd/bank/forgetting/{dataset}/{model}.json'
        with open(path, 'r') as f:
            fs_data[model] = json.load(f)
    
    return fs_data

def get_average_fs(student_id, dataset='assist2017', models=['lpkt', 'dkt', 'akt']):
    """
    获取学生在某个数据集上的平均Forgetting Score（三模型平均）
    
    Args:
        student_id: 学生ID (字符串)
        dataset: 数据集名称
        models: 使用的模型列表
        
    Returns:
        dict: {concept: {avg_fs, avg_s_tc, level, model_agreement}}
    """
    fs_data = load_forgetting_scores(dataset, models)
    
    if student_id not in fs_data[models[0]]:
        return None
    
    result = {}
    
    for concept in fs_data[models[0]][student_id]:
        # 收集所有模型的预测
        fs_values = []
        s_tc_values = []
        levels = []
        
        for model in models:
            if student_id in fs_data[model] and concept in fs_data[model][student_id]:
                info = fs_data[model][student_id][concept]
                fs_values.append(info['fs'])
                s_tc_values.append(info['s_tc'])
                levels.append(info['level'])
        
        if len(fs_values) > 0:
            # 计算平均值
            avg_fs = np.mean(fs_values)
            avg_s_tc = np.mean(s_tc_values)
            
            # 确定level（基于平均FS）
            if avg_fs < 0.1:
                avg_level = 'low'
            elif avg_fs < 0.3:
                avg_level = 'medium'
            else:
                avg_level = 'high'
            
            # 检查模型一致性
            model_agreement = len(set(levels)) == 1
            
            result[concept] = {
                'avg_fs': avg_fs,
                'avg_s_tc': avg_s_tc,
                'level': avg_level,
                'model_agreement': model_agreement,
                'individual_models': {
                    models[i]: {
                        'fs': fs_values[i],
                        's_tc': s_tc_values[i],
                        'level': levels[i]
                    } for i in range(len(models))
                }
            }
    
    return result

def analyze_model_agreement(dataset='assist2017'):
    """
    分析三个模型的一致性
    
    Args:
        dataset: 数据集名称
    """
    fs_data = load_forgetting_scores(dataset)
    models = list(fs_data.keys())
    
    agreement_stats = {
        'total': 0,
        'all_agree': 0,
        'two_agree': 0,
        'none_agree': 0
    }
    
    # 统计
    for student in fs_data[models[0]]:
        for concept in fs_data[models[0]][student]:
            levels = [fs_data[m][student][concept]['level'] for m in models]
            
            agreement_stats['total'] += 1
            
            if len(set(levels)) == 1:  # 所有模型一致
                agreement_stats['all_agree'] += 1
            elif len(set(levels)) == 2:  # 两个模型一致
                agreement_stats['two_agree'] += 1
            else:  # 三个模型都不一致
                agreement_stats['none_agree'] += 1
    
    print(f"\n{'='*80}")
    print(f"模型一致性分析 - {dataset}")
    print(f"{'='*80}")
    print(f"总记录数: {agreement_stats['total']}")
    print(f"三模型完全一致: {agreement_stats['all_agree']} ({agreement_stats['all_agree']/agreement_stats['total']*100:.1f}%)")
    print(f"两模型一致: {agreement_stats['two_agree']} ({agreement_stats['two_agree']/agreement_stats['total']*100:.1f}%)")
    print(f"三模型都不一致: {agreement_stats['none_agree']} ({agreement_stats['none_agree']/agreement_stats['total']*100:.1f}%)")
    print()

def find_concepts_needing_review(student_id, dataset='assist2017', threshold='high'):
    """
    找出需要复习的concepts（基于三模型平均）
    
    Args:
        student_id: 学生ID
        dataset: 数据集名称
        threshold: FS阈值 ('high', 'medium', 'low')
        
    Returns:
        list: 需要复习的concepts及其FS信息
    """
    avg_fs = get_average_fs(student_id, dataset)
    
    if avg_fs is None:
        return []
    
    needs_review = []
    for concept, info in avg_fs.items():
        if threshold == 'high' and info['level'] == 'high':
            needs_review.append((concept, info))
        elif threshold == 'medium' and info['level'] in ['medium', 'high']:
            needs_review.append((concept, info))
        elif threshold == 'low':  # 所有concepts
            needs_review.append((concept, info))
    
    # 按FS降序排序
    needs_review.sort(key=lambda x: x[1]['avg_fs'], reverse=True)
    
    return needs_review

# ============================================================================
#                           使用示例
# ============================================================================

if __name__ == '__main__':
    print("="*80)
    print("         Forgetting Score Bank - 三模型综合分析示例")
    print("="*80)
    print()
    print("✅ 所有4个数据集现在都有完整的三模型预测 (LPKT + DKT + AKT)")
    print()
    
    # 示例1：获取学生的平均FS
    print("\n【示例1】获取学生的三模型平均Forgetting Score")
    print("-" * 80)
    
    dataset = 'assist2017'
    student_id = '7'
    
    avg_fs = get_average_fs(student_id, dataset)
    
    if avg_fs:
        print(f"学生 {student_id} 在 {dataset} 上的预测:")
        print(f"  总共 {len(avg_fs)} 个concepts")
        
        # 显示前5个FS最高的concepts
        sorted_concepts = sorted(avg_fs.items(), key=lambda x: x[1]['avg_fs'], reverse=True)
        print(f"\n  前5个需要复习的concepts (FS最高):")
        for i, (concept, info) in enumerate(sorted_concepts[:5], 1):
            print(f"    {i}. {concept}")
            print(f"       平均FS: {info['avg_fs']:.4f} (level: {info['level']})")
            print(f"       平均s_tc: {info['avg_s_tc']:.4f}")
            print(f"       模型一致: {'✅' if info['model_agreement'] else '⚠️'}")
            if not info['model_agreement']:
                print(f"       各模型预测: ", end="")
                for model, pred in info['individual_models'].items():
                    print(f"{model}={pred['level']} ", end="")
                print()
    
    # 示例2：分析模型一致性
    print("\n【示例2】分析三个模型的一致性")
    print("-" * 80)
    
    for dataset in ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']:
        analyze_model_agreement(dataset)
    
    # 示例3：找出需要复习的concepts
    print("\n【示例3】找出需要复习的concepts")
    print("-" * 80)
    
    dataset = 'nips_task34'
    student_id = '2'
    
    high_fs_concepts = find_concepts_needing_review(student_id, dataset, threshold='high')
    
    print(f"学生 {student_id} 在 {dataset} 上需要复习的concepts (high FS):")
    print(f"  共 {len(high_fs_concepts)} 个concepts需要复习\n")
    
    for i, (concept, info) in enumerate(high_fs_concepts[:10], 1):
        print(f"  {i}. {concept}: FS={info['avg_fs']:.4f}, "
              f"s_tc={info['avg_s_tc']:.4f}, "
              f"一致={'✅' if info['model_agreement'] else '⚠️'}")
    
    # 示例4：对比不同数据集的统计
    print("\n【示例4】对比不同数据集的FS分布")
    print("-" * 80)
    
    for dataset in ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']:
        fs_data = load_forgetting_scores(dataset)
        
        # 使用LPKT作为代表（所有模型都有）
        data = fs_data['lpkt']
        
        all_fs = []
        for student in data.values():
            for concept_info in student.values():
                all_fs.append(concept_info['fs'])
        
        print(f"{dataset:20} | 记录数: {len(all_fs):6} | "
              f"平均FS: {np.mean(all_fs):.4f} | "
              f"中位数: {np.median(all_fs):.4f} | "
              f"标准差: {np.std(all_fs):.4f}")
    
    print("\n" + "="*80)
    print("✅ 示例完成！")
    print("="*80)
    print()
    print("💡 提示:")
    print("  - 所有数据集现在都支持三模型平均")
    print("  - 可以根据model_agreement判断预测的可靠性")
    print("  - 建议使用平均值来减少单一模型的偏差")
    print()

