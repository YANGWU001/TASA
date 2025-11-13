#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整数据集分析报告
分析train_valid和test的详细统计信息
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from collections import Counter
from tqdm import tqdm

def analyze_dataset_split(dataset_name, data_path, split_name):
    """
    分析单个数据分割（train_valid或test）
    """
    print(f"\n{'='*80}")
    print(f"📊 {dataset_name} - {split_name}")
    print(f"{'='*80}")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}")
        return None
    
    print(f"📂 读取数据: {data_path}")
    
    try:
        df = pd.read_csv(data_path)
        
        # Fold distribution (only for train_valid)
        if split_name == "Train/Valid":
            print("\n📋 Fold分布:")
            print(df['fold'].value_counts().sort_index().to_string())
        
        # Student count
        unique_students = df['uid'].nunique()
        print(f"\n👥 学生统计:\n  总学生数: {unique_students:,}")
        
        all_interactions = []
        all_concepts = set()
        all_questions = set()
        all_responses = []
        all_timestamps = []
        sequence_lengths = []
        
        print("\n⏳ 正在解析学生数据...")
        total_rows = len(df)
        for i, row in tqdm(df.iterrows(), total=total_rows, desc="  处理进度"):
            concepts_str = str(row['concepts'])
            responses_str = str(row['responses'])
            timestamps_str = str(row['timestamps'])
            questions_str = str(row['questions'])
            
            if concepts_str == 'NA' or responses_str == 'NA' or timestamps_str == 'NA' or questions_str == 'NA':
                continue
            
            try:
                concepts = [int(c) for c in concepts_str.split(',') if c and c != '-1']
                responses = [int(r) for r in responses_str.split(',') if r and r != '-1']
                timestamps = [int(t) for t in timestamps_str.split(',') if t and t != '-1']
                questions = [int(q) for q in questions_str.split(',') if q and q != '-1']
                
                min_len = min(len(concepts), len(responses), len(timestamps), len(questions))
                if min_len == 0:
                    continue
                
                concepts = concepts[:min_len]
                responses = responses[:min_len]
                timestamps = timestamps[:min_len]
                questions = questions[:min_len]
                
                all_interactions.extend(responses)
                all_concepts.update(concepts)
                all_questions.update(questions)
                all_responses.extend(responses)
                all_timestamps.extend(timestamps)
                sequence_lengths.append(min_len)
            except (ValueError, IndexError) as e:
                continue
        
        total_interactions = len(all_interactions)
        overall_accuracy = np.mean(all_responses) if all_responses else 0
        total_correct = sum(all_responses)
        total_incorrect = total_interactions - total_correct
        
        earliest_timestamp = datetime.fromtimestamp(min(all_timestamps) / 1000) if all_timestamps else "N/A"
        latest_timestamp = datetime.fromtimestamp(max(all_timestamps) / 1000) if all_timestamps else "N/A"
        time_span_days = (max(all_timestamps) - min(all_timestamps)) / (1000 * 60 * 60 * 24) if all_timestamps else 0
        
        # Concept frequency
        concept_counts = Counter()
        for _, row in df.iterrows():
            concepts_str = str(row['concepts'])
            if concepts_str != 'NA':
                for c_str in concepts_str.split(','):
                    if c_str and c_str != '-1':
                        try:
                            concept_counts[int(c_str)] += 1
                        except ValueError:
                            continue
        
        top_10_concepts = concept_counts.most_common(10)
        
        print("\n📈 详细统计:\n")
        print("  🔢 数量统计:")
        print(f"    - 总学生数: {unique_students:,}")
        print(f"    - 总交互数: {total_interactions:,}")
        print(f"    - 唯一Concepts: {len(all_concepts):,}")
        print(f"    - 唯一Questions: {len(all_questions):,}")
        print(f"    - 平均每个学生交互数: {total_interactions / unique_students:.1f}")
        
        print("\n  📏 序列长度统计:")
        print(f"    - 平均长度: {np.mean(sequence_lengths):.1f}")
        print(f"    - 中位数长度: {np.median(sequence_lengths):.1f}")
        print(f"    - 最小长度: {min(sequence_lengths)}")
        print(f"    - 最大长度: {max(sequence_lengths)}")
        print(f"    - 标准差: {np.std(sequence_lengths):.1f}")
        
        print("\n  ✅ 正确率统计:")
        print(f"    - 总体正确率: {overall_accuracy:.2%}")
        print(f"    - 正确答题数: {total_correct:,}")
        print(f"    - 错误答题数: {total_incorrect:,}")
        
        print("\n  ⏱️  时间跨度:")
        print(f"    - 最早时间: {earliest_timestamp}")
        print(f"    - 最晚时间: {latest_timestamp}")
        print(f"    - 时间跨度: {time_span_days:.1f} 天")
        
        print("\n  📊 序列长度分布:")
        print(f"    - 10th percentile: {np.percentile(sequence_lengths, 10):.0f}")
        print(f"    - 25th percentile: {np.percentile(sequence_lengths, 25):.0f}")
        print(f"    - 50th percentile: {np.percentile(sequence_lengths, 50):.0f}")
        print(f"    - 75th percentile: {np.percentile(sequence_lengths, 75):.0f}")
        print(f"    - 90th percentile: {np.percentile(sequence_lengths, 90):.0f}")
        print(f"    - 95th percentile: {np.percentile(sequence_lengths, 95):.0f}")
        print(f"    - 99th percentile: {np.percentile(sequence_lengths, 99):.0f}")
        
        print("\n  🔝 最常见的10个Concepts:")
        for concept_id, count in top_10_concepts:
            print(f"    - Concept {concept_id}: {count:,} 次 ({count / total_interactions:.2%})")
        
        return {
            'dataset': dataset_name,
            'split': split_name,
            'total_records': len(df),
            'unique_students': unique_students,
            'total_interactions': total_interactions,
            'unique_concepts': len(all_concepts),
            'unique_questions': len(all_questions),
            'avg_interactions_per_student': total_interactions / unique_students if unique_students > 0 else 0,
            'avg_sequence_length': np.mean(sequence_lengths),
            'median_sequence_length': np.median(sequence_lengths),
            'min_sequence_length': min(sequence_lengths) if sequence_lengths else 0,
            'max_sequence_length': max(sequence_lengths) if sequence_lengths else 0,
            'std_sequence_length': np.std(sequence_lengths),
            'overall_accuracy': overall_accuracy,
            'total_correct': total_correct,
            'total_incorrect': total_incorrect,
            'earliest_timestamp': min(all_timestamps) if all_timestamps else None,
            'latest_timestamp': max(all_timestamps) if all_timestamps else None,
            'time_span_days': time_span_days,
            'p10_seq_len': np.percentile(sequence_lengths, 10) if sequence_lengths else 0,
            'p25_seq_len': np.percentile(sequence_lengths, 25) if sequence_lengths else 0,
            'p50_seq_len': np.percentile(sequence_lengths, 50) if sequence_lengths else 0,
            'p75_seq_len': np.percentile(sequence_lengths, 75) if sequence_lengths else 0,
            'p90_seq_len': np.percentile(sequence_lengths, 90) if sequence_lengths else 0,
            'p95_seq_len': np.percentile(sequence_lengths, 95) if sequence_lengths else 0,
            'p99_seq_len': np.percentile(sequence_lengths, 99) if sequence_lengths else 0,
        }
    except Exception as e:
        print(f"❌ 处理数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_complete_dataset(dataset_name, data_dir):
    """
    分析完整数据集（train_valid + test）
    """
    print(f"\n{'='*80}")
    print(f"🔍 完整数据集分析: {dataset_name.upper()}")
    print(f"{'='*80}")
    
    train_valid_path = os.path.join(data_dir, "train_valid_sequences.csv")
    test_path = os.path.join(data_dir, "test_sequences.csv")
    
    # 分析train_valid
    train_valid_stats = analyze_dataset_split(dataset_name, train_valid_path, "Train/Valid")
    
    # 分析test
    test_stats = analyze_dataset_split(dataset_name, test_path, "Test")
    
    # 汇总统计
    if train_valid_stats and test_stats:
        print(f"\n{'='*80}")
        print(f"📊 {dataset_name} - 整体汇总")
        print(f"{'='*80}\n")
        
        total_students = train_valid_stats['unique_students'] + test_stats['unique_students']
        total_interactions = train_valid_stats['total_interactions'] + test_stats['total_interactions']
        
        # 合并concepts和questions (需要重新读取以获取准确的唯一值)
        print("⏳ 计算整体唯一Concepts和Questions...")
        df_train_valid = pd.read_csv(train_valid_path)
        df_test = pd.read_csv(test_path)
        
        all_concepts_combined = set()
        all_questions_combined = set()
        
        for df in [df_train_valid, df_test]:
            for _, row in df.iterrows():
                concepts_str = str(row['concepts'])
                questions_str = str(row['questions'])
                
                if concepts_str != 'NA':
                    for c_str in concepts_str.split(','):
                        if c_str and c_str != '-1':
                            try:
                                all_concepts_combined.add(int(c_str))
                            except ValueError:
                                continue
                
                if questions_str != 'NA':
                    for q_str in questions_str.split(','):
                        if q_str and q_str != '-1':
                            try:
                                all_questions_combined.add(int(q_str))
                            except ValueError:
                                continue
        
        total_correct = train_valid_stats['total_correct'] + test_stats['total_correct']
        overall_accuracy = total_correct / total_interactions if total_interactions > 0 else 0
        
        earliest_ts = min(train_valid_stats['earliest_timestamp'], test_stats['earliest_timestamp']) if train_valid_stats['earliest_timestamp'] and test_stats['earliest_timestamp'] else None
        latest_ts = max(train_valid_stats['latest_timestamp'], test_stats['latest_timestamp']) if train_valid_stats['latest_timestamp'] and test_stats['latest_timestamp'] else None
        total_time_span = (latest_ts - earliest_ts) / (1000 * 60 * 60 * 24) if earliest_ts and latest_ts else 0
        
        print("\n  🌍 整体统计:")
        print(f"    - 总学生数: {total_students:,}")
        print(f"    - 总交互数: {total_interactions:,}")
        print(f"    - 唯一Concepts: {len(all_concepts_combined):,}")
        print(f"    - 唯一Questions: {len(all_questions_combined):,}")
        print(f"    - 平均每个学生交互数: {total_interactions / total_students:.1f}")
        print(f"    - 总体正确率: {overall_accuracy:.2%}")
        print(f"    - 时间跨度: {total_time_span:.1f} 天")
        
        print("\n  📊 Train/Valid vs Test 对比:")
        print(f"    - 学生分布: Train/Valid {train_valid_stats['unique_students']:,} ({train_valid_stats['unique_students']/total_students*100:.1f}%) | Test {test_stats['unique_students']:,} ({test_stats['unique_students']/total_students*100:.1f}%)")
        print(f"    - 交互分布: Train/Valid {train_valid_stats['total_interactions']:,} ({train_valid_stats['total_interactions']/total_interactions*100:.1f}%) | Test {test_stats['total_interactions']:,} ({test_stats['total_interactions']/total_interactions*100:.1f}%)")
        print(f"    - 平均序列长度: Train/Valid {train_valid_stats['avg_sequence_length']:.1f} | Test {test_stats['avg_sequence_length']:.1f}")
        print(f"    - 正确率: Train/Valid {train_valid_stats['overall_accuracy']:.2%} | Test {test_stats['overall_accuracy']:.2%}")
        print(f"    - Concepts覆盖: Train/Valid {train_valid_stats['unique_concepts']:,} | Test {test_stats['unique_concepts']:,}")
        print(f"    - Questions覆盖: Train/Valid {train_valid_stats['unique_questions']:,} | Test {test_stats['unique_questions']:,}")
        
        # 计算Test中新出现的concepts和questions
        df_train_concepts = set()
        df_test_concepts = set()
        df_train_questions = set()
        df_test_questions = set()
        
        for _, row in df_train_valid.iterrows():
            concepts_str = str(row['concepts'])
            questions_str = str(row['questions'])
            if concepts_str != 'NA':
                for c_str in concepts_str.split(','):
                    if c_str and c_str != '-1':
                        try:
                            df_train_concepts.add(int(c_str))
                        except ValueError:
                            continue
            if questions_str != 'NA':
                for q_str in questions_str.split(','):
                    if q_str and q_str != '-1':
                        try:
                            df_train_questions.add(int(q_str))
                        except ValueError:
                            continue
        
        for _, row in df_test.iterrows():
            concepts_str = str(row['concepts'])
            questions_str = str(row['questions'])
            if concepts_str != 'NA':
                for c_str in concepts_str.split(','):
                    if c_str and c_str != '-1':
                        try:
                            df_test_concepts.add(int(c_str))
                        except ValueError:
                            continue
            if questions_str != 'NA':
                for q_str in questions_str.split(','):
                    if q_str and q_str != '-1':
                        try:
                            df_test_questions.add(int(q_str))
                        except ValueError:
                            continue
        
        new_concepts_in_test = df_test_concepts - df_train_concepts
        new_questions_in_test = df_test_questions - df_train_questions
        
        print("\n  🆕 Test中的新内容:")
        print(f"    - 新Concepts: {len(new_concepts_in_test):,} ({len(new_concepts_in_test)/len(df_test_concepts)*100:.1f}% of test concepts)")
        print(f"    - 新Questions: {len(new_questions_in_test):,} ({len(new_questions_in_test)/len(df_test_questions)*100:.1f}% of test questions)")
        
        return {
            'dataset': dataset_name,
            'train_valid': train_valid_stats,
            'test': test_stats,
            'total_students': total_students,
            'total_interactions': total_interactions,
            'total_unique_concepts': len(all_concepts_combined),
            'total_unique_questions': len(all_questions_combined),
            'overall_accuracy': overall_accuracy,
            'total_time_span_days': total_time_span,
            'new_concepts_in_test': len(new_concepts_in_test),
            'new_questions_in_test': len(new_questions_in_test)
        }
    
    return None


if __name__ == "__main__":
    print("🔍 完整数据集统计分析")
    print("=" * 80)
    print("\n这个分析包括：")
    print("  1. Train/Valid数据集的详细统计")
    print("  2. Test数据集的详细统计")
    print("  3. 整体数据集的汇总统计")
    print("  4. Train/Valid和Test的对比分析")
    
    datasets = {
        'EdNet': '/mnt/localssd/pykt-toolkit/data/ednet',
        'ASSISTments2017': '/mnt/localssd/pykt-toolkit/data/assist2017'
    }
    
    all_results = {}
    
    for dataset_name, data_dir in datasets.items():
        result = analyze_complete_dataset(dataset_name, data_dir)
        if result:
            all_results[dataset_name] = result
    
    # 生成对比表格
    if len(all_results) > 0:
        print(f"\n{'='*80}")
        print(f"📊 数据集整体对比")
        print(f"{'='*80}\n")
        
        comparison_data = []
        for dataset_name, result in all_results.items():
            comparison_data.append({
                'Dataset': dataset_name,
                'Total_Students': result['total_students'],
                'Total_Interactions': result['total_interactions'],
                'Unique_Concepts': result['total_unique_concepts'],
                'Unique_Questions': result['total_unique_questions'],
                'Overall_Accuracy': f"{result['overall_accuracy']:.2%}",
                'Avg_Interactions_Per_Student': f"{result['total_interactions'] / result['total_students']:.1f}",
                'Time_Span_Days': f"{result['total_time_span_days']:.1f}",
                'New_Concepts_In_Test': result['new_concepts_in_test'],
                'New_Questions_In_Test': result['new_questions_in_test']
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
        
        # 保存结果
        output_path = "/tmp/complete_dataset_comparison.csv"
        comparison_df.to_csv(output_path, index=False)
        print(f"\n✅ 对比结果已保存: {output_path}")
        
        # 保存详细统计到JSON
        import json
        detailed_output_path = "/tmp/complete_dataset_stats.json"
        with open(detailed_output_path, 'w', encoding='utf-8') as f:
            # Convert datetime to string for JSON serialization
            for dataset_name in all_results:
                for split in ['train_valid', 'test']:
                    if split in all_results[dataset_name] and all_results[dataset_name][split]:
                        stats = all_results[dataset_name][split]
                        if stats.get('earliest_timestamp'):
                            stats['earliest_timestamp'] = str(datetime.fromtimestamp(stats['earliest_timestamp'] / 1000))
                        if stats.get('latest_timestamp'):
                            stats['latest_timestamp'] = str(datetime.fromtimestamp(stats['latest_timestamp'] / 1000))
            
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"✅ 详细统计已保存: {detailed_output_path}")
    
    print(f"\n{'='*80}")
    print("✅ 完整数据集分析完成！")
    print(f"{'='*80}")

