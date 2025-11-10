#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用实际的答题间隔计算Forgetting Score
Δt_c = 最后一次答题时间 - 倒数第二次答题时间
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

print("="*100)
print(f"使用实际答题间隔计算Forgetting Score")
print(f"数据集: {DATASET.upper()}")
print(f"Δt_c = 最后一次答题时间 - 倒数第二次答题时间")
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

# 第1步：分析实际时间间隔分布
print("\n第1步：分析数据集中实际的答题时间间隔分布")
print("-"*100)

df = pd.read_csv(DATA_PATH)
all_intervals = []

for _, row in df.iterrows():
    timestamps = parse_field(row['timestamps'])
    concepts = parse_field(row['concepts'])
    
    if len(timestamps) < 2:
        continue
    
    # 按concept分组
    concept_timestamps = defaultdict(list)
    for i, cid in enumerate(concepts):
        concept_timestamps[cid].append(timestamps[i])
    
    # 计算每个concept的最后两次间隔
    for cid, ts_list in concept_timestamps.items():
        if len(ts_list) >= 2:
            ts_list_sorted = sorted(ts_list)
            interval_ms = ts_list_sorted[-1] - ts_list_sorted[-2]
            interval_minutes = interval_ms / (1000 * 60)
            all_intervals.append(interval_minutes)

all_intervals = np.array(all_intervals)

print(f"✅ 共收集到 {len(all_intervals)} 个实际答题间隔")
print(f"\n时间间隔统计 (分钟):")
print(f"  - 平均值: {np.mean(all_intervals):.2f} 分钟 = {np.mean(all_intervals)/60:.2f} 小时 = {np.mean(all_intervals)/(60*24):.2f} 天")
print(f"  - 中位数: {np.median(all_intervals):.2f} 分钟 = {np.median(all_intervals)/60:.2f} 小时 = {np.median(all_intervals)/(60*24):.2f} 天")
print(f"  - 标准差: {np.std(all_intervals):.2f} 分钟 = {np.std(all_intervals)/(60*24):.2f} 天")
print(f"  - 最小值: {np.min(all_intervals):.2f} 分钟 = {np.min(all_intervals)/60:.2f} 小时")
print(f"  - 最大值: {np.max(all_intervals):.2f} 分钟 = {np.max(all_intervals)/(60*24):.2f} 天")
print(f"  - 25分位: {np.percentile(all_intervals, 25):.2f} 分钟 = {np.percentile(all_intervals, 25)/60:.2f} 小时")
print(f"  - 75分位: {np.percentile(all_intervals, 75):.2f} 分钟 = {np.percentile(all_intervals, 75)/60:.2f} 小时")
print(f"  - 90分位: {np.percentile(all_intervals, 90):.2f} 分钟 = {np.percentile(all_intervals, 90)/(60*24):.2f} 天")

# 第2步：选择合适的τ值
print("\n第2步：根据实际间隔分布选择合适的τ值")
print("-"*100)

# 推荐τ为中位数附近，这样时间因子在0.5左右
tau_options = {
    '中位数': np.median(all_intervals),
    '平均值': np.mean(all_intervals),
    '75分位数': np.percentile(all_intervals, 75),
    '1天 (1440分钟)': 1440,
    '12小时 (720分钟)': 720,
    '6小时 (360分钟)': 360,
}

print("不同τ值下的时间因子分布:")
print(f"{'τ选择':<20} {'τ值(分钟)':<15} {'τ值(天)':<12} {'中位间隔时的时间因子':<25} {'平均间隔时的时间因子':<25}")
print("-"*100)

for name, tau_val in tau_options.items():
    median_interval = np.median(all_intervals)
    mean_interval = np.mean(all_intervals)
    
    time_factor_median = median_interval / (median_interval + tau_val)
    time_factor_mean = mean_interval / (mean_interval + tau_val)
    
    print(f"{name:<20} {tau_val:<15.2f} {tau_val/(60*24):<12.2f} {time_factor_median:<25.4f} {time_factor_mean:<25.4f}")

# 选择中位数作为τ
tau_selected = np.median(all_intervals)
print(f"\n✅ 推荐选择: τ = {tau_selected:.2f} 分钟 = {tau_selected/60:.2f} 小时 = {tau_selected/(60*24):.2f} 天")
print(f"   理由: 这样在中位数间隔下，时间因子 ≈ 0.5，对遗忘的敏感度适中")

# 第3步：使用新的时间差计算forgetting score
print("\n第3步：使用实际答题间隔重新计算Forgetting Score")
print("="*100)

