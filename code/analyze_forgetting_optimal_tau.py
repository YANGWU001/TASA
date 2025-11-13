#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用优化的τ值重新计算Forgetting Score
τ = 平均答题间隔 ≈ 3天
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random

# 设置随机种子
random.seed(42)
np.random.seed(42)

DATASET = 'nips_task34'
DATA_PATH = '/mnt/localssd/pykt-toolkit/data/nips_task34/test_sequences.csv'

# 使用平均间隔作为τ
TAU_MINUTES = 4224  # ≈ 3天
TAU_DAYS = TAU_MINUTES / (60 * 24)

print("="*100)
print(f"使用优化τ值计算Forgetting Score")
print(f"数据集: {DATASET.upper()}")
print(f"τ = {TAU_MINUTES:.0f} 分钟 = {TAU_DAYS:.2f} 天 (数据集平均答题间隔)")
print("="*100)

# 辅助函数
def parse_field(field_str):
    """解析CSV字段"""
    if pd.isna(field_str) or field_str == '' or str(field_str) == '-1':
        return []
    return [int(x) for x in str(field_str).split(',') if x.strip() != '-1' and x.strip() != '']

def calculate_forgetting_score(s_tc, delta_t_minutes, tau):
    """计算forgetting score"""
    if delta_t_minutes <= 0:
        return 0.0
    time_factor = delta_t_minutes / (delta_t_minutes + tau)
    return (1 - s_tc) * time_factor

def analyze_student_with_optimal_tau(student_row, tau):
    """使用优化τ值分析学生"""
    questions = parse_field(student_row['questions'])
    concepts = parse_field(student_row['concepts'])
    responses = parse_field(student_row['responses'])
    timestamps = parse_field(student_row['timestamps'])
    
    if len(concepts) < 2:
        return None
    
    # 按concept分组
    concept_data = defaultdict(list)
    for i in range(len(concepts)):
        concept_data[concepts[i]].append({
            'index': i,
            'question': questions[i],
            'response': responses[i],
            'timestamp': timestamps[i]
        })
    
    results = []
    
    for cid, interactions in concept_data.items():
        if len(interactions) < 2:
            continue
        
        # 按时间排序
        interactions_sorted = sorted(interactions, key=lambda x: x['timestamp'])
        
        # 历史正确率（不包括最后一次）
        historical_responses = [inter['response'] for inter in interactions_sorted[:-1]]
        s_tc = sum(historical_responses) / len(historical_responses)
        
        # 计算最后两次的时间间隔
        last_timestamp = interactions_sorted[-1]['timestamp']
        second_last_timestamp = interactions_sorted[-2]['timestamp']
        delta_t_ms = last_timestamp - second_last_timestamp
        delta_t_minutes = max(0, delta_t_ms / (1000 * 60))
        
        # 计算forgetting score
        forgetting_score = calculate_forgetting_score(s_tc, delta_t_minutes, tau)
        
        # 计算时间因子（用于分析）
        time_factor = delta_t_minutes / (delta_t_minutes + tau) if delta_t_minutes > 0 else 0
        
        results.append({
            'concept_id': cid,
            'total_attempts': len(interactions),
            'historical_accuracy': s_tc,
            'last_response': interactions_sorted[-1]['response'],
            'delta_t_minutes': delta_t_minutes,
            'delta_t_hours': delta_t_minutes / 60,
            'delta_t_days': delta_t_minutes / (60 * 24),
            'time_factor': time_factor,
            'forgetting_score': forgetting_score,
        })
    
    if len(results) == 0:
        return None
    
    # 统计信息
    fs_values = [r['forgetting_score'] for r in results]
    
    return {
        'uid': student_row['uid'],
        'concept_results': results,
        'fs_mean': np.mean(fs_values),
        'fs_std': np.std(fs_values),
        'fs_min': np.min(fs_values),
        'fs_max': np.max(fs_values),
    }

# 加载数据
df = pd.read_csv(DATA_PATH)

# 选择学生
qualified_students = []
for uid in df['uid'].unique():
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student_with_optimal_tau(student_row, TAU_MINUTES)
    if analysis and len(analysis['concept_results']) >= 5:
        qualified_students.append(uid)

selected_students = random.sample(qualified_students, min(5, len(qualified_students)))

print(f"\n选择5个学生进行分析:")
for i, uid in enumerate(selected_students, 1):
    print(f"  {i}. 学生ID: {uid}")

# 分析学生
print("\n" + "="*100)
print("详细分析结果 (τ = 3天)")
print("="*100)

all_results_for_csv = []

