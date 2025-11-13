#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为5个学生计算每个concept的Forgetting Score
使用τ = 3天 (4320分钟)
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random

# 设置随机种子以保证可重复性
random.seed(42)
np.random.seed(42)

# 配置
TAU = 3 * 24 * 60  # 3天 = 4320分钟
DATASET = 'ednet'
DATA_PATH = '/mnt/localssd/pykt-toolkit/data/ednet/test_sequences.csv'

print("="*100)
print(f"为5个学生计算Forgetting Score")
print(f"数据集: {DATASET.upper()}")
print(f"时间衰减参数: τ = 3天 = {TAU} 分钟")
print("="*100)

# 辅助函数
def parse_field(field_str):
    """解析CSV字段"""
    if pd.isna(field_str) or field_str == '' or str(field_str) == '-1':
        return []
    return [int(x) for x in str(field_str).split(',') if x.strip() != '-1' and x.strip() != '']

def calculate_forgetting_score(s_tc, delta_t_minutes, tau=TAU):
    """
    计算forgetting score
    F_c(t) = (1 - s_t,c) × (Δt_c / (Δt_c + τ))
    """
    time_factor = delta_t_minutes / (delta_t_minutes + tau)
    return (1 - s_tc) * time_factor

def analyze_student(student_row, current_timestamp=None):
    """分析单个学生的concept掌握情况"""
    questions = parse_field(student_row['questions'])
    concepts = parse_field(student_row['concepts'])
    responses = parse_field(student_row['responses'])
    timestamps = parse_field(student_row['timestamps'])
    
    if len(concepts) == 0:
        return None
    
    # 如果没有提供当前时间，使用最后一个timestamp + 3天
    if current_timestamp is None:
        current_timestamp = timestamps[-1] + (3 * 24 * 60 * 60 * 1000)  # 加3天（毫秒）
    
    # 统计每个concept的信息
    concept_stats = defaultdict(lambda: {
        'interactions': [],
        'last_timestamp': 0,
        'correct_count': 0,
        'total_count': 0
    })
    
    for i in range(len(concepts)):
        cid = concepts[i]
        concept_stats[cid]['interactions'].append({
            'index': i,
            'question': questions[i],
            'response': responses[i],
            'timestamp': timestamps[i]
        })
        concept_stats[cid]['last_timestamp'] = timestamps[i]
        concept_stats[cid]['total_count'] += 1
        concept_stats[cid]['correct_count'] += responses[i]
    
    # 计算每个concept的forgetting score
    results = []
    for cid, stats in concept_stats.items():
        # 使用历史正确率作为预测概率s_t,c的估算
        s_tc = stats['correct_count'] / stats['total_count']
        
        # 计算时间间隔（从最后一次做该concept到现在）
        delta_t_ms = current_timestamp - stats['last_timestamp']
        delta_t_minutes = delta_t_ms / (1000 * 60)  # 转换为分钟
        
        # 确保时间间隔非负
        if delta_t_minutes < 0:
            delta_t_minutes = 0
        
        # 计算forgetting score
        forgetting_score = calculate_forgetting_score(s_tc, delta_t_minutes, TAU)
        
        results.append({
            'concept_id': cid,
            'total_attempts': stats['total_count'],
            'correct_count': stats['correct_count'],
            'accuracy': s_tc,
            'predicted_prob': s_tc,  # 简化：使用历史正确率
            'delta_t_minutes': delta_t_minutes,
            'delta_t_days': delta_t_minutes / (24 * 60),
            'forgetting_score': forgetting_score
        })
    
    # 按forgetting score降序排列
    results.sort(key=lambda x: x['forgetting_score'], reverse=True)
    
    return {
        'uid': student_row['uid'],
        'total_interactions': len(concepts),
        'unique_concepts': len(concept_stats),
        'overall_accuracy': sum(responses) / len(responses) if responses else 0,
        'concept_results': results
    }

# 加载数据
print("\n第1步：加载数据并随机选择5个学生")
print("-"*100)

df = pd.read_csv(DATA_PATH)
all_students = df['uid'].unique().tolist()

# 随机选择5个学生
selected_students = random.sample(all_students, min(5, len(all_students)))
print(f"✅ 从{len(all_students)}个学生中随机选择了5个:")
for i, uid in enumerate(selected_students, 1):
    print(f"   {i}. 学生ID: {uid}")

# 分析每个学生
print("\n第2步：分析每个学生的concept掌握情况")
print("-"*100)

student_analyses = []
for uid in selected_students:
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student(student_row)
    if analysis:
        student_analyses.append(analysis)
        print(f"✅ 学生{uid}: {analysis['total_interactions']}次交互, "
              f"{analysis['unique_concepts']}个concept, "
              f"正确率{analysis['overall_accuracy']*100:.1f}%")

# 生成详细报告
print("\n" + "="*100)
print("第3步：详细报告 - 每个学生的Forgetting Score")
print("="*100)

