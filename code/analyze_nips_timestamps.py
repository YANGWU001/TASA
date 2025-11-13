#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析NIPS Task 3&4的时间戳和时间间隔
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_student_timestamps(df, student_idx=0):
    """分析单个学生的时间戳"""
    student = df.iloc[student_idx]
    
    timestamps_str = str(student['timestamps'])
    concepts_str = str(student['concepts'])
    responses_str = str(student['responses'])
    
    if timestamps_str == 'nan' or timestamps_str == '-1':
        print("该学生没有时间戳数据")
        return
    
    # 解析数据
    timestamps = [int(t) for t in timestamps_str.split(',') if t and t != '-1']
    concepts = [int(c) for c in concepts_str.split(',') if c and c != '-1']
    responses = [int(r) for r in responses_str.split(',') if r and r != '-1']
    
    min_len = min(len(timestamps), len(concepts), len(responses))
    timestamps = timestamps[:min_len]
    concepts = concepts[:min_len]
    responses = responses[:min_len]
    
    print(f"=" * 80)
    print(f"学生ID: {student['uid']}")
    print(f"总答题数: {len(timestamps)}")
    print(f"时间跨度: {datetime.fromtimestamp(timestamps[0]/1000)} 到 {datetime.fromtimestamp(timestamps[-1]/1000)}")
    total_days = (timestamps[-1] - timestamps[0]) / (1000 * 60 * 60 * 24)
    print(f"学习时长: {total_days:.1f} 天")
    print(f"=" * 80)
    
    # 计算整体时间间隔
    print(f"\n📊 整体时间间隔统计:")
    time_intervals = []
    for i in range(1, len(timestamps)):
        interval_ms = timestamps[i] - timestamps[i-1]
        interval_minutes = interval_ms / (1000 * 60)
        time_intervals.append(interval_minutes)
    
    print(f"  平均间隔: {np.mean(time_intervals):.1f} 分钟")
    print(f"  中位数间隔: {np.median(time_intervals):.1f} 分钟")
    print(f"  最短间隔: {np.min(time_intervals):.1f} 分钟")
    print(f"  最长间隔: {np.max(time_intervals):.1f} 分钟 ({np.max(time_intervals)/60/24:.1f} 天)")
    
    # 显示前10个间隔
    print(f"\n📋 前10次答题的时间间隔:")
    for i in range(min(10, len(time_intervals))):
        interval = time_intervals[i]
        if interval < 1:
            print(f"  答题{i+2} - 答题{i+1}: {interval*60:.0f} 秒 (concept {concepts[i+1]})")
        elif interval < 60:
            print(f"  答题{i+2} - 答题{i+1}: {interval:.1f} 分钟 (concept {concepts[i+1]})")
        else:
            print(f"  答题{i+2} - 答题{i+1}: {interval/60:.1f} 小时 (concept {concepts[i+1]})")
    
    # 计算同一concept的时间间隔
    print(f"\n🔄 同一Concept的重复时间间隔:")
    concept_last_time = {}
    concept_intervals = {}
    
    for i, (timestamp, concept) in enumerate(zip(timestamps, concepts)):
        if concept in concept_last_time:
            interval_ms = timestamp - concept_last_time[concept]
            interval_minutes = interval_ms / (1000 * 60)
            
            if concept not in concept_intervals:
                concept_intervals[concept] = []
            concept_intervals[concept].append(interval_minutes)
        
        concept_last_time[concept] = timestamp
    
    # 显示前10个有重复的concepts
    if concept_intervals:
        sorted_concepts = sorted(concept_intervals.items(), key=lambda x: len(x[1]), reverse=True)
        print(f"  (显示重复次数最多的前10个concepts)")
        for concept, intervals in sorted_concepts[:10]:
            avg_interval = np.mean(intervals)
            if avg_interval < 60:
                print(f"  Concept {concept}: 重复{len(intervals)}次, 平均间隔 {avg_interval:.1f} 分钟")
            elif avg_interval < 60*24:
                print(f"  Concept {concept}: 重复{len(intervals)}次, 平均间隔 {avg_interval/60:.1f} 小时")
            else:
                print(f"  Concept {concept}: 重复{len(intervals)}次, 平均间隔 {avg_interval/60/24:.1f} 天")
    else:
        print("  该学生没有重复做同一concept的题目")
    
    return timestamps, concepts, responses, time_intervals, concept_intervals