def analyze_student_with_actual_intervals(student_row, tau):
    """使用实际答题间隔分析学生"""
    questions = parse_field(student_row['questions'])
    concepts = parse_field(student_row['concepts'])
    responses = parse_field(student_row['responses'])
    timestamps = parse_field(student_row['timestamps'])
    
    if len(concepts) < 2:  # 需要至少2次交互才能计算间隔
        return None
    
    # 按concept分组，保留时间顺序
    concept_data = defaultdict(list)
    for i in range(len(concepts)):
        concept_data[concepts[i]].append({
            'index': i,
            'question': questions[i],
            'response': responses[i],
            'timestamp': timestamps[i]
        })
    
    # 计算每个concept的forgetting score
    results = []
    skipped_concepts = 0
    
    for cid, interactions in concept_data.items():
        if len(interactions) < 2:
            skipped_concepts += 1
            continue  # 只有1次交互，无法计算间隔
        
        # 按时间排序
        interactions_sorted = sorted(interactions, key=lambda x: x['timestamp'])
        
        # 计算历史正确率（使用倒数第二次之前的所有数据）
        historical_responses = [inter['response'] for inter in interactions_sorted[:-1]]
        s_tc = sum(historical_responses) / len(historical_responses)
        
        # 计算最后两次的时间间隔
        last_timestamp = interactions_sorted[-1]['timestamp']
        second_last_timestamp = interactions_sorted[-2]['timestamp']
        delta_t_ms = last_timestamp - second_last_timestamp
        delta_t_minutes = max(0, delta_t_ms / (1000 * 60))
        
        # 计算forgetting score
        forgetting_score = calculate_forgetting_score(s_tc, delta_t_minutes, tau)
        
        # 最后一次是否答对
        last_response = interactions_sorted[-1]['response']
        
        results.append({
            'concept_id': cid,
            'total_attempts': len(interactions),
            'historical_correct': sum(historical_responses),
            'historical_accuracy': s_tc,
            'last_response': last_response,
            'delta_t_minutes': delta_t_minutes,
            'delta_t_hours': delta_t_minutes / 60,
            'delta_t_days': delta_t_minutes / (60 * 24),
            'forgetting_score': forgetting_score,
        })
    
    if len(results) == 0:
        return None
    
    # 计算统计信息
    fs_values = [r['forgetting_score'] for r in results]
    acc_values = [r['historical_accuracy'] for r in results]
    intervals = [r['delta_t_minutes'] for r in results]
    
    diversity_stats = {
        'fs_mean': np.mean(fs_values),
        'fs_std': np.std(fs_values),
        'fs_min': np.min(fs_values),
        'fs_max': np.max(fs_values),
        'fs_range': np.max(fs_values) - np.min(fs_values),
        'acc_mean': np.mean(acc_values),
        'interval_mean_minutes': np.mean(intervals),
        'interval_std_minutes': np.std(intervals),
    }
    
    return {
        'uid': student_row['uid'],
        'total_interactions': len(concepts),
        'unique_concepts': len(concept_data),
        'concepts_with_2plus': len(results),
        'skipped_concepts': skipped_concepts,
        'overall_accuracy': sum(responses) / len(responses),
        'concept_results': results,
        'diversity_stats': diversity_stats
    }

# 选择有足够交互的学生
print("\n筛选条件：选择有5个以上concepts且每个concept至少2次交互的学生")
qualified_students = []

for uid in df['uid'].unique():
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student_with_actual_intervals(student_row, tau_selected)
    if analysis and analysis['concepts_with_2plus'] >= 5:
        qualified_students.append(uid)

print(f"✅ 共有 {len(qualified_students)} 个学生满足条件")

# 随机选择5个学生
selected_students = random.sample(qualified_students, min(5, len(qualified_students)))
print(f"✅ 随机选择5个学生进行详细分析:")
for i, uid in enumerate(selected_students, 1):
    print(f"   {i}. 学生ID: {uid}")

# 分析每个学生
print("\n" + "="*100)
print("第4步：详细分析结果")
print("="*100)

student_analyses = []
for uid in selected_students:
    student_row = df[df['uid'] == uid].iloc[0]
    analysis = analyze_student_with_actual_intervals(student_row, tau_selected)
    if analysis:
        student_analyses.append(analysis)

