#!/usr/bin/env python
"""
演示如何将FS预测结果与Bank数据结合使用

展示：
1. 加载学生的Forgetting Score（来自KT模型预测）
2. 加载学生的Persona（来自Bank）
3. 加载学生的Memory（来自Bank）
4. 综合展示学生的学习状态
"""

import pandas as pd
import json
import os
import numpy as np

def load_student_fs(dataset, student_id, fs_file):
    """加载学生的Forgetting Score"""
    df = pd.read_csv(fs_file)
    student_df = df[df['student_id'] == student_id]
    return student_df

def load_student_persona(dataset, student_id, bank_dir='/mnt/localssd/bank'):
    """加载学生的Persona"""
    persona_file = os.path.join(bank_dir, 'persona', dataset, 'data', f'{student_id}.json')
    if not os.path.exists(persona_file):
        return None
    with open(persona_file, 'r') as f:
        return json.load(f)

def load_student_memory(dataset, student_id, bank_dir='/mnt/localssd/bank'):
    """加载学生的Memory"""
    memory_file = os.path.join(bank_dir, 'memory', dataset, 'data', f'{student_id}.json')
    if not os.path.exists(memory_file):
        return None
    with open(memory_file, 'r') as f:
        return json.load(f)

def demo_single_student():
    """演示单个学生的完整信息"""
    print("="*100)
    print("🎓 学生学习状态综合分析")
    print("="*100)
    
    # 配置
    dataset = 'assist2017'
    student_id = 1643  # test集中的第一个学生
    fs_file = '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/fs_assist2017_lpkt_with_uid.csv'
    
    print(f"\n数据集: {dataset.upper()}")
    print(f"学生ID: {student_id}")
    
    # 1. 加载Forgetting Scores
    print(f"\n{'='*100}")
    print("📊 1. Forgetting Scores (来自LPKT模型预测)")
    print(f"{'='*100}")
    
    df_fs = load_student_fs(dataset, student_id, fs_file)
    
    if len(df_fs) == 0:
        print(f"⚠️  该学生在test集中没有数据")
        return
    
    print(f"\n该学生在 {len(df_fs)} 个concept上有Forgetting Score预测:")
    print(f"\nTop 5 高FS (容易遗忘的concept):")
    top_fs = df_fs.nlargest(5, 'fs')[['concept_id', 's_tc', 'fs', 'last_response', 'num_attempts']]
    print(top_fs.to_string(index=False))
    
    print(f"\nTop 5 低FS (不容易遗忘的concept):")
    bottom_fs = df_fs.nsmallest(5, 'fs')[['concept_id', 's_tc', 'fs', 'last_response', 'num_attempts']]
    print(bottom_fs.to_string(index=False))
    
    # 2. 加载Persona
    print(f"\n{'='*100}")
    print("👤 2. Persona (学生长期掌握程度)")
    print(f"{'='*100}")
    
    persona = load_student_persona(dataset, student_id)
    
    if persona and 'persona' in persona:
        print(f"\n该学生的Persona包含 {len(persona['persona'])} 个concept:")
        
        # 展示前3个
        print(f"\n示例 (前3个concept):")
        for i, p in enumerate(persona['persona'][:3]):
            print(f"\n  Concept {i+1}:")
            print(f"    Keywords: {p['keywords']}")
            print(f"    Description: {p['description'][:200]}...")
    else:
        print("⚠️  该学生没有Persona数据（可能只在test集中）")
    
    # 3. 加载Memory
    print(f"\n{'='*100}")
    print("📝 3. Memory (学习事件记录)")
    print(f"{'='*100}")
    
    memory = load_student_memory(dataset, student_id)
    
    if memory and 'memory' in memory:
        print(f"\n该学生的Memory包含 {len(memory['memory'])} 条学习事件:")
        
        # 展示前5条
        print(f"\n最近的5条事件:")
        for i, m in enumerate(memory['memory'][:5]):
            print(f"  {i+1}. {m['description'][:150]}...")
    else:
        print("⚠️  该学生没有Memory数据（可能只在test集中）")
    
    # 4. 综合分析
    print(f"\n{'='*100}")
    print("🔍 4. 综合分析")
    print(f"{'='*100}\n")
    
    print("【Forgetting Score统计】")
    print(f"  平均FS: {df_fs['fs'].mean():.4f}")
    print(f"  最高FS: {df_fs['fs'].max():.4f} (Concept {df_fs.loc[df_fs['fs'].idxmax(), 'concept_id']})")
    print(f"  最低FS: {df_fs['fs'].min():.4f} (Concept {df_fs.loc[df_fs['fs'].idxmin(), 'concept_id']})")
    
    high_fs_concepts = df_fs[df_fs['fs'] >= 0.3]
    if len(high_fs_concepts) > 0:
        print(f"\n【需要关注的概念】(FS ≥ 0.3)")
        print(f"  共 {len(high_fs_concepts)} 个concept需要重点复习")
        print(f"  这些concept的平均答错率: {(1-high_fs_concepts['last_response'].mean()):.1%}")
        print(f"  Concept IDs: {list(high_fs_concepts['concept_id'].values)}")
    
    low_fs_concepts = df_fs[df_fs['fs'] < 0.1]
    if len(low_fs_concepts) > 0:
        print(f"\n【掌握较好的概念】(FS < 0.1)")
        print(f"  共 {len(low_fs_concepts)} 个concept掌握稳定")
        print(f"  这些concept的平均答错率: {(1-low_fs_concepts['last_response'].mean()):.1%}")

