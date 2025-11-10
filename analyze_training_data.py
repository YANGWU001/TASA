#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析训练数据的统计信息
"""

import pandas as pd
import numpy as np
import os
from collections import Counter

def analyze_dataset(dataset_name, data_path):
    """
    分析数据集的详细统计信息
    """
    print(f"\n{'='*80}")
    print(f"📊 数据集: {dataset_name.upper()}")
    print(f"{'='*80}")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}")
        return None
    
    # 读取数据
    print(f"📂 读取数据: {data_path}")
    df = pd.read_csv(data_path)
    
    stats = {}
    
    # 基本统计
    stats['total_records'] = len(df)
    stats['unique_students'] = df['uid'].nunique()
    
    # 按fold统计
    print(f"\n📋 Fold分布:")
    fold_counts = df['fold'].value_counts().sort_index()
    for fold, count in fold_counts.items():
        print(f"  Fold {fold}: {count:,} 条记录")
        stats[f'fold_{fold}_records'] = count
    
    # 统计每个学生的信息
    print(f"\n👥 学生统计:")
    print(f"  总学生数: {stats['unique_students']:,}")
    
    # 解析每个学生的详细信息
    total_interactions = 0
    total_questions = 0
    total_concepts = 0
    sequence_lengths = []
    response_correct = []
    timestamps_list = []
    all_concepts = set()
    all_questions = set()
    
    print(f"\n⏳ 正在解析学生数据...")
    
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  处理进度: {idx}/{len(df)} ({idx/len(df)*100:.1f}%)")
        
        # 解析concepts
        concepts_str = str(row['concepts'])
        if concepts_str != 'NA' and concepts_str != 'nan':
            concepts = [int(c) for c in concepts_str.split(',') if c and c != '-1']
            sequence_lengths.append(len(concepts))
            total_interactions += len(concepts)
            all_concepts.update(concepts)
        
        # 解析questions
        questions_str = str(row['questions'])
        if questions_str != 'NA' and questions_str != 'nan':
            questions = [int(q) for q in questions_str.split(',') if q and q != '-1']
            total_questions += len(questions)
            all_questions.update(questions)
        
        # 解析responses
        responses_str = str(row['responses'])
        if responses_str != 'NA' and responses_str != 'nan':
            responses = [int(r) for r in responses_str.split(',') if r and r != '-1']
            response_correct.extend(responses)
        
        # 解析timestamps
        timestamps_str = str(row['timestamps'])
        if timestamps_str != 'NA' and timestamps_str != 'nan':
            try:
                timestamps = [int(t) for t in timestamps_str.split(',') if t and t != '-1']
                timestamps_list.extend(timestamps)
            except:
                pass
    
    print(f"  处理完成: {len(df)}/{len(df)} (100.0%)")
    
    # 统计结果
    stats['total_interactions'] = total_interactions
    stats['unique_concepts'] = len(all_concepts)
    stats['unique_questions'] = len(all_questions)
    stats['avg_sequence_length'] = np.mean(sequence_lengths) if sequence_lengths else 0
    stats['median_sequence_length'] = np.median(sequence_lengths) if sequence_lengths else 0
    stats['min_sequence_length'] = np.min(sequence_lengths) if sequence_lengths else 0
    stats['max_sequence_length'] = np.max(sequence_lengths) if sequence_lengths else 0
    stats['std_sequence_length'] = np.std(sequence_lengths) if sequence_lengths else 0
    
    # 正确率统计
    if response_correct:
        stats['overall_accuracy'] = np.mean(response_correct)
        stats['total_correct'] = sum(response_correct)
        stats['total_incorrect'] = len(response_correct) - sum(response_correct)
    
    # 时间跨度统计
    if timestamps_list:
        timestamps_array = np.array(timestamps_list)
        stats['earliest_timestamp'] = int(np.min(timestamps_array))
        stats['latest_timestamp'] = int(np.max(timestamps_array))
        time_span_days = (stats['latest_timestamp'] - stats['earliest_timestamp']) / 1000 / 60 / 60 / 24
        stats['time_span_days'] = time_span_days
    
    # 打印详细统计
    print(f"\n📈 详细统计:")
    print(f"\n  🔢 数量统计:")
    print(f"    - 总学生数: {stats['unique_students']:,}")
    print(f"    - 总交互数: {stats['total_interactions']:,}")
    print(f"    - 唯一Concepts: {stats['unique_concepts']:,}")
    print(f"    - 唯一Questions: {stats['unique_questions']:,}")
    print(f"    - 平均每个学生交互数: {stats['total_interactions']/stats['unique_students']:.1f}")
    
    print(f"\n  📏 序列长度统计:")
    print(f"    - 平均长度: {stats['avg_sequence_length']:.1f}")
    print(f"    - 中位数长度: {stats['median_sequence_length']:.1f}")
    print(f"    - 最小长度: {stats['min_sequence_length']}")
    print(f"    - 最大长度: {stats['max_sequence_length']}")
    print(f"    - 标准差: {stats['std_sequence_length']:.1f}")
    
    if 'overall_accuracy' in stats:
        print(f"\n  ✅ 正确率统计:")
        print(f"    - 总体正确率: {stats['overall_accuracy']*100:.2f}%")
        print(f"    - 正确答题数: {stats['total_correct']:,}")
        print(f"    - 错误答题数: {stats['total_incorrect']:,}")
    
    if 'time_span_days' in stats:
        print(f"\n  ⏱️  时间跨度:")
        print(f"    - 最早时间: {pd.to_datetime(stats['earliest_timestamp'], unit='ms')}")
        print(f"    - 最晚时间: {pd.to_datetime(stats['latest_timestamp'], unit='ms')}")
        print(f"    - 时间跨度: {stats['time_span_days']:.1f} 天")
    
    # 序列长度分布
    print(f"\n  📊 序列长度分布:")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        value = np.percentile(sequence_lengths, p) if sequence_lengths else 0
        print(f"    - {p}th percentile: {value:.0f}")
    
    # Concept频率统计（Top 10）
    if response_correct:
        print(f"\n  🔝 最常见的10个Concepts:")
        concept_counter = Counter()
        for idx, row in df.iterrows():
            concepts_str = str(row['concepts'])
            if concepts_str != 'NA' and concepts_str != 'nan':
                concepts = [int(c) for c in concepts_str.split(',') if c and c != '-1']
                concept_counter.update(concepts)
        
        for concept, count in concept_counter.most_common(10):
            percentage = count / stats['total_interactions'] * 100
            print(f"    - Concept {concept}: {count:,} 次 ({percentage:.2f}%)")
    
    return stats


def compare_datasets(stats_dict):
    """
    对比多个数据集的统计信息
    """
    print(f"\n{'='*80}")
    print(f"📊 数据集对比")
    print(f"{'='*80}\n")
    
    comparison_df = pd.DataFrame(stats_dict).T
    
    # 选择关键指标进行对比
    key_metrics = [
        'unique_students',
        'total_interactions',
        'unique_concepts',
        'unique_questions',
        'avg_sequence_length',
        'overall_accuracy',
        'time_span_days'
    ]
    
    print("📋 关键指标对比:")
    print("-" * 80)
    
    for metric in key_metrics:
        if metric in comparison_df.columns:
            print(f"\n{metric}:")
            for dataset in comparison_df.index:
                value = comparison_df.loc[dataset, metric]
                if isinstance(value, float):
                    if 'accuracy' in metric:
                        print(f"  {dataset:15s}: {value*100:10.2f}%")
                    else:
                        print(f"  {dataset:15s}: {value:10.1f}")
                else:
                    print(f"  {dataset:15s}: {value:10,}")
    
    return comparison_df


if __name__ == "__main__":
    print("🔍 训练数据统计分析")
    print("=" * 80)
    
    datasets = {
        'EdNet': '/mnt/localssd/pykt-toolkit/data/ednet/train_valid_sequences.csv',
        'ASSISTments2017': '/mnt/localssd/pykt-toolkit/data/assist2017/train_valid_sequences.csv'
    }
    
    stats_dict = {}
    
    for dataset_name, data_path in datasets.items():
        stats = analyze_dataset(dataset_name, data_path)
        if stats:
            stats_dict[dataset_name] = stats
    
    # 对比数据集
    if len(stats_dict) > 1:
        comparison_df = compare_datasets(stats_dict)
        
        # 保存对比结果
        output_path = "/tmp/dataset_comparison.csv"
        comparison_df.to_csv(output_path)
        print(f"\n✅ 对比结果已保存: {output_path}")
    
    print(f"\n{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}")

