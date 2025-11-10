#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Carnegie Learning数据集统计分析
分析Algebra2005和Bridge2Algebra2006数据集
"""

import pandas as pd
import os
from collections import defaultdict, Counter

def parse_csv_field(field_str):
    """解析CSV字段，处理逗号分隔的字符串"""
    if pd.isna(field_str) or field_str == 'NA' or field_str == '':
        return []
    
    try:
        # 尝试直接分割
        values = str(field_str).strip().split(',')
        result = []
        for v in values:
            v = v.strip()
            if v and v != '-1' and v != 'NA':
                try:
                    result.append(int(v))
                except ValueError:
                    # 如果不能转换为int，保留字符串（用于skills）
                    result.append(v)
        return result
    except Exception as e:
        print(f"警告: 解析字段失败 {field_str}: {e}")
        return []

def analyze_dataset(dataset_name, data_path):
    """分析单个数据集"""
    print(f"\n{'='*60}")
    print(f"  {dataset_name} 数据集分析")
    print(f"{'='*60}\n")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}\n")
        return None
    
    try:
        # 读取数据（CSV格式，有header）
        df = pd.read_csv(data_path)
        
        # 解析字段
        all_students = []
        all_questions = []
        all_concepts = []
        all_responses = []
        all_timestamps = []
        total_interactions = 0
        sequence_lengths = []
        
        print(f"正在分析 {len(df)} 个序列...")
        
        for idx, row in df.iterrows():
            # 学生ID
            student_id = row['uid']
            
            # 解析各个字段
            questions = parse_csv_field(row['questions'])
            concepts = parse_csv_field(row['concepts'])
            responses = parse_csv_field(row['responses'])
            timestamps = parse_csv_field(row['timestamps'])
            
            # 计算序列长度
            seq_len = len(responses)
            
            # 对于concepts，可能是字符串，需要特殊处理
            if len(concepts) > 0 and isinstance(concepts[0], str):
                # 如果是字符串形式的concept（如"Skill~~Name"），需要拆分
                expanded_concepts = []
                for c in concepts:
                    if '~~' in str(c):
                        expanded_concepts.extend(str(c).split('~~'))
                    else:
                        expanded_concepts.append(str(c))
                concepts = expanded_concepts
            
            # 确保数据一致性
            if len(responses) != seq_len:
                print(f"  警告: 学生 {student_id} 的序列长度不一致: {len(responses)} vs {seq_len}")
                continue
            
            all_students.append(student_id)
            all_questions.extend(questions)
            all_concepts.extend(concepts)
            all_responses.extend(responses)
            all_timestamps.extend([t for t in timestamps if isinstance(t, (int, float))])
            total_interactions += seq_len
            sequence_lengths.append(seq_len)
        
        # 统计信息
        num_students = len(set(all_students))
        num_unique_questions = len(set(all_questions))
        num_unique_concepts = len(set(all_concepts))
        
        print(f"\n📊 基本统计信息")
        print(f"{'─'*60}")
        print(f"  学生数量:        {num_students:,}")
        print(f"  唯一问题数:      {num_unique_questions:,}")
        print(f"  唯一概念/技能数: {num_unique_concepts:,}")
        print(f"  总交互数:        {total_interactions:,}")
        
        # 序列长度统计
        if sequence_lengths:
            avg_seq_len = sum(sequence_lengths) / len(sequence_lengths)
            min_seq_len = min(sequence_lengths)
            max_seq_len = max(sequence_lengths)
            median_seq_len = sorted(sequence_lengths)[len(sequence_lengths)//2]
            
            print(f"\n📏 序列长度统计")
            print(f"{'─'*60}")
            print(f"  平均序列长度:    {avg_seq_len:.1f}")
            print(f"  中位数序列长度:  {median_seq_len}")
            print(f"  最小序列长度:    {min_seq_len}")
            print(f"  最大序列长度:    {max_seq_len}")
        
        # 答题正确率
        if all_responses:
            correct_responses = sum(1 for r in all_responses if r == 1)
            accuracy = correct_responses / len(all_responses) * 100
            
            print(f"\n✅ 答题正确率")
            print(f"{'─'*60}")
            print(f"  正确答题数:      {correct_responses:,}")
            print(f"  错误答题数:      {len(all_responses) - correct_responses:,}")
            print(f"  总体正确率:      {accuracy:.2f}%")
        
        # 时间戳信息
        if all_timestamps:
            print(f"\n⏱️  时间戳信息")
            print(f"{'─'*60}")
            print(f"  有时间戳的交互: {len(all_timestamps):,}")
            print(f"  时间戳覆盖率:   {len(all_timestamps)/total_interactions*100:.1f}%")
        
        # 概念/技能分布
        if all_concepts:
            concept_counts = Counter(all_concepts)
            top_10_concepts = concept_counts.most_common(10)
            
            print(f"\n🎯 Top 10 最常见的概念/技能")
            print(f"{'─'*60}")
            for i, (concept, count) in enumerate(top_10_concepts, 1):
                # 截断过长的concept名称
                concept_str = str(concept)[:40] + '...' if len(str(concept)) > 40 else str(concept)
                percentage = count / len(all_concepts) * 100
                print(f"  {i:2d}. {concept_str:45s} {count:6,} ({percentage:5.2f}%)")
        
        # 数据稀疏性
        if num_students > 0 and num_unique_questions > 0:
            potential_interactions = num_students * num_unique_questions
            sparsity = (1 - total_interactions / potential_interactions) * 100
            
            print(f"\n📉 数据稀疏性")
            print(f"{'─'*60}")
            print(f"  潜在交互数:      {potential_interactions:,}")
            print(f"  实际交互数:      {total_interactions:,}")
            print(f"  数据稀疏度:      {sparsity:.2f}%")
        
        print(f"\n{'='*60}\n")
        
        return {
            'dataset_name': dataset_name,
            'num_students': num_students,
            'num_questions': num_unique_questions,
            'num_concepts': num_unique_concepts,
            'total_interactions': total_interactions,
            'avg_seq_len': avg_seq_len if sequence_lengths else 0,
            'accuracy': accuracy if all_responses else 0,
            'has_timestamps': len(all_timestamps) > 0
        }
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  Carnegie Learning 数据集统计分析")
    print("="*60)
    
    datasets = {
        'Algebra2005': '/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv',
        'Bridge2Algebra2006': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv'
    }
    
    results = []
    
    for dataset_name, data_path in datasets.items():
        result = analyze_dataset(dataset_name, data_path)
        if result:
            results.append(result)
    
    # 对比总结
    if len(results) >= 2:
        print("\n" + "="*60)
        print("  数据集对比总结")
        print("="*60 + "\n")
        
        print(f"{'指标':<25} {'Algebra2005':>15} {'Bridge2Algebra2006':>20}")
        print("─"*60)
        
        for r in results:
            if r['dataset_name'] == 'Algebra2005':
                alg2005 = r
            else:
                bridge2006 = r
        
        if 'alg2005' in locals() and 'bridge2006' in locals():
            print(f"{'学生数':<25} {alg2005['num_students']:>15,} {bridge2006['num_students']:>20,}")
            print(f"{'问题数':<25} {alg2005['num_questions']:>15,} {bridge2006['num_questions']:>20,}")
            print(f"{'概念数':<25} {alg2005['num_concepts']:>15,} {bridge2006['num_concepts']:>20,}")
            print(f"{'总交互数':<25} {alg2005['total_interactions']:>15,} {bridge2006['total_interactions']:>20,}")
            print(f"{'平均序列长度':<25} {alg2005['avg_seq_len']:>15.1f} {bridge2006['avg_seq_len']:>20.1f}")
            print(f"{'正确率 (%)':<25} {alg2005['accuracy']:>15.2f} {bridge2006['accuracy']:>20.2f}")
            print(f"{'时间戳':<25} {'✅' if alg2005['has_timestamps'] else '❌':>15} {'✅' if bridge2006['has_timestamps'] else '❌':>20}")
            print()
    
    # 保存结果
    if results:
        result_df = pd.DataFrame(results)
        output_file = '/mnt/localssd/carnegie_datasets_statistics.csv'
        result_df.to_csv(output_file, index=False)
        print(f"✅ 统计结果已保存到: {output_file}\n")

if __name__ == '__main__':
    main()

