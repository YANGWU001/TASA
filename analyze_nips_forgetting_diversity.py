#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析nips_task34数据集中学生在不同concept上的Forgetting Score差异
重点展示同一学生不同concept之间的差异
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random

# 设置随机种子
random.seed(42)
np.random.seed(42)

# 配置
TAU = 3 * 24 * 60  # 3天 = 4320分钟
DATASET = 'nips_task34'
DATA_PATH = '/mnt/localssd/pykt-toolkit/data/nips_task34/test_sequences.csv'

print("="*100)
print(f"分析学生在不同Concept上的Forgetting Score差异")
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
    """计算forgetting score"""
    time_factor = delta_t_minutes / (delta_t_minutes + tau)
    return (1 - s_tc) * time_factor

def analyze_student_diversity(student_row, current_timestamp=None):
    """分析单个学生在不同concept上的差异"""
    questions = parse_field(student_row['questions'])
    concepts = parse_field(student_row['concepts'])
    responses = parse_field(student_row['responses'])
    timestamps = parse_field(student_row['timestamps'])
    
    if len(concepts) == 0:
        return None
    
    # 使用最后timestamp + 3天作为当前时间
    if current_timestamp is None:
        current_timestamp = timestamps[-1] + (3 * 24 * 60 * 60 * 1000)
    
    # 统计每个concept
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
        s_tc = stats['correct_count'] / stats['total_count']
        delta_t_ms = current_timestamp - stats['last_timestamp']
        delta_t_minutes = max(0, delta_t_ms / (1000 * 60))
        forgetting_score = calculate_forgetting_score(s_tc, delta_t_minutes, TAU)
        
        results.append({
            'concept_id': cid,
            'total_attempts': stats['total_count'],
            'correct_count': stats['correct_count'],
            'accuracy': s_tc,
            'delta_t_days': delta_t_minutes / (24 * 60),
            'forgetting_score': forgetting_score,
            'mastery_level': s_tc  # 掌握程度
        })
    
    # 按concept_id排序（便于观察）
    results.sort(key=lambda x: x['concept_id'])
    
    # 计算差异统计
    fs_values = [r['forgetting_score'] for r in results]
    acc_values = [r['accuracy'] for r in results]
    
    diversity_stats = {
        'fs_mean': np.mean(fs_values),
        'fs_std': np.std(fs_values),
        'fs_min': np.min(fs_values),
        'fs_max': np.max(fs_values),
        'fs_range': np.max(fs_values) - np.min(fs_values),
        'acc_mean': np.mean(acc_values),
        'acc_std': np.std(acc_values),
        'acc_min': np.min(acc_values),
        'acc_max': np.max(acc_values),
    }
    
    return {
        'uid': student_row['uid'],
        'total_interactions': len(concepts),
        'unique_concepts': len(concept_stats),
        'overall_accuracy': sum(responses) / len(responses),
        'concept_results': results,
        'diversity_stats': diversity_stats
    }

# 加载数据
print("\n第1步：加载nips_task34数据")
print("-"*100)

df = pd.read_csv(DATA_PATH)
all_students = df['uid'].unique().tolist()

# 选择做过多个concept的学生（更能体现差异）
print("筛选条件：选择做过5个以上concepts的学生")
qualified_students = []
for uid in all_students:
    student_row = df[df['uid'] == uid].iloc[0]
    concepts = parse_field(student_row['concepts'])
    unique_concepts = len(set(concepts))
    if unique_concepts >= 5:  # 至少5个不同的concepts
        qualified_students.append(uid)

print(f"✅ 共有{len(qualified_students)}个学生满足条件（做过5+个concepts）")

# 随机选择5个学生
selected_students = random.sample(qualified_students, min(5, len(qualified_students)))
print(f"✅ 随机选择5个学生进行详细分析:")
for i, uid in enumerate(selected_students, 1):
    print(f"   {i}. 学生ID: {uid}")

# 分析每个学生
print("\n第2步：分析每个学生在不同Concepts上的Forgetting Score")
print("="*100)