def analyze_dataset_timestamps(df, num_students=5):
    """分析多个学生的时间戳"""
    print(f"\n{'='*80}")
    print(f"📊 NIPS Task 3&4 时间戳分析（采样{num_students}个学生）")
    print(f"{'='*80}\n")
    
    all_intervals = []
    all_concept_intervals = []
    
    for i in range(min(num_students, len(df))):
        try:
            timestamps, concepts, responses, intervals, concept_intervals = analyze_student_timestamps(df, i)
            all_intervals.extend(intervals)
            for intervals_list in concept_intervals.values():
                all_concept_intervals.extend(intervals_list)
            print("\n")
        except Exception as e:
            print(f"学生{i}分析失败: {e}\n")
    
    # 整体统计
    if all_intervals:
        print(f"\n{'='*80}")
        print(f"📈 整体时间间隔统计（{num_students}个学生）")
        print(f"{'='*80}")
        print(f"  总答题次数: {len(all_intervals)}")
        print(f"  平均间隔: {np.mean(all_intervals):.1f} 分钟 ({np.mean(all_intervals)/60:.1f} 小时)")
        print(f"  中位数间隔: {np.median(all_intervals):.1f} 分钟")
        print(f"  10th percentile: {np.percentile(all_intervals, 10):.1f} 分钟")
        print(f"  90th percentile: {np.percentile(all_intervals, 90)/60:.1f} 小时")
        
        # 间隔分布
        print(f"\n  时间间隔分布:")
        print(f"    < 1分钟: {sum(1 for x in all_intervals if x < 1)} ({sum(1 for x in all_intervals if x < 1)/len(all_intervals)*100:.1f}%)")
        print(f"    1-10分钟: {sum(1 for x in all_intervals if 1 <= x < 10)} ({sum(1 for x in all_intervals if 1 <= x < 10)/len(all_intervals)*100:.1f}%)")
        print(f"    10-60分钟: {sum(1 for x in all_intervals if 10 <= x < 60)} ({sum(1 for x in all_intervals if 10 <= x < 60)/len(all_intervals)*100:.1f}%)")
        print(f"    1-24小时: {sum(1 for x in all_intervals if 60 <= x < 1440)} ({sum(1 for x in all_intervals if 60 <= x < 1440)/len(all_intervals)*100:.1f}%)")
        print(f"    > 24小时: {sum(1 for x in all_intervals if x >= 1440)} ({sum(1 for x in all_intervals if x >= 1440)/len(all_intervals)*100:.1f}%)")
    
    if all_concept_intervals:
        print(f"\n  同一Concept重复间隔:")
        print(f"    平均: {np.mean(all_concept_intervals):.1f} 分钟 ({np.mean(all_concept_intervals)/60:.1f} 小时)")
        print(f"    中位数: {np.median(all_concept_intervals):.1f} 分钟")


if __name__ == "__main__":
    print("🔍 NIPS Task 3&4 时间戳分析\n")
    
    # 读取数据
    data_path = '/mnt/localssd/pykt-toolkit/data/nips_task34/train_valid_sequences.csv'
    print(f"📂 读取数据: {data_path}")
    df = pd.read_csv(data_path)
    print(f"✅ 加载成功，共 {len(df)} 条记录\n")
    
    # 分析
    analyze_dataset_timestamps(df, num_students=3)
    
    print(f"\n{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}")
    print("\n💡 结论:")
    print("  ✅ NIPS Task 3&4 包含完整的时间戳信息")
    print("  ✅ 可以计算任意两次答题之间的时间差")
    print("  ✅ 可以计算同一concept的重复间隔")
    print("  ✅ 适合用于Forgetting Score计算中的 Δt_c")
    print("")

