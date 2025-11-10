#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析训练集、验证集和测试集中的学生分布
检查学生是否在不同集合间重叠
"""

import pandas as pd
import numpy as np
import os

def analyze_student_overlap(dataset_name, data_dir):
    """
    分析数据集中train/valid/test的学生重叠情况
    """
    print(f"\n{'='*80}")
    print(f"📊 数据集: {dataset_name.upper()}")
    print(f"{'='*80}")
    
    train_valid_path = os.path.join(data_dir, "train_valid_sequences.csv")
    test_path = os.path.join(data_dir, "test_sequences.csv")
    
    # 检查文件是否存在
    if not os.path.exists(train_valid_path):
        print(f"❌ 文件不存在: {train_valid_path}")
        return
    
    if not os.path.exists(test_path):
        print(f"❌ 文件不存在: {test_path}")
        return
    
    print(f"\n📂 读取数据文件...")
    print(f"  - Train/Valid: {train_valid_path}")
    print(f"  - Test: {test_path}")
    
    # 读取数据
    df_train_valid = pd.read_csv(train_valid_path)
    df_test = pd.read_csv(test_path)
    
    print(f"\n✅ 数据加载完成")
    print(f"  - Train/Valid records: {len(df_train_valid):,}")
    print(f"  - Test records: {len(df_test):,}")
    
    # 获取学生ID
    train_valid_students = set(df_train_valid['uid'].unique())
    test_students = set(df_test['uid'].unique())
    
    print(f"\n👥 学生数量统计:")
    print(f"  - Train/Valid中的唯一学生: {len(train_valid_students):,}")
    print(f"  - Test中的唯一学生: {len(test_students):,}")
    
    # 分析train和valid的fold分布
    print(f"\n📋 Train/Valid的Fold分布:")
    fold_students = {}
    for fold in sorted(df_train_valid['fold'].unique()):
        students_in_fold = set(df_train_valid[df_train_valid['fold'] == fold]['uid'].unique())
        fold_students[fold] = students_in_fold
        print(f"  - Fold {fold}: {len(students_in_fold):,} 个学生")
    
    # 检查fold之间是否有重叠
    print(f"\n🔍 检查Train/Valid Folds之间的学生重叠:")
    has_overlap_in_folds = False
    for i in sorted(fold_students.keys()):
        for j in sorted(fold_students.keys()):
            if i < j:
                overlap = fold_students[i] & fold_students[j]
                if len(overlap) > 0:
                    print(f"  ⚠️  Fold {i} 和 Fold {j} 有 {len(overlap)} 个重叠学生")
                    has_overlap_in_folds = True
    
    if not has_overlap_in_folds:
        print(f"  ✅ 各个Fold之间没有学生重叠（K-Fold交叉验证）")
    
    # 检查train/valid和test之间的重叠
    print(f"\n🔍 检查Train/Valid和Test之间的学生重叠:")
    overlap_students = train_valid_students & test_students
    
    if len(overlap_students) > 0:
        print(f"  ⚠️  发现重叠！")
        print(f"  - 重叠学生数: {len(overlap_students):,}")
        print(f"  - 重叠比例 (相对Train/Valid): {len(overlap_students)/len(train_valid_students)*100:.2f}%")
        print(f"  - 重叠比例 (相对Test): {len(overlap_students)/len(test_students)*100:.2f}%")
        
        # 分析重叠学生在train/valid中的分布
        print(f"\n  📊 重叠学生在Train/Valid中的Fold分布:")
        for fold in sorted(df_train_valid['fold'].unique()):
            overlap_in_fold = overlap_students & fold_students[fold]
            if len(overlap_in_fold) > 0:
                print(f"    - Fold {fold}: {len(overlap_in_fold):,} 个重叠学生 ({len(overlap_in_fold)/len(fold_students[fold])*100:.1f}%)")
        
        # 分析重叠学生的数据量
        print(f"\n  📈 重叠学生的数据量分析:")
        
        # Train/Valid中重叠学生的数据
        overlap_train_valid = df_train_valid[df_train_valid['uid'].isin(overlap_students)]
        print(f"    - Train/Valid中重叠学生的记录数: {len(overlap_train_valid):,}")
        print(f"    - 占Train/Valid总记录的比例: {len(overlap_train_valid)/len(df_train_valid)*100:.2f}%")
        
        # Test中重叠学生的数据
        overlap_test = df_test[df_test['uid'].isin(overlap_students)]
        print(f"    - Test中重叠学生的记录数: {len(overlap_test):,}")
        print(f"    - 占Test总记录的比例: {len(overlap_test)/len(df_test)*100:.2f}%")
        
        # 展示几个重叠学生的例子
        print(f"\n  📋 重叠学生示例（前10个）:")
        sample_overlap = list(overlap_students)[:10]
        for student_id in sample_overlap:
            train_records = len(df_train_valid[df_train_valid['uid'] == student_id])
            test_records = len(df_test[df_test['uid'] == student_id])
            print(f"    - 学生 {student_id}: Train/Valid有{train_records}条, Test有{test_records}条")
        
        print(f"\n  💡 结论: 这是 **时序分割 (Temporal Split)**")
        print(f"     - 同一个学生的早期数据在Train/Valid中")
        print(f"     - 同一个学生的后期数据在Test中")
        print(f"     - 这种方式评估模型对**同一学生未来表现**的预测能力")
        
    else:
        print(f"  ✅ 没有重叠！")
        print(f"  - Train/Valid和Test中的学生完全不同")
        
        only_train_valid = train_valid_students - test_students
        only_test = test_students - train_valid_students
        
        print(f"\n  📊 独立学生统计:")
        print(f"    - 仅在Train/Valid中: {len(only_train_valid):,} 个学生")
        print(f"    - 仅在Test中: {len(only_test):,} 个学生")
        
        print(f"\n  💡 结论: 这是 **冷启动分割 (Cold-Start Split)**")
        print(f"     - Train/Valid和Test使用完全不同的学生")
        print(f"     - 这种方式评估模型对**新学生**的泛化能力")
    
    # 分析validation策略
    print(f"\n📋 Validation策略分析:")
    num_folds = len(df_train_valid['fold'].unique())
    print(f"  - 使用 {num_folds}-Fold 交叉验证")
    print(f"  - 每个Fold作为验证集时，其他{num_folds-1}个Fold作为训练集")
    
    # 总结
    print(f"\n📊 数据划分总结:")
    total_students = len(train_valid_students | test_students)
    print(f"  - 总学生数: {total_students:,}")
    print(f"  - Train/Valid学生: {len(train_valid_students):,} ({len(train_valid_students)/total_students*100:.1f}%)")
    print(f"  - Test学生: {len(test_students):,} ({len(test_students)/total_students*100:.1f}%)")
    if len(overlap_students) > 0:
        print(f"  - 重叠学生: {len(overlap_students):,} ({len(overlap_students)/total_students*100:.1f}%)")
        print(f"  - 划分类型: ⏱️  **时序分割 (Temporal Split)**")
    else:
        print(f"  - 重叠学生: 0")
        print(f"  - 划分类型: 🆕 **冷启动分割 (Cold-Start Split)**")
    
    return {
        'dataset': dataset_name,
        'train_valid_students': len(train_valid_students),
        'test_students': len(test_students),
        'overlap_students': len(overlap_students),
        'total_students': total_students,
        'split_type': 'Temporal' if len(overlap_students) > 0 else 'Cold-Start'
    }


if __name__ == "__main__":
    print("🔍 学生分割策略分析")
    print("=" * 80)
    print("\n这个分析将告诉你：")
    print("  1. Train/Valid和Test中的学生是否重叠")
    print("  2. 数据集使用的是时序分割还是冷启动分割")
    print("  3. Validation策略（K-Fold交叉验证）")
    
    datasets = {
        'EdNet': '/mnt/localssd/pykt-toolkit/data/ednet',
        'ASSISTments2017': '/mnt/localssd/pykt-toolkit/data/assist2017'
    }
    
    results = []
    
    for dataset_name, data_dir in datasets.items():
        result = analyze_student_overlap(dataset_name, data_dir)
        if result:
            results.append(result)
    
    # 对比总结
    if len(results) > 0:
        print(f"\n{'='*80}")
        print(f"📊 数据集对比总结")
        print(f"{'='*80}\n")
        
        comparison_df = pd.DataFrame(results)
        print(comparison_df.to_string(index=False))
        
        # 保存结果
        output_path = "/tmp/student_split_analysis.csv"
        comparison_df.to_csv(output_path, index=False)
        print(f"\n✅ 分析结果已保存: {output_path}")
    
    print(f"\n{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}")