student_analyses = []
for uid in selected_students:
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student_diversity(student_row)
    if analysis:
        student_analyses.append(analysis)
        
        div = analysis['diversity_stats']
        print(f"\n学生 {uid}:")
        print(f"  总体信息: {analysis['total_interactions']}次交互, "
              f"{analysis['unique_concepts']}个concept, "
              f"正确率{analysis['overall_accuracy']*100:.1f}%")
        print(f"  Forgetting Score统计:")
        print(f"    - 平均值: {div['fs_mean']:.4f}")
        print(f"    - 标准差: {div['fs_std']:.4f}")
        print(f"    - 范围: [{div['fs_min']:.4f}, {div['fs_max']:.4f}]")
        print(f"    - 差值: {div['fs_range']:.4f}")
        print(f"  掌握程度统计:")
        print(f"    - 平均正确率: {div['acc_mean']*100:.1f}%")
        print(f"    - 标准差: {div['acc_std']:.4f}")
        print(f"    - 范围: [{div['acc_min']*100:.0f}%, {div['acc_max']*100:.0f}%]")

# 详细展示每个学生的concept差异
print("\n" + "="*100)
print("第3步：详细展示 - 每个学生不同Concept的Forgetting Score对比")
print("="*100)

for idx, analysis in enumerate(student_analyses, 1):
    print(f"\n{'='*100}")
    print(f"学生 #{idx}: ID {analysis['uid']}")
    print(f"{'='*100}")
    
    results = analysis['concept_results']
    
    print(f"\n所有Concepts的详细数据:")
    print(f"{'-'*100}")
    print(f"{'Concept':<10} {'尝试次数':<10} {'正确次数':<10} {'正确率':<10} "
          f"{'时间间隔':<12} {'Forgetting Score':<18} {'分类':<10}")
    print(f"{'-'*100}")
    
    for result in results:
        cid = result['concept_id']
        attempts = result['total_attempts']
        correct = result['correct_count']
        accuracy = result['accuracy'] * 100
        delta_days = result['delta_t_days']
        fs = result['forgetting_score']
        
        # 分类
        if fs >= 0.3:
            category = "🔴 紧急"
        elif fs >= 0.2:
            category = "🟠 重要"
        elif fs >= 0.1:
            category = "🟡 一般"
        else:
            category = "🟢 维持"
        
        print(f"{cid:<10} {attempts:<10} {correct:<10} {accuracy:<9.1f}% "
              f"{delta_days:<11.2f}天 {fs:<18.6f} {category:<10}")
    
    # 可视化差异（用ASCII图）
    print(f"\n Forgetting Score 分布可视化:")
    print(f"{'-'*100}")
    
    # 按FS排序
    sorted_results = sorted(results, key=lambda x: x['forgetting_score'], reverse=True)
    
    for result in sorted_results[:10]:  # 只显示前10个
        cid = result['concept_id']
        fs = result['forgetting_score']
        acc = result['accuracy']
        
        # 创建ASCII条形图
        bar_length = int(fs * 50)  # 最大50个字符
        bar = '█' * bar_length
        
        print(f"  Concept {cid:>3} [{acc*100:>5.1f}%]: {bar} {fs:.4f}")
    
    # 分析差异来源
    print(f"\n 差异分析:")
    print(f"{'-'*100}")
    
    # 1. 掌握程度差异
    high_mastery = [r for r in results if r['accuracy'] >= 0.7]
    low_mastery = [r for r in results if r['accuracy'] <= 0.3]
    
    print(f"  掌握程度差异:")
    print(f"    - 掌握良好 (正确率≥70%): {len(high_mastery)} 个concepts")
    if high_mastery:
        avg_fs_high = np.mean([r['forgetting_score'] for r in high_mastery])
        print(f"      平均Forgetting Score: {avg_fs_high:.4f}")
    
    print(f"    - 掌握较差 (正确率≤30%): {len(low_mastery)} 个concepts")
    if low_mastery:
        avg_fs_low = np.mean([r['forgetting_score'] for r in low_mastery])
        print(f"      平均Forgetting Score: {avg_fs_low:.4f}")
    
    if high_mastery and low_mastery:
        diff = avg_fs_low - avg_fs_high
        print(f"    - 差异: 掌握差的concepts比掌握好的高 {diff:.4f}")
    
    # 2. 时间差异（虽然在测试集中时间间隔通常一致，但还是检查一下）
    time_diffs = [r['delta_t_days'] for r in results]
    time_std = np.std(time_diffs)
    print(f"\n  时间间隔差异:")
    print(f"    - 标准差: {time_std:.4f} 天")
    if time_std < 0.1:
        print(f"    - 所有concepts的时间间隔基本一致")
    else:
        print(f"    - 不同concepts的时间间隔有差异")

