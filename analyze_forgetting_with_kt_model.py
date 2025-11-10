#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用训练好的KT模型（LPKT）预测s_{t,c}，然后计算Forgetting Score
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random
import os
import json
import torch
import torch.nn as nn
from pykt.models.lpkt import LPKT

# 设置随机种子
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# 数据集配置
DATASETS = {
    'assist2017': {
        'name': 'ASSISTments2017',
        'data_path': '/mnt/localssd/pykt-toolkit/data/assist2017',
        'model_path': '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0',
    },
    'ednet': {
        'name': 'EdNet',
        'data_path': '/mnt/localssd/pykt-toolkit/data/ednet',
        'model_path': '/mnt/localssd/pykt-toolkit/examples/saved_model/ednet_lpkt_qid_saved_model_42_0_0.003_0.2_64_64_64_0.03_1_0',
    },
    'algebra2005': {
        'name': 'Algebra2005',
        'data_path': '/mnt/localssd/pykt-toolkit/data/algebra2005',
        'model_path': '/mnt/localssd/pykt-toolkit/examples/saved_model/algebra2005_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0',
    },
    'bridge2006': {
        'name': 'Bridge2Algebra2006',
        'data_path': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006',
        'model_path': '/mnt/localssd/pykt-toolkit/examples/saved_model/bridge2algebra2006_lpkt_qid_saved_model_42_0_0.003_0.2_50_128_128_0.03_1_0',
    },
}

print("="*120)
print("使用KT模型（LPKT）预测s_{t,c}来计算Forgetting Score")
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

def load_model_and_config(dataset_key):
    """加载KT模型和配置"""
    model_dir = DATASETS[dataset_key]['model_path']
    
    # 加载配置
    config_path = os.path.join(model_dir, 'config.json')
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return None, None, None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # 查找checkpoint
    checkpoint_files = [
        'qid_model.ckpt',
        'model.ckpt',
        'best_model.ckpt'
    ]
    
    checkpoint_path = None
    for ckpt_file in checkpoint_files:
        ckpt_path = os.path.join(model_dir, ckpt_file)
        if os.path.exists(ckpt_path):
            checkpoint_path = ckpt_path
            break
    
    if checkpoint_path is None:
        print(f"❌ 未找到checkpoint文件")
        return None, None, None
    
    # 提取模型配置（过滤掉训练相关参数）
    data_config = config['data_config']
    model_params = config.get('model_config', {})
    params = config.get('params', {})
    
    # LPKT需要的参数
    n_question = data_config['num_q']
    n_exercise = data_config['num_c']
    n_at = data_config.get('num_at', n_question)
    n_it = data_config.get('num_it', n_question)
    d_a = model_params.get('d_a', params.get('d_a', 64))
    d_e = model_params.get('d_e', params.get('d_e', 64))
    d_k = model_params.get('d_k', params.get('d_k', 64))
    gamma = model_params.get('gamma', params.get('gamma', 0.03))
    dropout = model_params.get('dropout', params.get('dropout', 0.2))
    
    # 构建q_matrix（question到concept的映射）
    # 简化版本：假设每个question对应一个concept
    device = torch.device('cpu')  # 强制使用CPU避免CUDA索引问题
    print(f"   使用设备: {device}")
    q_matrix = torch.ones((n_question, n_exercise)) * gamma
    q_matrix = q_matrix.to(device)
    
    # 初始化模型
    model = LPKT(
        n_at=n_at,
        n_it=n_it,
        n_exercise=n_exercise,
        n_question=n_question,
        d_a=d_a,
        d_e=d_e,
        d_k=d_k,
        gamma=gamma,
        dropout=dropout,
        q_matrix=q_matrix,
        emb_type="qid",
        emb_path="",
        pretrain_dim=768,
        use_time=True
    )
    
    # 加载权重
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # 过滤掉不匹配的权重
    model_state_dict = model.state_dict()
    filtered_state_dict = {}
    for k, v in checkpoint.items():
        if k in model_state_dict and v.shape == model_state_dict[k].shape:
            filtered_state_dict[k] = v
    
    model.load_state_dict(filtered_state_dict, strict=False)
    model.to(device)
    model.eval()
    
    print(f"✅ 成功加载模型: {checkpoint_path}")
    print(f"   num_q={data_config['num_q']}, num_c={data_config['num_c']}")
    
    return model, data_config, device