for idx, analysis in enumerate(student_analyses, 1):
    print(f"\n{'='*100}")
    print(f"学生 #{idx}: ID {analysis['uid']}")
    print(f"{'='*100}")
    print(f"总体信息:")
    print(f"  - 总交互数: {analysis['total_interactions']}")
    print(f"  - 唯一概念数: {analysis['unique_concepts']}")
    print(f"  - 总体正确率: {analysis['overall_accuracy']*100:.1f}%")
    
    print(f"\n前10个最需要复习的概念 (Forgetting Score最高):")
    print(f"{'-'*100}")
    print(f"{'Concept':<10} {'次数':<8} {'正确率':<10} {'预测概率':<12} "
          f"{'时间间隔':<15} {'Forgetting Score':<18} {'建议':<10}")
    print(f"{'-'*100}")
    
    for result in analysis['concept_results'][:10]:
        cid = result['concept_id']
        attempts = result['total_attempts']
        accuracy = result['accuracy'] * 100
        pred_prob = result['predicted_prob']
        delta_days = result['delta_t_days']
        fs = result['forgetting_score']
        
        # 根据forgetting score给出建议
        if fs >= 0.3:
            suggestion = "🔴 紧急"
        elif fs >= 0.2:
            suggestion = "🟠 重要"
        elif fs >= 0.1:
            suggestion = "🟡 一般"
        else:
            suggestion = "🟢 维持"
        
        print(f"{cid:<10} {attempts:<8} {accuracy:<9.1f}% {pred_prob:<12.3f} "
              f"{delta_days:<14.2f}天 {fs:<18.6f} {suggestion:<10}")
    
    # 统计分布
    fs_values = [r['forgetting_score'] for r in analysis['concept_results']]
    urgent = sum(1 for fs in fs_values if fs >= 0.3)
    important = sum(1 for fs in fs_values if 0.2 <= fs < 0.3)
    normal = sum(1 for fs in fs_values if 0.1 <= fs < 0.2)
    maintain = sum(1 for fs in fs_values if fs < 0.1)
    
    print(f"\n复习优先级分布:")
    print(f"  🔴 紧急 (FS≥0.3):  {urgent} 个concept ({urgent/len(fs_values)*100:.1f}%)")
    print(f"  🟠 重要 (0.2≤FS<0.3): {important} 个concept ({important/len(fs_values)*100:.1f}%)")
    print(f"  🟡 一般 (0.1≤FS<0.2): {normal} 个concept ({normal/len(fs_values)*100:.1f}%)")
    print(f"  🟢 维持 (FS<0.1):  {maintain} 个concept ({maintain/len(fs_values)*100:.1f}%)")

# 生成汇总表格
print("\n" + "="*100)
print("第4步：5个学生的汇总对比")
print("="*100)

print(f"\n{'学生ID':<12} {'交互数':<10} {'概念数':<10} {'正确率':<10} "
      f"{'紧急':<8} {'重要':<8} {'一般':<8} {'维持':<8}")
print("-"*100)

for analysis in student_analyses:
    uid = analysis['uid']
    total_int = analysis['total_interactions']
    unique_c = analysis['unique_concepts']
    accuracy = analysis['overall_accuracy'] * 100
    
    fs_values = [r['forgetting_score'] for r in analysis['concept_results']]
    urgent = sum(1 for fs in fs_values if fs >= 0.3)
    important = sum(1 for fs in fs_values if 0.2 <= fs < 0.3)
    normal = sum(1 for fs in fs_values if 0.1 <= fs < 0.2)
    maintain = sum(1 for fs in fs_values if fs < 0.1)
    
    print(f"{uid:<12} {total_int:<10} {unique_c:<10} {accuracy:<9.1f}% "
          f"{urgent:<8} {important:<8} {normal:<8} {maintain:<8}")

# 保存到CSV文件
print("\n" + "="*100)
print("第5步：保存详细结果到CSV文件")
print("="*100)

all_results = []
for analysis in student_analyses:
    uid = analysis['uid']
    for result in analysis['concept_results']:
        all_results.append({
            'student_id': uid,
            'concept_id': result['concept_id'],
            'attempts': result['total_attempts'],
            'correct': result['correct_count'],
            'accuracy': result['accuracy'],
            'predicted_prob': result['predicted_prob'],
            'time_interval_days': result['delta_t_days'],
            'forgetting_score': result['forgetting_score']
        })

results_df = pd.DataFrame(all_results)
output_file = f'/mnt/localssd/forgetting_scores_5students_{DATASET}.csv'
results_df.to_csv(output_file, index=False)
print(f"✅ 详细结果已保存到: {output_file}")
print(f"   共 {len(all_results)} 条记录 (5个学生 × 每人的concepts)")

print("\n" + "="*100)
print("✅ 完成！")
print("="*100)

# 额外分析：最需要关注的concepts（跨学生）
print("\n" + "="*100)
print("额外分析：哪些concepts最容易被遗忘？（跨学生统计）")
print("="*100)

concept_forgetting = defaultdict(list)
for analysis in student_analyses:
    for result in analysis['concept_results']:
        concept_forgetting[result['concept_id']].append(result['forgetting_score'])

# 计算每个concept的平均forgetting score
concept_avg_fs = {}
for cid, fs_list in concept_forgetting.items():
    concept_avg_fs[cid] = {
        'avg_fs': np.mean(fs_list),
        'count': len(fs_list),
        'max_fs': max(fs_list),
        'min_fs': min(fs_list)
    }

# 排序
sorted_concepts = sorted(concept_avg_fs.items(), key=lambda x: x[1]['avg_fs'], reverse=True)

print(f"\n前15个平均Forgetting Score最高的concepts:")
print(f"{'-'*80}")
print(f"{'Concept':<10} {'学生数':<10} {'平均FS':<15} {'最大FS':<15} {'最小FS':<15}")
print(f"{'-'*80}")

for cid, stats in sorted_concepts[:15]:
    print(f"{cid:<10} {stats['count']:<10} {stats['avg_fs']:<15.6f} "
          f"{stats['max_fs']:<15.6f} {stats['min_fs']:<15.6f}")

print("\n建议：这些concepts需要在课程设计中加强复习和巩固！")
print("="*100)