for idx, uid in enumerate(selected_students, 1):
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student_with_optimal_tau(student_row, TAU_MINUTES)
    
    if not analysis:
        continue
    
    print(f"\n{'='*100}")
    print(f"学生 #{idx}: ID {uid}")
    print(f"{'='*100}")
    
    print(f"\nForgetting Score统计:")
    print(f"  - 平均: {analysis['fs_mean']:.4f}")
    print(f"  - 标准差: {analysis['fs_std']:.4f}")
    print(f"  - 范围: [{analysis['fs_min']:.4f}, {analysis['fs_max']:.4f}]")
    
    results = analysis['concept_results']
    results_sorted = sorted(results, key=lambda x: x['forgetting_score'], reverse=True)
    
    print(f"\n所有Concepts详情:")
    print(f"{'-'*100}")
    print(f"{'Concept':<10} {'次数':<6} {'历史准确率':<12} {'答题间隔':<15} "
          f"{'时间因子':<12} {'FS':<12} {'最后':<6} {'分类':<10}")
    print(f"{'-'*100}")
    
    for result in results_sorted:
        cid = result['concept_id']
        attempts = result['total_attempts']
        hist_acc = result['historical_accuracy'] * 100
        
        # 时间间隔显示
        if result['delta_t_days'] >= 1:
            interval_str = f"{result['delta_t_days']:.1f}d"
        elif result['delta_t_hours'] >= 1:
            interval_str = f"{result['delta_t_hours']:.1f}h"
        else:
            interval_str = f"{result['delta_t_minutes']:.1f}m"
        
        time_factor = result['time_factor']
        fs = result['forgetting_score']
        last_resp = "✅" if result['last_response'] == 1 else "❌"
        
        # 分类
        if fs >= 0.3:
            category = "🔴 紧急"
        elif fs >= 0.2:
            category = "🟠 重要"
        elif fs >= 0.1:
            category = "🟡 一般"
        else:
            category = "🟢 维持"
        
        print(f"{cid:<10} {attempts:<6} {hist_acc:<11.1f}% {interval_str:<15} "
              f"{time_factor:<12.4f} {fs:<12.4f} {last_resp:<6} {category:<10}")
        
        # 保存用于CSV
        all_results_for_csv.append({
            'student_id': uid,
            'concept_id': cid,
            'attempts': attempts,
            'historical_accuracy': hist_acc,
            'interval_days': result['delta_t_days'],
            'time_factor': time_factor,
            'forgetting_score': fs,
            'last_correct': result['last_response'],
            'category': category
        })
    
    # 分析时间因子和掌握程度的贡献
    print(f"\n关键洞察 - FS差异的来源:")
    print(f"{'-'*100}")
    
    # 按间隔分组
    very_short = [r for r in results if r['delta_t_hours'] < 1]
    short = [r for r in results if 1 <= r['delta_t_hours'] < 24]
    medium = [r for r in results if 1 <= r['delta_t_days'] < 7]
    long = [r for r in results if r['delta_t_days'] >= 7]
    
    print(f"  时间间隔分布:")
    if very_short:
        print(f"    - 极短 (<1小时): {len(very_short)}个, 平均时间因子={np.mean([r['time_factor'] for r in very_short]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in very_short]):.4f}")
    if short:
        print(f"    - 短 (1-24小时): {len(short)}个, 平均时间因子={np.mean([r['time_factor'] for r in short]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in short]):.4f}")
    if medium:
        print(f"    - 中 (1-7天): {len(medium)}个, 平均时间因子={np.mean([r['time_factor'] for r in medium]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in medium]):.4f}")
    if long:
        print(f"    - 长 (≥7天): {len(long)}个, 平均时间因子={np.mean([r['time_factor'] for r in long]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in long]):.4f}")
    
    # 按掌握程度分组
    print(f"\n  掌握程度影响:")
    high_mastery = [r for r in results if r['historical_accuracy'] >= 0.7]
    low_mastery = [r for r in results if r['historical_accuracy'] <= 0.3]
    
    if high_mastery:
        print(f"    - 掌握好 (≥70%): {len(high_mastery)}个, 平均(1-s)={1-np.mean([r['historical_accuracy'] for r in high_mastery]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in high_mastery]):.4f}")
    if low_mastery:
        print(f"    - 掌握差 (≤30%): {len(low_mastery)}个, 平均(1-s)={1-np.mean([r['historical_accuracy'] for r in low_mastery]):.4f}, 平均FS={np.mean([r['forgetting_score'] for r in low_mastery]):.4f}")

# 保存结果
output_csv = '/mnt/localssd/forgetting_scores_optimal_tau.csv'
df_output = pd.DataFrame(all_results_for_csv)
df_output.to_csv(output_csv, index=False)

print("\n" + "="*100)
print("总结：使用优化τ值的效果")
print("="*100)

print(f"""
✅ 使用 τ = {TAU_DAYS:.2f}天 (平均答题间隔) 的优势：

1. 【时间因子合理分布】
   - 极短间隔 (<1小时): 时间因子 ≈ 0.0-0.01 (几乎不考虑遗忘)
   - 短间隔 (1-24小时): 时间因子 ≈ 0.01-0.25 (轻微遗忘)
   - 中间隔 (1-7天): 时间因子 ≈ 0.25-0.70 (中等遗忘)
   - 长间隔 (≥7天): 时间因子 ≈ 0.70-0.98 (严重遗忘)

2. 【FS差异更显著】
   - 同样掌握程度下，长间隔的FS明显高于短间隔
   - 同样间隔下，掌握差的FS明显高于掌握好的

3. 【实际应用】
   适合回答以下问题：
   • 学生在不同间隔下复习同一concept，遗忘程度如何？
   • 哪些concepts需要更频繁的复习（间隔短但FS高）？
   • 哪些concepts可以间隔较长时间（掌握好，FS低）？

4. 【与实际遗忘的对比】
   可以验证：高FS的concepts，最后一次答题是否真的答错了？
   （见输出中的"最后"列：✅=答对，❌=答错）

💡 关键insight：
  FS = (1 - s_{{t,c}}) × 时间因子
        ↑              ↑
    掌握程度        答题间隔
    
  两个因素共同决定遗忘风险！

详细结果已保存至: {output_csv}
""")

print("="*100)
print("✅ 分析完成！")
print("="*100)