def demo_multiple_students():
    """演示多个学生的FS分布"""
    print(f"\n{'='*100}")
    print("📊 多学生分析")
    print(f"{'='*100}\n")
    
    dataset = 'assist2017'
    fs_file = '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_0_0/fs_assist2017_lpkt_with_uid.csv'
    
    df = pd.read_csv(fs_file)
    
    print(f"数据集: {dataset.upper()}")
    print(f"总学生数: {df['student_id'].nunique()}")
    print(f"总记录数: {len(df)}")
    
    # 按学生统计
    print(f"\n【按学生统计平均FS】")
    student_stats = df.groupby('student_id').agg({
        'fs': ['mean', 'max', 'min'],
        'concept_id': 'count',
        'last_response': lambda x: 1 - x.mean()
    }).round(4)
    student_stats.columns = ['Avg_FS', 'Max_FS', 'Min_FS', 'Num_Concepts', 'Error_Rate']
    
    print(f"\nTop 5 高平均FS学生 (更容易遗忘):")
    print(student_stats.nlargest(5, 'Avg_FS').to_string())
    
    print(f"\nTop 5 低平均FS学生 (记忆更稳定):")
    print(student_stats.nsmallest(5, 'Avg_FS').to_string())
    
    # 概念层面统计
    print(f"\n【按Concept统计】")
    concept_stats = df.groupby('concept_id').agg({
        'fs': 'mean',
        'student_id': 'count',
        'last_response': lambda x: 1 - x.mean()
    }).round(4)
    concept_stats.columns = ['Avg_FS', 'Num_Students', 'Error_Rate']
    
    print(f"\nTop 5 高平均FS的concept (整体更容易遗忘):")
    print(concept_stats.nlargest(5, 'Avg_FS').to_string())

def main():
    print("\n🚀 Bank + FS集成演示\n")
    print("本脚本演示如何将:")
    print("  1. KT模型的Forgetting Score预测")
    print("  2. Bank中的Persona (长期掌握程度)")
    print("  3. Bank中的Memory (学习事件)")
    print("结合使用，提供学生的全方位学习分析\n")
    
    # 演示单个学生
    demo_single_student()
    
    # 演示多个学生
    demo_multiple_students()
    
    print(f"\n{'='*100}")
    print("✅ 演示完成！")
    print(f"{'='*100}")
    
    print(f"\n💡 数据对应关系:")
    print(f"  - FS文件中的 student_id = Bank中的文件名")
    print(f"  - FS文件中的 concept_id = Bank中persona/memory的concept")
    print(f"  - 可以根据student_id + concept_id 查询完整信息")
    
    print(f"\n📁 文件位置:")
    print(f"  - FS (带uid): /mnt/localssd/pykt-toolkit/examples/saved_model/*/fs_*_with_uid.csv")
    print(f"  - Persona: /mnt/localssd/bank/persona/<dataset>/data/<student_id>.json")
    print(f"  - Memory: /mnt/localssd/bank/memory/<dataset>/data/<student_id>.json")
    print(f"  - Embeddings: /mnt/localssd/bank/persona/<dataset>/embeddings/<student_id>_*.npz")

if __name__ == '__main__':
    main()

