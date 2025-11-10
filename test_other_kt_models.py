#!/usr/bin/env python
"""
测试其他KT模型（simpleKT, DKT, AKT）用于Forgetting Score计算
"""

import os
import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import random
from datetime import timedelta

# 设置随机种子
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# 导入模型加载函数
from pykt.models.init_model import init_model

# 数据集配置
DATASETS = {
    'assist2017': {
        'name': 'ASSISTments2017',
        'data_path': '/mnt/localssd/pykt-toolkit/data/assist2017',
        'tau_days': 3.21,
        'models': {
            'simplekt': '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_simplekt_qid_saved_model_42_0_0.1_256_256_2_4_0.5_0.5_0.5_50_256_256_4_2_0.0001_1_0',
            'dkt': '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_dkt_qid_saved_model_42_0_0.2_200_0.001_1_0',
            'akt': '/mnt/localssd/pykt-toolkit/examples/saved_model/assist2017_akt_qid_saved_model_3407_0_0.2_256_512_8_4_0.0001_1_0',
        }
    },
}

def load_model(model_name, model_path, num_q, num_c, device):
    """加载指定的KT模型"""
    config_path = os.path.join(model_path, 'config.json')
    
    # 尝试多个可能的checkpoint文件名
    checkpoint_names = ['qid_model.ckpt', 'model.ckpt', 'best_model.ckpt']
    checkpoint_path = None
    for name in checkpoint_names:
        path = os.path.join(model_path, name)
        if os.path.exists(path):
            checkpoint_path = path
            break
    
    if not checkpoint_path:
        print(f"  ❌ 未找到checkpoint文件")
        return None
    
    # 读取配置
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    model_config = config.get('model_config', {})
    params = config.get('params', {})
    data_config = {
        'num_q': num_q,
        'num_c': num_c,
        'emb_path': '',
    }
    
    try:
        # 定义训练相关的参数（不是模型架构参数）
        training_params = {
            'learning_rate', 'use_wandb', 'add_uuid', 'batch_size', 
            'num_epochs', 'optimizer', 'seq_len', 'emb_type', 'emb_path',
            'dataset_name', 'model_name', 'save_dir', 'seed', 'fold'
        }
        
        # 只保留模型架构参数
        clean_model_config = {k: v for k, v in model_config.items() 
                              if k not in training_params}
        
        print(f"  模型参数: {list(clean_model_config.keys())}")
        
        # 使用init_model函数
        model = init_model(model_name, clean_model_config, data_config, emb_type='qid')
        
        if model is None:
            print(f"  ❌ init_model返回None")
            return None
        
        # 加载权重
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint, strict=False)
        model.to(device)
        model.eval()
        
        print(f"  ✅ 成功加载 {model_name.upper()} 模型")
        return model
        
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def predict_with_model(model, model_name, device, questions, concepts, responses, num_q, num_c):
    """使用KT模型预测"""
    if len(questions) < 2:
        return None
    
    try:
        # 准备输入（不包括最后一次）
        q_seq = questions[:-1]
        c_seq = concepts[:-1]
        r_seq = responses[:-1]
        
        # 检查ID范围
        if max(q_seq) >= num_q or max(c_seq) >= num_c:
            return None
        
        # 转换为tensor
        q_tensor = torch.LongTensor([q_seq]).to(device)
        c_tensor = torch.LongTensor([c_seq]).to(device)
        r_tensor = torch.LongTensor([r_seq]).to(device)
        
        # 构建shifted版本
        qshft = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), q_tensor[:, :-1]], dim=1)
        cshft = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), c_tensor[:, :-1]], dim=1)
        rshft = torch.cat([torch.zeros(1, 1, dtype=torch.long).to(device), r_tensor[:, :-1]], dim=1)
        
        # 拼接
        cq = torch.cat([q_tensor[:, 0:1], qshft], dim=1)
        cc = torch.cat([c_tensor[:, 0:1], cshft], dim=1)
        cr = torch.cat([r_tensor[:, 0:1], rshft], dim=1)
        
        with torch.no_grad():
            if model_name == 'simplekt':
                # SimpleKT使用dcur字典
                dcur = {
                    'qseqs': q_tensor,
                    'cseqs': c_tensor,
                    'rseqs': r_tensor,
                    'shft_qseqs': qshft,
                    'shft_cseqs': cshft,
                    'shft_rseqs': rshft,
                }
                y = model(dcur)
                y = y[:, 1:]  # 跳过第一个
                
            elif model_name == 'dkt':
                # DKT: y = model(cc, cr, cq)
                y = model(cc.long(), cr.long(), cq.long())
                y = y[:, 1:]
                
            elif model_name == 'akt':
                # AKT: y, reg_loss = model(cc, cr, cq)
                y, reg_loss = model(cc.long(), cr.long(), cq.long())
                y = y[:, 1:]
            
            # 获取最后一个预测
            pred_prob = torch.sigmoid(y[0, -1]).item()
            return pred_prob
            
    except Exception as e:
        # print(f"    ⚠️ {model_name} 预测失败: {e}")
        return None