# 展示每个学生的结果
for idx, analysis in enumerate(student_analyses, 1):
    print(f"\n{'='*100}")
    print(f"学生 #{idx}: ID {analysis['uid']}")
    print(f"{'='*100}")
    
    div = analysis['diversity_stats']
    print(f"\n总体信息:")
    print(f"  - 总交互数: {analysis['total_interactions']}")
    print(f"  - 唯一concepts: {analysis['unique_concepts']}")
    print(f"  - 可计算FS的concepts: {analysis['concepts_with_2plus']} (需要≥2次交互)")
    print(f"  - 跳过的concepts: {analysis['skipped_concepts']} (只有1次交互)")
    print(f"  - 总体正确率: {analysis['overall_accuracy']*100:.1f}%")
    
    print(f"\n答题间隔统计:")
    print(f"  - 平均间隔: {div['interval_mean_minutes']/60:.2f} 小时 = {div['interval_mean_minutes']/(60*24):.2f} 天")
    print(f"  - 间隔标准差: {div['interval_std_minutes']/60:.2f} 小时")
    
    print(f"\nForgetting Score统计:")
    print(f"  - 平均值: {div['fs_mean']:.4f}")
    print(f"  - 标准差: {div['fs_std']:.4f}")
    print(f"  - 范围: [{div['fs_min']:.4f}, {div['fs_max']:.4f}]")
    print(f"  - 差值: {div['fs_range']:.4f}")
    
    results = analysis['concept_results']
    results_sorted = sorted(results, key=lambda x: x['forgetting_score'], reverse=True)
    
    print(f"\n前10个最需要复习的concepts (Forgetting Score最高):")
    print(f"{'-'*100}")
    print(f"{'Concept':<10} {'次数':<6} {'历史正确率':<12} {'最后答题':<10} "
          f"{'答题间隔':<18} {'FS':<12} {'分类':<10}")
    print(f"{'-'*100}")
    
    for result in results_sorted[:10]:
        cid = result['concept_id']
        attempts = result['total_attempts']
        hist_acc = result['historical_accuracy'] * 100
        last_resp = "✅" if result['last_response'] == 1 else "❌"
        interval_str = f"{result['delta_t_hours']:.1f}h"
        if result['delta_t_days'] >= 1:
            interval_str = f"{result['delta_t_days']:.1f}d"
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
        
        print(f"{cid:<10} {attempts:<6} {hist_acc:<11.1f}% {last_resp:<10} "
              f"{interval_str:<18} {fs:<12.4f} {category:<10}")
    
    # 分析：间隔时间和遗忘的关系
    print(f"\n关键洞察:")
    print(f"{'-'*100}")
    
    # 1. 短间隔 vs 长间隔
    short_interval = [r for r in results if r['delta_t_hours'] < 24]
    long_interval = [r for r in results if r['delta_t_hours'] >= 24]
    
    if short_interval:
        avg_fs_short = np.mean([r['forgetting_score'] for r in short_interval])
        print(f"  短间隔 (<24小时): {len(short_interval)}个concepts, 平均FS = {avg_fs_short:.4f}")
    
    if long_interval:
        avg_fs_long = np.mean([r['forgetting_score'] for r in long_interval])
        print(f"  长间隔 (≥24小时): {len(long_interval)}个concepts, 平均FS = {avg_fs_long:.4f}")
    
    # 2. 掌握好 vs 掌握差
    high_mastery = [r for r in results if r['historical_accuracy'] >= 0.7]
    low_mastery = [r for r in results if r['historical_accuracy'] <= 0.3]
    
    if high_mastery:
        avg_fs_high = np.mean([r['forgetting_score'] for r in high_mastery])
        print(f"  掌握良好 (正确率≥70%): {len(high_mastery)}个concepts, 平均FS = {avg_fs_high:.4f}")
    
    if low_mastery:
        avg_fs_low = np.mean([r['forgetting_score'] for r in low_mastery])
        print(f"  掌握较差 (正确率≤30%): {len(low_mastery)}个concepts, 平均FS = {avg_fs_low:.4f}")

# 第5步：跨学生对比
print("\n" + "="*100)
print("第5步：跨学生对比")
print("="*100)

print(f"\n{'学生ID':<12} {'Concepts':<10} {'平均间隔':<15} {'FS均值':<12} "
      f"{'FS标准差':<12} {'FS范围':<25}")
print("-"*100)

for analysis in student_analyses:
    uid = analysis['uid']
    n_concepts = analysis['concepts_with_2plus']
    div = analysis['diversity_stats']
    
    interval_str = f"{div['interval_mean_minutes']/60:.1f}h"
    if div['interval_mean_minutes'] >= 60*24:
        interval_str = f"{div['interval_mean_minutes']/(60*24):.1f}d"
    
    fs_range_str = f"[{div['fs_min']:.3f}, {div['fs_max']:.3f}]"
    
    print(f"{uid:<12} {n_concepts:<10} {interval_str:<15} {div['fs_mean']:<12.4f} "
          f"{div['fs_std']:<12.4f} {fs_range_str:<25}")

# 第6步：关键洞察
print("\n" + "="*100)
print("第6步：使用实际答题间隔的关键洞察")
print("="*100)

print(f"""
使用"最后一次和倒数第二次答题间隔"计算Forgetting Score的优势：

1. ✅ 反映真实学习节奏
   - 基于学生实际的答题间隔
   - 不需要假设"当前评估时间"
   - 更符合实际应用场景

2. ✅ τ值选择更合理
   - τ = {tau_selected/(60*24):.2f}天 (数据中位数)
   - 在中位数间隔下，时间因子 ≈ 0.5
   - 对遗忘的敏感度适中

3. ✅ 差异来源更清晰
   - 掌握程度差异 (s_{{t,c}}): 影响 (1 - s_{{t,c}})
   - 答题间隔差异 (Δt_c): 影响时间因子
   - 两个因素都直接来自数据

4. ✅ 可预测性更强
   - 可以预测：如果学生在下次答题前间隔X天，遗忘程度如何
   - 可用于推荐系统：建议学生在合适的时间间隔复习

5. ⚠️  注意事项
   - 需要每个concept至少2次交互
   - 最后一次答题结果可作为验证（实际遗忘与否）

推荐使用场景：
• 个性化学习间隔推荐 (Spaced Repetition)
• 预测学生在不同复习间隔下的表现
• 优化课程设计中的练习题间隔
""")

print("="*100)
print("✅ 分析完成！")
print("="*100)

