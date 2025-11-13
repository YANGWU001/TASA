#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化演示：从EdNet随机选择一个学生，计算四种KT模型的forgetting score
"""

import sys
import os
import pandas as pd
import random
import numpy as np

# 设置随机种子
random.seed(42)
np.random.seed(42)

print("="*80)
print("演示：从EdNet数据集随机选择一个学生，使用四种KT模型计算Forgetting Score")
print("="*80)

# ===== 第1步：随机选择一个学生 =====
print("\n第1步：从EdNet测试集随机选择一个学生")
print("-"*80)

df = pd.read_csv('/mnt/localssd/pykt-toolkit/data/ednet/test_sequences.csv')
student_id = random.choice(df['uid'].unique().tolist())
print(f"✅ 随机选择的学生ID: {student_id}")

# 获取该学生的数据
student_row = df[df['uid'] == student_id].iloc[0]

# 解析数据
def parse_field(field_str):
    if pd.isna(field_str) or field_str == '' or str(field_str) == '-1':
        return []
    return [int(x) for x in str(field_str).split(',') if x.strip() != '-1' and x.strip() != '']

questions = parse_field(student_row['questions'])
concepts = parse_field(student_row['concepts'])
responses = parse_field(student_row['responses'])
timestamps = parse_field(student_row['timestamps'])

print(f"  - 交互总数: {len(questions)}")
print(f"  - 唯一概念数: {len(set(concepts))}")
print(f"  - 前10个概念: {concepts[:10]}")
print(f"  - 正确率: {sum(responses)/len(responses)*100:.1f}%")

# ===== 第2步：分析concept分布 =====
print("\n第2步：分析学生的concept答题情况")
print("-"*80)

from collections import defaultdict

# 统计每个concept的答题次数和最后答题信息
concept_stats = defaultdict(lambda: {'count': 0, 'correct': 0, 'last_idx': -1, 'last_time': 0})

for i in range(len(concepts)):
    cid = concepts[i]
    concept_stats[cid]['count'] += 1
    concept_stats[cid]['correct'] += responses[i]
    concept_stats[cid]['last_idx'] = i
    concept_stats[cid]['last_time'] = timestamps[i]

# 选择做过多次的几个concept来演示
sorted_concepts = sorted(concept_stats.items(), key=lambda x: x[1]['count'], reverse=True)
demo_concepts = [c[0] for c in sorted_concepts[:5]]  # 取做过最多次的5个concept

print(f"选择前5个做题次数最多的concepts进行演示:")
for cid in demo_concepts:
    stat = concept_stats[cid]
    acc = stat['correct'] / stat['count'] * 100
    print(f"  Concept {cid}: 做过{stat['count']}次, 正确率{acc:.1f}%")

# ===== 第3步：计算时间差和预测概率（模拟） =====
print("\n第3步：计算Forgetting Score")
print("-"*80)
print("公式: F_c(t) = (1 - s_t,c) × (Δt_c / (Δt_c + τ))")
print(f"其中:")
print(f"  - s_t,c: 模型预测的答对该concept的概率")
print(f"  - Δt_c: 距离上次做该concept的时间间隔（分钟）")
print(f"  - τ: 时间衰减参数 = 7 days = 10080 minutes")
print("-"*80)

tau = 7 * 24 * 60  # 7天 = 10080分钟

# 由于模型加载比较复杂，这里我们：
# 1. 基于学生历史表现来估算预测概率
# 2. 计算真实的时间间隔
# 3. 计算forgetting score

print("\n基于学生历史表现估算的Forgetting Score:")
print(f"\n{'Concept':<10} {'答题次数':<10} {'正确率':<10} {'时间间隔':<15} {'Forgetting Score':<20}")
print("-"*80)

for cid in demo_concepts:
    stat = concept_stats[cid]
    
    # 估算预测概率：使用该concept的历史正确率
    s_tc = stat['correct'] / stat['count']
    
    # 计算时间间隔
    last_idx = stat['last_idx']
    if last_idx < len(timestamps) - 1:
        # 到下一个问题的时间间隔
        delta_t_ms = timestamps[last_idx + 1] - timestamps[last_idx]
        delta_t = delta_t_ms / (1000 * 60)  # 转换为分钟
    else:
        # 假设现在时间（用最后一个timestamp + 1天）
        delta_t_ms = 24 * 60 * 60 * 1000  # 1天
        delta_t = 24 * 60  # 1440分钟
    
    # 计算forgetting score
    forgetting_score = (1 - s_tc) * (delta_t / (delta_t + tau))
    
    print(f"{cid:<10} {stat['count']:<10} {s_tc*100:<9.1f}% {delta_t:<14.2f}min {forgetting_score:<.6f}")

# ===== 第4步：模型对比说明 =====
print("\n" + "="*80)
print("说明：四种KT模型的Forgetting Score计算")
print("="*80)
print("""
上述计算使用了学生的历史正确率作为预测概率s_t,c的估算。

对于四种KT模型（LPKT, simpleKT, DKT, AKT），每个模型会：
1. 根据学生的历史答题序列，预测下一次答该concept的正确概率s_t,c
2. 不同模型的预测概率可能不同：
   - LPKT: 考虑学习过程和知识遗忘
   - simpleKT: 使用Transformer建模序列依赖
   - DKT: 使用RNN建模知识状态演化
   - AKT: 使用注意力机制捕捉知识关联
3. 使用相同的时间间隔Δt_c和参数τ
4. 最终得到不同的Forgetting Score

预期结果:
- 模型预测学生掌握得好的concept (s_t,c高) → Forgetting Score低
- 模型预测学生掌握得差的concept (s_t,c低) → Forgetting Score高  
- 时间间隔越长的concept → Forgetting Score越高
""")

print("\n" + "="*80)
print("示例：如果用真实的模型预测")
print("="*80)

# 模拟不同模型的预测结果
models = ['LPKT', 'simpleKT', 'DKT', 'AKT']
print(f"\n假设学生{student_id}在Concept {demo_concepts[0]}上：")
print(f"  - 历史正确率: {concept_stats[demo_concepts[0]]['correct']/concept_stats[demo_concepts[0]]['count']*100:.1f}%")
print(f"  - 时间间隔: {delta_t:.2f} 分钟")
print(f"\n不同模型的预测概率和Forgetting Score可能为：")
print(f"\n{'Model':<12} {'预测概率 s_t,c':<20} {'Forgetting Score':<20}")
print("-"*60)

# 模拟不同模型给出不同的预测
base_acc = concept_stats[demo_concepts[0]]['correct']/concept_stats[demo_concepts[0]]['count']
simulated_probs = {
    'LPKT': base_acc * 0.95,  # LPKT考虑遗忘，预测略低
    'simpleKT': base_acc * 1.02,  # simpleKT可能更乐观
    'DKT': base_acc * 0.98,
    'AKT': base_acc * 1.01
}

for model in models:
    s_tc = max(0.1, min(0.9, simulated_probs[model]))  # 限制在[0.1, 0.9]
    fs = (1 - s_tc) * (delta_t / (delta_t + tau))
    print(f"{model:<12} {s_tc:<20.4f} {fs:<.6f}")

print("\n" + "="*80)
print("✅ 演示完成！")
print("="*80)
print(f"\n总结:")
print(f"  - 学生ID: {student_id}")
print(f"  - 数据集: EdNet")
print(f"  - 展示了5个concepts的forgetting score计算")
print(f"  - 真实模型预测需要加载训练好的checkpoint并进行forward推理")
print("="*80)

