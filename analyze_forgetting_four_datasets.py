#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
在四个数据集上分析Forgetting Score
使用实际答题间隔（最后一次 - 倒数第二次）
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random
import os

# 设置随机种子
random.seed(42)
np.random.seed(42)

# 数据集配置
DATASETS = {
    'assist2017': {
        'path': '/mnt/localssd/pykt-toolkit/data/assist2017/test_sequences.csv',
        'name': 'ASSISTments2017'
    },
    'ednet': {
        'path': '/mnt/localssd/pykt-toolkit/data/ednet/test_sequences.csv',
        'name': 'EdNet'
    },
    'algebra2005': {
        'path': '/mnt/localssd/pykt-toolkit/data/algebra2005/test_sequences.csv',
        'name': 'Algebra2005'
    },
    'bridge2006': {
        'path': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/test_sequences.csv',
        'name': 'Bridge2Algebra2006'
    }
}

print("="*120)
print("四个数据集的Forgetting Score分析")
print("使用实际答题间隔: Δt_c = 最后一次答题时间 - 倒数第二次答题时间")
print("="*120)

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

def analyze_interval_distribution(df):
    """分析数据集的答题间隔分布"""
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
    
    return np.array(all_intervals)

def analyze_student_with_tau(student_row, tau):
    """使用指定τ值分析学生"""
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
        
        # 计算时间因子
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