def test_single_student(dataset_key, model_name, student_id=None):
    """测试单个学生"""
    dataset_info = DATASETS[dataset_key]
    
    print(f"\n{'='*100}")
    print(f"数据集: {dataset_info['name']} | 模型: {model_name.upper()}")
    print(f"{'='*100}")
    
    # 加载数据
    data_file = os.path.join(dataset_info['data_path'], 'train_valid_sequences.csv')
    df = pd.read_csv(data_file)
    
    # 获取num_q和num_c
    all_questions = []
    all_concepts = []
    for _, row in df.iterrows():
        questions = list(map(int, str(row['questions']).split(',')))
        concepts = list(map(int, str(row['concepts']).split(',')))
        all_questions.extend(questions)
        all_concepts.extend(concepts)
    
    num_q = max(all_questions) + 1
    num_c = max(all_concepts) + 1
    
    print(f"数据统计: num_q={num_q}, num_c={num_c}, 学生数={len(df)}")
    
    # 加载模型
    device = torch.device('cpu')
    model_path = dataset_info['models'][model_name]
    model = load_model(model_name, model_path, num_q, num_c, device)
    
    if model is None:
        return
    
    # 选择一个学生
    if student_id is None:
        # 选择有多个concepts的学生
        valid_students = []
        for idx, row in df.iterrows():
            concepts = list(map(int, str(row['concepts']).split(',')))
            if len(set(concepts)) >= 5:  # 至少5个不同的concepts
                valid_students.append(idx)
        
        if not valid_students:
            print("  ❌ 没有找到合适的学生")
            return
        
        student_idx = random.choice(valid_students[:50])
    else:
        student_idx = df[df['uid'] == student_id].index[0]
    
    row = df.iloc[student_idx]
    uid = row['uid']
    
    print(f"\n测试学生: {uid}")
    print(f"{'-'*100}")
    
    # 解析数据
    questions = list(map(int, str(row['questions']).split(',')))
    concepts = list(map(int, str(row['concepts']).split(',')))
    responses = list(map(int, str(row['responses']).split(',')))
    timestamps = list(map(int, str(row['timestamps']).split(',')))
    
    # 按concept分组
    concept_data = {}
    for i in range(len(concepts)):
        c = concepts[i]
        if c not in concept_data:
            concept_data[c] = {
                'questions': [],
                'responses': [],
                'timestamps': [],
                'indices': []
            }
        concept_data[c]['questions'].append(questions[i])
        concept_data[c]['responses'].append(responses[i])
        concept_data[c]['timestamps'].append(timestamps[i])
        concept_data[c]['indices'].append(i)
    
    # 计算每个concept的FS
    tau_minutes = dataset_info['tau_days'] * 24 * 60
    
    results = []
    success_count = 0
    fallback_count = 0
    
    for concept, data in concept_data.items():
        if len(data['indices']) < 2:
            continue
        
        # 获取最后两次的索引
        last_idx = data['indices'][-1]
        second_last_idx = data['indices'][-2]
        
        # 时间间隔
        delta_t = (data['timestamps'][-1] - data['timestamps'][-2]) / (1000 * 60)  # 转换为分钟
        
        # 使用模型预测s_t,c（使用到倒数第二次的所有数据）
        seq_end_idx = second_last_idx + 1
        q_seq = questions[:seq_end_idx]
        c_seq = concepts[:seq_end_idx]
        r_seq = responses[:seq_end_idx]
        
        s_tc = predict_with_model(model, model_name, device, q_seq, c_seq, r_seq, num_q, num_c)
        
        if s_tc is None:
            # Fallback到历史准确率
            s_tc = sum(data['responses'][:-1]) / len(data['responses'][:-1]) if len(data['responses']) > 1 else 0.5
            method = '📊历史'
            fallback_count += 1
        else:
            method = f'🤖{model_name}'
            success_count += 1
        
        # 计算FS
        time_factor = delta_t / (delta_t + tau_minutes)
        fs = (1 - s_tc) * time_factor
        
        results.append({
            'concept': concept,
            'count': len(data['indices']),
            's_tc': s_tc,
            'method': method,
            'delta_t': delta_t,
            'time_factor': time_factor,
            'fs': fs,
            'last_correct': data['responses'][-1] == 1,
        })
    
    # 排序并显示
    results.sort(key=lambda x: x['fs'], reverse=True)
    
    print(f"\nForgetting Score统计:")
    print(f"  模型预测成功: {success_count}个 ({success_count*100/(success_count+fallback_count):.1f}%)")
    print(f"  回退到历史: {fallback_count}个 ({fallback_count*100/(success_count+fallback_count):.1f}%)")
    
    if results:
        fs_values = [r['fs'] for r in results]
        print(f"  平均FS: {np.mean(fs_values):.4f}")
        print(f"  标准差: {np.std(fs_values):.4f}")
        print(f"  范围: [{np.min(fs_values):.4f}, {np.max(fs_values):.4f}]")
    
    print(f"\n前10个最需要复习的Concepts:")
    print(f"  {'Concept':<10} {'次数':<8} {'预测概率':<12} {'方法':<15} {'间隔':<15} {'FS':<10} {'最后':<8}")
    print(f"  {'-'*90}")
    
    for r in results[:10]:
        delta_str = format_time_interval(r['delta_t'])
        last_str = '✅' if r['last_correct'] else '❌'
        print(f"  {r['concept']:<10} {r['count']:<8} {r['s_tc']*100:<11.1f}% {r['method']:<15} "
              f"{delta_str:<15} {r['fs']:<10.4f} {last_str:<8}")

def format_time_interval(minutes):
    """格式化时间间隔"""
    if minutes < 1:
        return f"{minutes*60:.0f}s"
    elif minutes < 60:
        return f"{minutes:.1f}m"
    elif minutes < 1440:
        return f"{minutes/60:.1f}h"
    else:
        return f"{minutes/1440:.1f}d"

if __name__ == '__main__':
    print("="*100)
    print("测试其他KT模型（simpleKT, DKT, AKT）用于Forgetting Score预测")
    print("="*100)
    
    # 测试所有三个模型
    for model_name in ['simplekt', 'dkt', 'akt']:
        test_single_student('assist2017', model_name)
    
    print(f"\n{'='*100}")
    print("✅ 测试完成！")
    print(f"{'='*100}")

