#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演示：从nips_task34随机选择一个学生，使用四种KT模型计算forgetting score
"""

import sys
import os
import pandas as pd
import random
import torch
import json
import numpy as np
from collections import defaultdict

# 添加路径
sys.path.append('/mnt/localssd/pykt-toolkit')
sys.path.append('/mnt/localssd/pykt-toolkit/examples')

from pykt.models import init_model

# 设置随机种子
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# ===== 第1步：随机选择一个学生 =====
print("="*60)
print("第1步：从nips_task34随机选择一个学生")
print("="*60)

df = pd.read_csv('/mnt/localssd/pykt-toolkit/data/nips_task34/test_sequences.csv')
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
print(f"  - 概念列表（前10个）: {concepts[:10]}")
print(f"  - 正确率: {sum(responses)/len(responses)*100:.1f}%")

# ===== 第2步：准备每个concept的最后一次答题信息 =====
print("\n" + "="*60)
print("第2步：准备每个concept的最后一次答题信息")
print("="*60)

# 按concept分组，找到每个concept的最后一次答题
concept_last_interaction = {}
for i in range(len(concepts)):
    cid = concepts[i]
    concept_last_interaction[cid] = {
        'question': questions[i],
        'response': responses[i],
        'timestamp': timestamps[i],
        'index': i
    }

print(f"  - 该学生做过的唯一概念数: {len(concept_last_interaction)}")
print(f"  - 前5个概念的最后答题情况:")
for idx, (cid, info) in enumerate(list(concept_last_interaction.items())[:5]):
    print(f"    Concept {cid}: 第{info['index']}次, 答{'对' if info['response']==1 else '错'}, 时间戳{info['timestamp']}")

# ===== 第3步：加载四种模型 =====
print("\n" + "="*60)
print("第3步：加载四种训练好的KT模型")
print("="*60)

models_info = {
    'LPKT': '/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0',
    'simpleKT': '/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0',
    'DKT': '/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0',
    'AKT': '/mnt/localssd/pykt-toolkit/examples/saved_model/nips_task34_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0'
}

loaded_models = {}
for model_name, model_dir in models_info.items():
    try:
        # 加载config
        config_path = os.path.join(model_dir, 'config.json')
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        
        # 提取model_config和data_config
        model_config = full_config.get('model_config', {})
        data_config = full_config.get('data_config', {})
        
        # 过滤掉训练相关的参数
        training_params = ['learning_rate', 'use_wandb', 'add_uuid', 'optimizer', 'lr', 'weight_decay']
        model_config_filtered = {k: v for k, v in model_config.items() if k not in training_params}
        
        # 初始化模型
        model = init_model(model_name.lower(), model_config_filtered, data_config, full_config.get('emb_type', 'qid'))
        
        # 加载权重（尝试不同的文件名）
        possible_names = ['qid_model.ckpt', 'model.ckpt', 'best_model.ckpt']
        model_path = None
        for name in possible_names:
            test_path = os.path.join(model_dir, name)
            if os.path.exists(test_path):
                model_path = test_path
                break
        
        if model_path is None:
            raise FileNotFoundError(f"No model checkpoint found in {model_dir}")
        
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint)
        model.eval()
        
        loaded_models[model_name] = {
            'model': model,
            'config': full_config,
            'num_c': data_config.get('num_c', model_config_filtered.get('num_c', 100))
        }
        print(f"  ✅ {model_name}: 加载成功 (概念数: {loaded_models[model_name]['num_c']})")
    except Exception as e:
        print(f"  ❌ {model_name}: 加载失败 - {e}")

# ===== 第4步：使用模型预测每个concept的最后答题概率 =====
print("\n" + "="*60)
print("第4步：使用模型预测最后一次答题的正确概率")
print("="*60)

# 准备输入数据（使用所有历史数据，不包括最后一次）
# 注意：这里我们需要准备正确的输入格式

predictions = defaultdict(dict)

for model_name, model_info in loaded_models.items():
    model = model_info['model']
    num_c = model_info['num_c']
    
    print(f"\n{model_name}:")
    
    # 对于每个concept，使用该concept之前的所有历史来预测最后一次
    for cid, last_info in list(concept_last_interaction.items())[:5]:  # 只演示前5个
        last_idx = last_info['index']
        
        if last_idx == 0:
            # 第一次答题，无历史
            pred_prob = 0.5  # 默认概率
        else:
            # 准备历史数据
            hist_q = questions[:last_idx]
            hist_c = concepts[:last_idx]
            hist_r = responses[:last_idx]
            
            # 转换为tensor
            q_tensor = torch.LongTensor([hist_q]).unsqueeze(0)  # [1, 1, seq_len]
            c_tensor = torch.LongTensor([hist_c]).unsqueeze(0)
            r_tensor = torch.LongTensor([hist_r]).unsqueeze(0)
            
            with torch.no_grad():
                # 根据不同模型调用不同的forward方法
                try:
                    if model_name == 'LPKT':
                        # LPKT需要额外的时间间隔信息
                        # 这里简化处理，使用固定时间间隔
                        it = torch.zeros_like(q_tensor)
                        output = model(q_tensor, c_tensor, r_tensor, it, it)
                    else:
                        output = model(q_tensor, c_tensor, r_tensor)
                    
                    # 获取最后一个时间步的预测
                    pred_prob = torch.sigmoid(output[0, -1, cid]).item()
                except Exception as e:
                    print(f"    ⚠️ Concept {cid}: 预测失败 - {e}")
                    pred_prob = 0.5
        
        predictions[model_name][cid] = pred_prob
        print(f"    Concept {cid}: 预测正确概率 = {pred_prob:.4f}")

# ===== 第5步：计算forgetting score =====
print("\n" + "="*60)
print("第5步：计算Forgetting Score")
print("="*60)
print("公式: F_c(t) = (1 - s_t,c) * (Δt_c / (Δt_c + τ))")
print(f"参数: τ = 7 days = {7*24*60} minutes")
print("="*60)

tau = 7 * 24 * 60  # 7天，单位：分钟

forgetting_scores = defaultdict(dict)

for model_name in loaded_models.keys():
    print(f"\n{model_name} Forgetting Scores:")
    
    for cid, last_info in list(concept_last_interaction.items())[:5]:  # 只演示前5个
        s_tc = predictions[model_name].get(cid, 0.5)
        
        # 计算时间差（这里简化，假设从最后一次答题到现在经过了一定时间）
        # 实际应该是：当前时间 - 最后一次该concept的答题时间
        # 这里我们假设使用下一个问题的时间或固定时间差
        last_idx = last_info['index']
        if last_idx < len(timestamps) - 1:
            delta_t = (timestamps[last_idx + 1] - timestamps[last_idx]) / (1000 * 60)  # 转换为分钟
        else:
            delta_t = 60  # 假设60分钟
        
        # 计算forgetting score
        forgetting_score = (1 - s_tc) * (delta_t / (delta_t + tau))
        
        forgetting_scores[model_name][cid] = forgetting_score
        
        print(f"    Concept {cid}:")
        print(f"      - 预测正确概率 s_t,c = {s_tc:.4f}")
        print(f"      - 时间差 Δt_c = {delta_t:.2f} minutes")
        print(f"      - Forgetting Score = {forgetting_score:.6f}")

# ===== 第6步：汇总报告 =====
print("\n" + "="*60)
print("第6步：汇总报告 - Forgetting Score对比")
print("="*60)

print(f"\n学生ID: {student_id}")
print(f"数据集: nips_task34")
print(f"\n前5个概念的Forgetting Score对比:\n")

# 创建表格
print(f"{'Concept':<10} {'LPKT':<12} {'simpleKT':<12} {'DKT':<12} {'AKT':<12}")
print("-" * 60)

for cid in list(concept_last_interaction.keys())[:5]:
    lpkt_score = forgetting_scores.get('LPKT', {}).get(cid, 0)
    simplekt_score = forgetting_scores.get('simpleKT', {}).get(cid, 0)
    dkt_score = forgetting_scores.get('DKT', {}).get(cid, 0)
    akt_score = forgetting_scores.get('AKT', {}).get(cid, 0)
    
    print(f"{cid:<10} {lpkt_score:.6f}    {simplekt_score:.6f}    {dkt_score:.6f}    {akt_score:.6f}")

print("\n" + "="*60)
print("✅ 演示完成！")
print("="*60)