# 处理每个数据集
for dataset_key, dataset_info in DATASETS.items():
    print(f"\n{'='*120}")
    print(f"数据集: {dataset_info['name']}")
    print(f"{'='*120}")
    
    # 检查文件是否存在
    if not os.path.exists(dataset_info['path']):
        print(f"❌ 数据文件不存在: {dataset_info['path']}")
        continue
    
    # 加载数据
    df = pd.read_csv(dataset_info['path'])
    print(f"\n加载数据: {len(df)} 个学生")
    
    # 第1步：分析间隔分布
    print(f"\n第1步：分析答题间隔分布")
    print("-"*120)
    
    all_intervals = analyze_interval_distribution(df)
    
    if len(all_intervals) == 0:
        print(f"❌ 未找到足够的答题间隔数据")
        continue
    
    print(f"✅ 共收集到 {len(all_intervals):,} 个实际答题间隔")
    print(f"\n间隔统计:")
    print(f"  平均值: {np.mean(all_intervals):.2f} 分钟 = {np.mean(all_intervals)/60:.2f} 小时 = {np.mean(all_intervals)/(60*24):.2f} 天")
    print(f"  中位数: {np.median(all_intervals):.2f} 分钟 = {np.median(all_intervals)/60:.2f} 小时 = {np.median(all_intervals)/(60*24):.2f} 天")
    print(f"  标准差: {np.std(all_intervals):.2f} 分钟 = {np.std(all_intervals)/(60*24):.2f} 天")
    print(f"  25分位: {np.percentile(all_intervals, 25):.2f} 分钟 = {np.percentile(all_intervals, 25)/60:.2f} 小时")
    print(f"  75分位: {np.percentile(all_intervals, 75):.2f} 分钟 = {np.percentile(all_intervals, 75)/60:.2f} 小时")
    print(f"  90分位: {np.percentile(all_intervals, 90):.2f} 分钟 = {np.percentile(all_intervals, 90)/(60*24):.2f} 天")
    
    # 第2步：选择τ值
    print(f"\n第2步：选择合适的τ值")
    print("-"*120)
    
    # 使用平均值作为τ
    tau_selected = np.mean(all_intervals)
    tau_days = tau_selected / (60 * 24)
    
    print(f"✅ 选择 τ = {tau_selected:.2f} 分钟 = {tau_selected/60:.2f} 小时 = {tau_days:.2f} 天 (平均答题间隔)")
    print(f"   在平均间隔下，时间因子 ≈ 0.5，对遗忘的敏感度适中")
    
    # 显示不同间隔下的时间因子
    print(f"\n时间因子示例:")
    intervals_examples = [
        ("1分钟", 1),
        ("10分钟", 10),
        ("1小时", 60),
        ("6小时", 360),
        ("1天", 1440),
        ("3天", 4320),
        ("7天", 10080),
        ("30天", 43200),
    ]
    for name, interval_min in intervals_examples:
        time_factor = interval_min / (interval_min + tau_selected)
        print(f"  {name:>8}: 时间因子 = {time_factor:.4f}")
    
    # 第3步：选择学生并分析
    print(f"\n第3步：选择5个学生进行详细分析")
    print("-"*120)
    
    # 筛选有足够交互的学生
    qualified_students = []
    for uid in df['uid'].unique():
        student_row = df[df['uid'] == uid].iloc[0]
        analysis = analyze_student_with_tau(student_row, tau_selected)
        if analysis and len(analysis['concept_results']) >= 5:
            qualified_students.append(uid)
    
    print(f"✅ 共有 {len(qualified_students)} 个学生满足条件 (≥5个concepts，每个≥2次交互)")
    
    if len(qualified_students) == 0:
        print(f"❌ 未找到符合条件的学生")
        continue
    
    # 随机选择5个学生
    selected_students = random.sample(qualified_students, min(5, len(qualified_students)))
    print(f"✅ 随机选择 {len(selected_students)} 个学生:")
    for i, uid in enumerate(selected_students, 1):
        print(f"   {i}. 学生ID: {uid}")
    
    # 第4步：详细分析每个学生
    print(f"\n第4步：详细分析结果")
    print("="*120)
    
    for idx, uid in enumerate(selected_students, 1):
        student_row = df[df['uid'] == uid].iloc[0]
        analysis = analyze_student_with_tau(student_row, tau_selected)
        
        if not analysis:
            continue
        
        print(f"\n{'-'*120}")
        print(f"学生 #{idx}: ID {uid}")
        print(f"{'-'*120}")
        
        print(f"\nForgetting Score统计:")
        print(f"  平均值: {analysis['fs_mean']:.4f}")
        print(f"  标准差: {analysis['fs_std']:.4f}")
        print(f"  范围: [{analysis['fs_min']:.4f}, {analysis['fs_max']:.4f}]")
        
        results = analysis['concept_results']
        results_sorted = sorted(results, key=lambda x: x['forgetting_score'], reverse=True)
        
        # 显示前10个最高FS的concepts
        print(f"\n前10个最需要复习的Concepts (Forgetting Score最高):")
        print(f"  {'Concept':<10} {'次数':<6} {'历史准确率':<12} {'间隔':<12} {'时间因子':<12} {'FS':<12} {'最后':<6} {'分类':<10}")
        print(f"  {'-'*108}")
        
        for result in results_sorted[:10]:
            cid = result['concept_id']
            attempts = result['total_attempts']
            hist_acc = result['historical_accuracy'] * 100
            
            # 间隔显示
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
            
            print(f"  {cid:<10} {attempts:<6} {hist_acc:<11.1f}% {interval_str:<12} "
                  f"{time_factor:<12.4f} {fs:<12.4f} {last_resp:<6} {category:<10}")
        
        # 关键洞察
        print(f"\n  关键洞察:")
        
        # 按间隔分组
        very_short = [r for r in results if r['delta_t_hours'] < 1]
        short = [r for r in results if 1 <= r['delta_t_hours'] < 24]
        medium = [r for r in results if 1 <= r['delta_t_days'] < 7]
        long = [r for r in results if r['delta_t_days'] >= 7]
        
        if very_short:
            print(f"    极短间隔 (<1小时): {len(very_short)}个concepts, "
                  f"平均时间因子={np.mean([r['time_factor'] for r in very_short]):.4f}, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in very_short]):.4f}")
        if short:
            print(f"    短间隔 (1-24小时): {len(short)}个concepts, "
                  f"平均时间因子={np.mean([r['time_factor'] for r in short]):.4f}, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in short]):.4f}")
        if medium:
            print(f"    中间隔 (1-7天): {len(medium)}个concepts, "
                  f"平均时间因子={np.mean([r['time_factor'] for r in medium]):.4f}, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in medium]):.4f}")
        if long:
            print(f"    长间隔 (≥7天): {len(long)}个concepts, "
                  f"平均时间因子={np.mean([r['time_factor'] for r in long]):.4f}, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in long]):.4f}")
        
        # 按掌握程度分组
        high_mastery = [r for r in results if r['historical_accuracy'] >= 0.7]
        low_mastery = [r for r in results if r['historical_accuracy'] <= 0.3]
        
        if high_mastery:
            print(f"    掌握好 (≥70%): {len(high_mastery)}个concepts, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in high_mastery]):.4f}")
        if low_mastery:
            print(f"    掌握差 (≤30%): {len(low_mastery)}个concepts, "
                  f"平均FS={np.mean([r['forgetting_score'] for r in low_mastery]):.4f}")

print("\n" + "="*120)
print("汇总：四个数据集的τ值选择")
print("="*120)

# 重新加载并显示汇总
summary_data = []
for dataset_key, dataset_info in DATASETS.items():
    if not os.path.exists(dataset_info['path']):
        continue
    
    df = pd.read_csv(dataset_info['path'])
    all_intervals = analyze_interval_distribution(df)
    
    if len(all_intervals) > 0:
        tau = np.mean(all_intervals)
        summary_data.append({
            'dataset': dataset_info['name'],
            'tau_minutes': tau,
            'tau_hours': tau / 60,
            'tau_days': tau / (60 * 24),
            'median_minutes': np.median(all_intervals),
            'median_days': np.median(all_intervals) / (60 * 24),
        })

print(f"\n{'数据集':<25} {'τ值(平均间隔)':<25} {'中位数间隔':<25}")
print("-"*120)
for item in summary_data:
    tau_str = f"{item['tau_minutes']:.0f}m = {item['tau_hours']:.1f}h = {item['tau_days']:.2f}d"
    median_str = f"{item['median_minutes']:.0f}m = {item['median_days']:.2f}d"
    print(f"{item['dataset']:<25} {tau_str:<25} {median_str:<25}")

print("\n" + "="*120)
print("✅ 四个数据集分析完成！")
print("="*120)

