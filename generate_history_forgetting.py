#!/usr/bin/env python3
"""
生成基于历史accuracy的Forgetting Score
这是最标准的方法，所有字段都基于相同的原始数据
"""

import os
import json
import pandas as pd
import numpy as np
from collections import defaultdict
import argparse

def load_sequences(dataset_name):
    """加载所有数据（train/valid/test）"""
    data_dir = f'/mnt/localssd/pykt-toolkit/data/{dataset_name}'
    
    all_data = []
    
    # 加载train+valid
    train_valid_file = os.path.join(data_dir, 'train_valid_sequences.csv')
    if os.path.exists(train_valid_file):
        df_tv = pd.read_csv(train_valid_file)
        df_tv['split'] = 'train_valid'
        all_data.append(df_tv)
        print(f"  ✅ Train+Valid: {len(df_tv)} sequences")
    
    # 加载test
    test_file = os.path.join(data_dir, 'test_sequences.csv')
    if os.path.exists(test_file):
        df_test = pd.read_csv(test_file)
        df_test['split'] = 'test'
        all_data.append(df_test)
        print(f"  ✅ Test: {len(df_test)} sequences")
    
    if not all_data:
        raise FileNotFoundError(f"No data files found for {dataset_name}")
    
    df_all = pd.concat(all_data, ignore_index=True)
    print(f"  ✅ Total: {len(df_all)} sequences, {df_all['uid'].nunique()} unique students")
    
    return df_all

def parse_sequence_data(df_all, dataset_name):
    """解析序列数据，提取每个学生的每个concept的交互历史"""
    print(f"\n📊 解析序列数据...")
    
    # 学生-concept级别的统计
    student_concept_data = defaultdict(lambda: {
        'interactions': [],  # [(timestamp, response)]
        'concept_id': None,
        'concept_text': None
    })
    
    # 加载concept映射
    concept_map = {}
    concepts_file = f'/mnt/localssd/pykt-toolkit/data/{dataset_name}/concepts.txt'
    if os.path.exists(concepts_file):
        with open(concepts_file) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    concept_map[int(parts[0])] = parts[1]
    
    total_interactions = 0
    
    for idx, row in df_all.iterrows():
        uid = str(row['uid'])
        
        # 解析concepts, responses, timestamps
        concepts = [int(c) for c in str(row['concepts']).split(',')]
        responses = [int(r) for r in str(row['responses']).split(',')]
        
        # 解析timestamps
        if 'timestamps' in row and pd.notna(row['timestamps']):
            timestamps = [int(t) for t in str(row['timestamps']).split(',')]
        else:
            # 如果没有timestamps，使用序列索引
            timestamps = list(range(len(concepts)))
        
        # 确保长度一致
        min_len = min(len(concepts), len(responses), len(timestamps))
        concepts = concepts[:min_len]
        responses = responses[:min_len]
        timestamps = timestamps[:min_len]
        
        # 记录每个concept的交互
        for c, r, t in zip(concepts, responses, timestamps):
            if c == -1:  # 跳过无效concept
                continue
            
            key = (uid, c)
            student_concept_data[key]['interactions'].append((t, r))
            student_concept_data[key]['concept_id'] = c
            
            # 设置concept_text
            if c in concept_map:
                student_concept_data[key]['concept_text'] = concept_map[c]
            else:
                student_concept_data[key]['concept_text'] = f'concept_{c}'
            
            total_interactions += 1
    
    print(f"  ✅ Parsed {total_interactions} interactions")
    print(f"  ✅ {len(student_concept_data)} student-concept pairs")
    
    return student_concept_data