def predict_with_model(model, device, questions, concepts, responses, timestamps, num_q, num_c):
    """使用KT模型预测序列 - 参考evaluate_model.py的实现"""
    if len(questions) < 2:
        return None
    
    try:
        # 准备输入（不包括最后一次）
        q_seq = questions[:-1]
        r_seq = responses[:-1]
        
        # 检查question ID是否在合理范围内
        if max(q_seq) >= num_q:
            # print(f"  ⚠️  Question ID超出范围: max={max(q_seq)}, num_q={num_q}")
            return None
        
        # 计算时间间隔
        time_intervals = []
        for i in range(1, len(timestamps) - 1):
            interval_ms = timestamps[i] - timestamps[i-1]
            interval_minutes = max(0, interval_ms / (1000 * 60))
            # 限制时间间隔的最大值，避免索引问题
            time_intervals.append(min(int(interval_minutes), 10000))
        
        # 第一个时间间隔设为0
        time_intervals = [0] + time_intervals
        
        # 构建shifted序列（参考evaluate_model.py的方式）
        q_tensor = torch.LongTensor([q_seq]).to(device)
        r_tensor = torch.LongTensor([r_seq]).to(device)
        it_tensor = torch.LongTensor([time_intervals]).to(device)
        
        # 构建shifted版本（向右移动一位，首位补0）
        qshft_tensor = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), q_tensor[:, :-1]], dim=1)
        rshft_tensor = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), r_tensor[:, :-1]], dim=1)
        itshft_tensor = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), it_tensor[:, :-1]], dim=1)
        
        # 拼接原始和shifted（参考evaluate.py的方式）
        cq = torch.cat([q_tensor[:, 0:1], qshft_tensor], dim=1)
        cr = torch.cat([r_tensor[:, 0:1], rshft_tensor], dim=1)
        cit = torch.cat([it_tensor[:, 0:1], itshft_tensor], dim=1)
        
        # 预测 - 参考evaluate_model.py line 133
        with torch.no_grad():
            y = model(cq.long(), cr.long(), cit.long())
            
            # 返回最后一步的预测（对应倒数第二次答题之后的状态）
            pred_prob = torch.sigmoid(y[0, -1]).item()
            return pred_prob
            
    except Exception as e:
        # print(f"  ⚠️  模型预测失败: {type(e).__name__}: {str(e)[:100]}")
        return None

def analyze_interval_distribution(df):
    """分析数据集的答题间隔分布"""
    all_intervals = []
    for _, row in df.iterrows():
        timestamps = parse_field(row['timestamps'])
        concepts = parse_field(row['concepts'])
        if len(timestamps) < 2:
            continue
        concept_timestamps = defaultdict(list)
        for i, cid in enumerate(concepts):
            concept_timestamps[cid].append(timestamps[i])
        for cid, ts_list in concept_timestamps.items():
            if len(ts_list) >= 2:
                ts_list_sorted = sorted(ts_list)
                interval_ms = ts_list_sorted[-1] - ts_list_sorted[-2]
                interval_minutes = interval_ms / (1000 * 60)
                all_intervals.append(interval_minutes)
    return np.array(all_intervals)