# 跨学生对比
print("\n" + "="*100)
print("第4步：跨学生对比 - Forgetting Score差异程度")
print("="*100)

print(f"\n{'学生ID':<12} {'Concepts数':<12} {'FS均值':<12} {'FS标准差':<12} "
      f"{'FS范围':<20} {'差异程度':<10}")
print("-"*100)

for analysis in student_analyses:
    uid = analysis['uid']
    n_concepts = analysis['unique_concepts']
    div = analysis['diversity_stats']
    
    # 判断差异程度
    if div['fs_std'] > 0.2:
        diversity_level = "大"
    elif div['fs_std'] > 0.1:
        diversity_level = "中"
    else:
        diversity_level = "小"
    
    fs_range_str = f"[{div['fs_min']:.3f}, {div['fs_max']:.3f}]"
    
    print(f"{uid:<12} {n_concepts:<12} {div['fs_mean']:<12.4f} {div['fs_std']:<12.4f} "
          f"{fs_range_str:<20} {diversity_level:<10}")

# 关键洞察
print("\n" + "="*100)
print("第5步：关键洞察 - 为什么同一学生不同Concept的Forgetting Score不同？")
print("="*100)

print("""
从分析结果可以看出，同一个学生在不同concepts上的Forgetting Score确实存在差异。

主要原因包括：

1. 【掌握程度差异】★ 最重要因素
   
   公式: F_c(t) = (1 - s_{t,c}) × (时间因子)
   
   - s_{t,c}是预测的正确概率（基于历史表现）
   - 掌握好的concept (s_{t,c}高): (1 - s_{t,c})小 → FS低
   - 掌握差的concept (s_{t,c}低): (1 - s_{t,c})大 → FS高
   
   例如:
   - Concept A: 正确率90% → s_{t,c}=0.9 → (1-s_{t,c})=0.1 → FS≈0.05
   - Concept B: 正确率10% → s_{t,c}=0.1 → (1-s_{t,c})=0.9 → FS≈0.45
   - 差异: 0.40！

2. 【时间间隔差异】
   
   如果学生在不同concepts上的最后答题时间不同：
   - 最近做过的concept: 时间间隔短 → 时间因子小 → FS低
   - 很久没做的concept: 时间间隔长 → 时间因子大 → FS高
   
   (注: 在测试集中，通常时间间隔一致，这个因素影响较小)

3. 【学习次数差异】
   
   虽然不直接影响公式，但影响s_{t,c}的稳定性：
   - 做过很多次的concept: 正确率更可靠
   - 只做过1-2次的concept: 正确率可能不准确
   
4. 【实际案例】
   
   假设学生在3天前做过多个concepts，时间因子相同(0.5):
   
   | Concept | 正确率 | s_{t,c} | (1-s_{t,c}) | FS = (1-s)×0.5 |
   |---------|--------|---------|-------------|----------------|
   | A       | 100%   | 1.0     | 0.0         | 0.000          |
   | B       | 80%    | 0.8     | 0.2         | 0.100          |
   | C       | 50%    | 0.5     | 0.5         | 0.250          |
   | D       | 20%    | 0.2     | 0.8         | 0.400          |
   | E       | 0%     | 0.0     | 1.0         | 0.500          |
   
   → 同一时间间隔下，FS从0.0到0.5，差异巨大！

结论: 
✅ 同一学生不同concept的Forgetting Score确实不同
✅ 主要由掌握程度(s_{t,c})差异导致
✅ 这种差异是合理的，反映了学生对不同知识点的掌握情况
✅ 可用于个性化推荐：优先复习高FS的concepts
""")

print("="*100)
print("✅ 分析完成！")
print("="*100)