def calculate_forgetting_scores(student_concept_data, tau_days):
    """计算基于历史accuracy的forgetting score"""
    print(f"\n📈 计算Forgetting Scores (τ={tau_days} days)...")
    
    tau_minutes = tau_days * 24 * 60
    results = []
    
    for (uid, concept_id), data in student_concept_data.items():
        interactions = sorted(data['interactions'])  # 按时间排序
        
        if len(interactions) < 2:
            # 至少需要2次交互才能计算forgetting score
            continue
        
        # 计算历史accuracy (使用倒数第二次之前的所有交互)
        historical_responses = [r for t, r in interactions[:-1]]
        s_tc = sum(historical_responses) / len(historical_responses)
        
        # 最后一次交互信息
        last_time, last_response = interactions[-1]
        second_last_time, _ = interactions[-2]
        
        # 计算时间差（转换为分钟）
        if isinstance(last_time, (int, float)) and last_time > 1e9:  # 毫秒级时间戳
            delta_t = (last_time - second_last_time) / 1000 / 60  # ms -> minutes
        else:  # 序列索引或秒级
            delta_t = abs(last_time - second_last_time)
            if delta_t < 1000:  # 可能是序列索引
                delta_t = delta_t * 60  # 假设每个step是1分钟
        
        # 计算forgetting score
        time_factor = delta_t / (delta_t + tau_minutes)
        fs = (1 - s_tc) * time_factor
        
        results.append({
            'uid': uid,
            'concept_id': concept_id,
            'concept_text': data['concept_text'],
            's_tc': s_tc,
            'fs': fs,
            'delta_t': delta_t,
            'tau': tau_minutes,
            'last_response': last_response,
            'num_attempts': len(interactions)
        })
    
    print(f"  ✅ Calculated {len(results)} forgetting scores")
    
    return results

def assign_levels(results):
    """根据FS分布分配level"""
    if not results:
        return results
    
    fs_values = [r['fs'] for r in results]
    q33 = np.percentile(fs_values, 33)
    q67 = np.percentile(fs_values, 67)
    
    for r in results:
        if r['fs'] < q33:
            r['level'] = 'low'
        elif r['fs'] < q67:
            r['level'] = 'medium'
        else:
            r['level'] = 'high'
    
    return results

def save_to_bank(results, dataset_name):
    """保存到bank格式"""
    print(f"\n💾 保存到Bank...")
    
    # 转换为bank格式
    bank_data = defaultdict(dict)
    
    for r in results:
        uid = r['uid']
        concept_text = r['concept_text']
        
        bank_data[uid][concept_text] = {
            's_tc': float(r['s_tc']),
            'fs': float(r['fs']),
            'delta_t': float(r['delta_t']),
            'tau': float(r['tau']),
            'level': r['level'],
            'last_response': int(r['last_response']),
            'num_attempts': int(r['num_attempts'])
        }
    
    # 保存
    output_dir = f'/mnt/localssd/bank/forgetting/{dataset_name}'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'history.json')
    
    with open(output_file, 'w') as f:
        json.dump(bank_data, f, indent=2)
    
    print(f"  ✅ Saved: {output_file}")
    print(f"  📊 Students: {len(bank_data)}")
    print(f"  📊 Total entries: {sum(len(concepts) for concepts in bank_data.values())}")
    print(f"  📊 Avg concepts/student: {sum(len(concepts) for concepts in bank_data.values()) / len(bank_data):.1f}")

def main():
    parser = argparse.ArgumentParser(description='Generate history-based forgetting scores')
    parser.add_argument('--dataset', type=str, required=True, 
                       help='Dataset name (assist2017, nips_task34, algebra2005, bridge2algebra2006)')
    parser.add_argument('--tau', type=float, default=None,
                       help='Tau value in days (if not specified, use dataset default)')
    
    args = parser.parse_args()
    
    # Tau默认值
    tau_values = {
        'assist2017': 2.93,
        'nips_task34': 2.93,
        'algebra2005': 0.70,
        'bridge2algebra2006': 0.70,
    }
    tau = args.tau if args.tau is not None else tau_values.get(args.dataset, 2.93)
    
    print("="*100)
    print(f"📊 生成基于历史accuracy的Forgetting Score")
    print(f"   Dataset: {args.dataset}")
    print(f"   Tau: {tau} days ({tau * 24 * 60:.1f} minutes)")
    print("="*100)
    
    # 1. 加载数据
    print(f"\n📂 加载数据...")
    df_all = load_sequences(args.dataset)
    
    # 2. 解析序列数据
    student_concept_data = parse_sequence_data(df_all, args.dataset)
    
    # 3. 计算forgetting scores
    results = calculate_forgetting_scores(student_concept_data, tau)
    
    # 4. 分配levels
    results = assign_levels(results)
    
    # 5. 保存
    save_to_bank(results, args.dataset)
    
    print("\n" + "="*100)
    print("✅ 完成！")
    print("="*100)

if __name__ == '__main__':
    main()

