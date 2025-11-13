#!/usr/bin/env python3
"""生成基于历史accuracy的Forgetting Score V2 - 自动计算合理的tau"""
import os, json, pandas as pd, numpy as np
from collections import defaultdict
import argparse

def load_sequences(dataset_name):
    data_dir = f'/mnt/localssd/pykt-toolkit/data/{dataset_name}'
    all_data = []
    train_valid_file = os.path.join(data_dir, 'train_valid_sequences.csv')
    if os.path.exists(train_valid_file):
        df_tv = pd.read_csv(train_valid_file)
        all_data.append(df_tv)
        print(f"  ✅ Train+Valid: {len(df_tv)}")
    test_file = os.path.join(data_dir, 'test_sequences.csv')
    if os.path.exists(test_file):
        df_test = pd.read_csv(test_file)
        all_data.append(df_test)
        print(f"  ✅ Test: {len(df_test)}")
    df_all = pd.concat(all_data, ignore_index=True)
    print(f"  ✅ Total: {len(df_all)}, {df_all['uid'].nunique()} students")
    return df_all

def parse_sequence_data(df_all, dataset_name):
    student_concept_data = defaultdict(lambda: {'interactions': [], 'concept_id': None, 'concept_text': None})
    concept_map = {}
    concepts_file = f'/mnt/localssd/pykt-toolkit/data/{dataset_name}/concepts.txt'
    if os.path.exists(concepts_file):
        with open(concepts_file) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    concept_map[int(parts[0])] = parts[1]
    for idx, row in df_all.iterrows():
        uid = str(row['uid'])
        concepts = [int(c) for c in str(row['concepts']).split(',')]
        responses = [int(r) for r in str(row['responses']).split(',')]
        if 'timestamps' in row and pd.notna(row['timestamps']):
            timestamps = [int(t) for t in str(row['timestamps']).split(',')]
        else:
            timestamps = list(range(len(concepts)))
        min_len = min(len(concepts), len(responses), len(timestamps))
        concepts, responses, timestamps = concepts[:min_len], responses[:min_len], timestamps[:min_len]
        for c, r, t in zip(concepts, responses, timestamps):
            if c == -1: continue
            key = (uid, c)
            student_concept_data[key]['interactions'].append((t, r))
            student_concept_data[key]['concept_id'] = c
            student_concept_data[key]['concept_text'] = concept_map.get(c, f'concept_{c}')
    print(f"  ✅ {len(student_concept_data)} student-concept pairs")
    return student_concept_data

def calculate_optimal_tau(student_concept_data):
    print(f"\n📈 计算最优Tau...")
    all_delta_t = []
    for (uid, concept_id), data in student_concept_data.items():
        interactions = sorted(data['interactions'])
        if len(interactions) < 2: continue
        last_time, _ = interactions[-1]
        second_last_time, _ = interactions[-2]
        if isinstance(last_time, (int, float)) and last_time > 1e9:
            delta_t = (last_time - second_last_time) / 1000
        else:
            delta_t = abs(last_time - second_last_time)
            if delta_t < 1000: delta_t = delta_t * 60
        if delta_t > 0: all_delta_t.append(delta_t)
    tau = np.median(all_delta_t) if all_delta_t else 60.0
    print(f"  Median delta_t: {tau:.2f}秒 = {tau/60:.2f}分钟")
    return tau

def calculate_forgetting_scores(student_concept_data, tau_seconds):
    print(f"\n📈 计算FS (τ={tau_seconds:.2f}秒)...")
    results = []
    for (uid, concept_id), data in student_concept_data.items():
        interactions = sorted(data['interactions'])
        if len(interactions) < 2: continue
        historical_responses = [r for t, r in interactions[:-1]]
        s_tc = sum(historical_responses) / len(historical_responses)
        last_time, last_response = interactions[-1]
        second_last_time, _ = interactions[-2]
        if isinstance(last_time, (int, float)) and last_time > 1e9:
            delta_t = (last_time - second_last_time) / 1000
        else:
            delta_t = abs(last_time - second_last_time)
            if delta_t < 1000: delta_t = delta_t * 60
        fs = (1 - s_tc) * (delta_t / (delta_t + tau_seconds))
        results.append({'uid': uid, 'concept_id': concept_id, 'concept_text': data['concept_text'],
                       's_tc': s_tc, 'fs': fs, 'delta_t': delta_t, 'tau': tau_seconds,
                       'last_response': last_response, 'num_attempts': len(interactions)})
    fs_values = [r['fs'] for r in results]
    print(f"  ✅ {len(results)} scores. FS range: [{np.min(fs_values):.4f}, {np.max(fs_values):.4f}], median={np.median(fs_values):.4f}")
    return results

def assign_levels(results):
    fs_values = [r['fs'] for r in results]
    q33, q67 = np.percentile(fs_values, 33), np.percentile(fs_values, 67)
    print(f"\n📊 Level: low<{q33:.4f}<medium<{q67:.4f}<high")
    for r in results:
        r['level'] = 'low' if r['fs'] < q33 else ('medium' if r['fs'] < q67 else 'high')
    return results

def save_to_bank(results, dataset_name):
    bank_data = defaultdict(dict)
    for r in results:
        bank_data[r['uid']][r['concept_text']] = {
            's_tc': float(r['s_tc']), 'fs': float(r['fs']),
            'delta_t': float(r['delta_t']), 'tau': float(r['tau']),
            'level': r['level'], 'last_response': int(r['last_response']),
            'num_attempts': int(r['num_attempts'])
        }
    output_dir = f'/mnt/localssd/bank/forgetting/{dataset_name}'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'history.json')
    with open(output_file, 'w') as f:
        json.dump(bank_data, f, indent=2)
    print(f"  ✅ Saved: {output_file}, {len(bank_data)} students")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--tau', type=float, default=None)
    args = parser.parse_args()
    print("="*100 + f"\n📊 生成History FS V2 - {args.dataset}\n" + "="*100)
    df_all = load_sequences(args.dataset)
    student_concept_data = parse_sequence_data(df_all, args.dataset)
    tau = args.tau if args.tau else calculate_optimal_tau(student_concept_data)
    results = calculate_forgetting_scores(student_concept_data, tau)
    results = assign_levels(results)
    save_to_bank(results, args.dataset)
    print("\n" + "="*100 + "\n✅ 完成！\n" + "="*100)