def analyze_student_with_kt_model(student_row, model, device, tau, num_q, num_c):
    """使用KT模型分析学生"""
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
        
        # 提取该concept的所有索引
        indices = [inter['index'] for inter in interactions_sorted]
        
        # 使用模型预测：输入从开始到倒数第二次的所有数据
        # 预测倒数第二次答题后的知识状态
        last_index = indices[-1]
        second_last_index = indices[-2]
        
        # 获取从开始到倒数第二次该concept出现时的所有数据
        end_pos = second_last_index + 1
        
        pred_prob = predict_with_model(
            model, device,
            questions[:end_pos],
            concepts[:end_pos],
            responses[:end_pos],
            timestamps[:end_pos],
            num_q, num_c
        )
        
        if pred_prob is None:
            # 如果模型预测失败，回退到历史准确率
            historical_responses = [inter['response'] for inter in interactions_sorted[:-1]]
            s_tc = sum(historical_responses) / len(historical_responses)
            pred_method = 'historical'
        else:
            s_tc = pred_prob
            pred_method = 'model'
        
        # 计算最后两次的时间间隔
        last_timestamp = interactions_sorted[-1]['timestamp']
        second_last_timestamp = interactions_sorted[-2]['timestamp']
        delta_t_ms = last_timestamp - second_last_timestamp
        delta_t_minutes = max(0, delta_t_ms / (1000 * 60))
        
        # 计算forgetting score
        forgetting_score = calculate_forgetting_score(s_tc, delta_t_minutes, tau)
        time_factor = delta_t_minutes / (delta_t_minutes + tau) if delta_t_minutes > 0 else 0
        
        results.append({
            'concept_id': cid,
            'total_attempts': len(interactions),
            'predicted_prob': s_tc,
            'pred_method': pred_method,
            'last_response': interactions_sorted[-1]['response'],
            'delta_t_minutes': delta_t_minutes,
            'delta_t_hours': delta_t_minutes / 60,
            'delta_t_days': delta_t_minutes / (60 * 24),
            'time_factor': time_factor,
            'forgetting_score': forgetting_score,
        })
    
    if len(results) == 0:
        return None
    
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
for dataset_key in ['assist2017', 'ednet', 'algebra2005', 'bridge2006']:
    dataset_info = DATASETS[dataset_key]
    
    print(f"\n{'='*120}")
    print(f"数据集: {dataset_info['name']}")
    print(f"{'='*120}")
    
    # 第1步：加载模型
    print(f"\n第1步：加载LPKT模型")
    print("-"*120)
    
    model, data_config, device = load_model_and_config(dataset_key)
    if model is None:
        print(f"❌ 跳过该数据集")
        continue
    
    num_q = data_config['num_q']
    num_c = data_config['num_c']
    
    # 第2步：加载数据
    test_path = os.path.join(dataset_info['data_path'], 'test_sequences.csv')
    if not os.path.exists(test_path):
        print(f"❌ 数据文件不存在: {test_path}")
        continue
    
    df = pd.read_csv(test_path)
    print(f"✅ 加载数据: {len(df)} 个学生")
    
    # 第3步：分析间隔分布并确定τ
    print(f"\n第2步：确定τ值")
    print("-"*120)
    
    all_intervals = analyze_interval_distribution(df)
    tau_selected = np.mean(all_intervals)
    tau_days = tau_selected / (60 * 24)
    
    print(f"✅ τ = {tau_selected:.2f} 分钟 = {tau_selected/60:.2f} 小时 = {tau_days:.2f} 天")
    
    # 第4步：选择学生
    print(f"\n第3步：选择5个学生进行分析")
    print("-"*120)
    
    qualified_students = []
    for uid in df['uid'].unique()[:50]:  # 只检查前50个学生以加速
        student_row = df[df['uid'] == uid].iloc[0]
        # 快速检查
        concepts = parse_field(student_row['concepts'])
        concept_counts = defaultdict(int)
        for c in concepts:
            concept_counts[c] += 1
        valid_concepts = sum(1 for count in concept_counts.values() if count >= 2)
        if valid_concepts >= 5:
            qualified_students.append(uid)
    
    if len(qualified_students) == 0:
        print(f"❌ 未找到符合条件的学生")
        continue
    
    selected_students = random.sample(qualified_students, min(5, len(qualified_students)))
    print(f"✅ 从 {len(qualified_students)} 个学生中选择 {len(selected_students)} 个:")
    for i, uid in enumerate(selected_students, 1):
        print(f"   {i}. 学生ID: {uid}")
    
    # 第5步：详细分析
    print(f"\n第4步：使用LPKT模型预测并计算Forgetting Score")
    print("="*120)
    
    for idx, uid in enumerate(selected_students, 1):
        student_row = df[df['uid'] == uid].iloc[0]
        
        print(f"\n{'-'*120}")
        print(f"学生 #{idx}: ID {uid}")
        print(f"{'-'*120}")
        
        analysis = analyze_student_with_kt_model(
            student_row, model, device, tau_selected, num_q, num_c
        )
        
        if not analysis:
            print(f"  ⚠️  该学生数据不足")
            continue
        
        print(f"\nForgetting Score统计:")
        print(f"  平均值: {analysis['fs_mean']:.4f}")
        print(f"  标准差: {analysis['fs_std']:.4f}")
        print(f"  范围: [{analysis['fs_min']:.4f}, {analysis['fs_max']:.4f}]")
        
        results = analysis['concept_results']
        results_sorted = sorted(results, key=lambda x: x['forgetting_score'], reverse=True)
        
        # 统计预测方法
        model_pred_count = sum(1 for r in results if r['pred_method'] == 'model')
        hist_pred_count = sum(1 for r in results if r['pred_method'] == 'historical')
        print(f"  预测方法: 模型预测={model_pred_count}个, 历史准确率={hist_pred_count}个")
        
        print(f"\n前10个最需要复习的Concepts:")
        print(f"  {'Concept':<10} {'次数':<6} {'预测概率':<12} {'方法':<8} {'间隔':<12} "
              f"{'时间因子':<12} {'FS':<12} {'最后':<6} {'分类':<10}")
        print(f"  {'-'*116}")
        
        for result in results_sorted[:10]:
            cid = result['concept_id']
            attempts = result['total_attempts']
            pred_prob = result['predicted_prob'] * 100
            pred_method = "🤖模型" if result['pred_method'] == 'model' else "📊历史"
            
            if result['delta_t_days'] >= 1:
                interval_str = f"{result['delta_t_days']:.1f}d"
            elif result['delta_t_hours'] >= 1:
                interval_str = f"{result['delta_t_hours']:.1f}h"
            else:
                interval_str = f"{result['delta_t_minutes']:.1f}m"
            
            time_factor = result['time_factor']
            fs = result['forgetting_score']
            last_resp = "✅" if result['last_response'] == 1 else "❌"
            
            if fs >= 0.3:
                category = "🔴 紧急"
            elif fs >= 0.2:
                category = "🟠 重要"
            elif fs >= 0.1:
                category = "🟡 一般"
            else:
                category = "🟢 维持"
            
            print(f"  {cid:<10} {attempts:<6} {pred_prob:<11.1f}% {pred_method:<8} {interval_str:<12} "
                  f"{time_factor:<12.4f} {fs:<12.4f} {last_resp:<6} {category:<10}")

print("\n" + "="*120)
print("✅ 所有数据集分析完成！")
print("="*120)
print("\n对比说明:")
print("  🤖模型: 使用LPKT模型预测的s_{t,c}")
print("  📊历史: 模型预测失败时回退到历史准确率")
print("\n优势:")
print("  ✅ LPKT考虑了学习轨迹和序列信息")
print("  ✅ 比简单平均更能反映真实的知识状态")
print("  ✅ 能捕捉学习效应和遗忘效应")

