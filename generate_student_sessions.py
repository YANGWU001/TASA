#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为每个学生生成Session数据
- 选择interaction次数为中位数的concept
- 包含persona, memory, delta_t, 五种method的s_tc/fs/level
"""

import os
import json
import numpy as np
from collections import defaultdict
from tqdm import tqdm
import argparse

# 数据集配置
DATASET_MAPPING = {
    'assist2017': 'assist2017',
    'nips_task34': 'nips_task34',
    'algebra2005': 'algebra2005',
    'bridge2006': 'bridge2algebra2006'
}

def load_concept_mapping(dataset):
    """加载concept ID到文本的映射"""
    actual_dataset = DATASET_MAPPING.get(dataset, dataset)
    keyid_file = f'/mnt/localssd/pykt-toolkit/data/{actual_dataset}/keyid2idx.json'
    
    if not os.path.exists(keyid_file):
        return {}
    
    with open(keyid_file) as f:
        data = json.load(f)
    
    # concepts字段：{concept_text: concept_id}
    concepts_dict = data.get('concepts', {})
    
    # 反向映射：{concept_id: concept_text}
    id_to_text = {v: k for k, v in concepts_dict.items()}
    
    return id_to_text

def concept_id_to_text(concept_key, id_to_text_map):
    """将concept_X格式转换为实际文本"""
    # concept_key格式: "concept_0", "concept_1", etc.
    if concept_key.startswith('concept_'):
        try:
            concept_id = int(concept_key.split('_')[1])
            return id_to_text_map.get(concept_id, concept_key)
        except:
            return concept_key
    return concept_key

def load_student_interactions(dataset):
    """加载学生的interaction数据，统计每个concept的次数"""
    # 从overall.json中加载数据
    overall_file = f'/mnt/localssd/bank/forgetting/{dataset}/overall.json'
    
    if not os.path.exists(overall_file):
        print(f"  ❌ Overall.json不存在: {overall_file}")
        return {}
    
    with open(overall_file) as f:
        overall_data = json.load(f)
    
    # 统计每个学生每个concept的interaction次数
    student_concept_attempts = {}
    
    for uid, concepts in overall_data.items():
        student_concept_attempts[uid] = {}
        
        for concept_text, data in concepts.items():
            num_attempts = data.get('num_attempts', 0)
            if num_attempts > 0:
                student_concept_attempts[uid][concept_text] = num_attempts
    
    return student_concept_attempts

def select_median_concept(student_attempts):
    """选择interaction次数为中位数的concept"""
    if not student_attempts:
        return None
    
    # 获取所有attempt次数
    attempts_list = list(student_attempts.values())
    
    # 计算中位数
    median_attempts = np.median(attempts_list)
    
    # 找到最接近中位数的concept
    closest_concept = None
    min_diff = float('inf')
    
    for concept, attempts in student_attempts.items():
        diff = abs(attempts - median_attempts)
        if diff < min_diff:
            min_diff = diff
            closest_concept = concept
    
    return closest_concept

def load_persona(dataset, uid, concept_text):
    """加载学生在该concept上的persona"""
    persona_file = f'/mnt/localssd/bank/persona/{dataset}/data/{uid}.json'
    
    if not os.path.exists(persona_file):
        return None
    
    with open(persona_file) as f:
        persona_data = json.load(f)
    
    # persona_data是一个list，需要找到对应concept的记录
    if isinstance(persona_data, list):
        for item in persona_data:
            if item.get('concept_text') == concept_text:
                return {
                    'description': item.get('description'),
                    'keywords': item.get('keywords'),
                    'stats': item.get('stats')
                }
    
    return None

def load_memory(dataset, uid, concept_text):
    """加载学生在该concept上的memory，返回按timestamp排序的description列表"""
    memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{uid}.json'
    
    if not os.path.exists(memory_file):
        return None
    
    with open(memory_file) as f:
        memory_data = json.load(f)
    
    # memory是一个list，需要找到对应concept的所有记录
    memories = []
    
    if isinstance(memory_data, list):
        for mem in memory_data:
            if mem.get('concept_text') == concept_text:
                memories.append({
                    'description': mem.get('description'),
                    'timestamp': mem.get('timestamp'),
                    'response': mem.get('response')
                })
    
    if not memories:
        return None
    
    # 按timestamp排序
    memories.sort(key=lambda x: x.get('timestamp', 0))
    
    # 返回description列表（保留timestamp和response用于参考）
    return memories

def load_forgetting(dataset, uid, concept_text):
    """加载学生在该concept上的forgetting信息"""
    overall_file = f'/mnt/localssd/bank/forgetting/{dataset}/overall.json'
    
    if not os.path.exists(overall_file):
        return None
    
    with open(overall_file) as f:
        overall_data = json.load(f)
    
    if uid not in overall_data:
        return None
    
    if concept_text not in overall_data[uid]:
        return None
    
    concept_data = overall_data[uid][concept_text]
    
    # 提取需要的信息
    delta_t_minutes = concept_data.get('delta_t')
    delta_t_days = delta_t_minutes / 60 / 24 if delta_t_minutes is not None else None
    
    methods_data = {}
    for method in ['history', 'lpkt', 'dkt', 'akt', 'simplekt']:
        if method in concept_data.get('methods', {}):
            methods_data[method] = concept_data['methods'][method]
    
    return {
        'delta_t_days': delta_t_days,
        'delta_t_minutes': delta_t_minutes,
        'tau_minutes': concept_data.get('tau'),
        'last_response': concept_data.get('last_response'),
        'num_attempts': concept_data.get('num_attempts'),
        'methods': methods_data
    }

def generate_session_for_dataset(dataset):
    """为整个数据集生成session"""
    print("="*100)
    print(f"📚 为 {dataset.upper()} 生成Student Sessions")
    print("="*100)
    print()
    
    # 1. 加载concept映射
    print("📂 加载Concept映射...")
    id_to_text_map = load_concept_mapping(dataset)
    print(f"  ✅ 加载了 {len(id_to_text_map)} 个concept映射")
    print()
    
    # 2. 加载学生的interaction统计
    print("📂 加载学生Interaction数据...")
    student_attempts = load_student_interactions(dataset)
    
    if not student_attempts:
        print("❌ 没有找到数据，退出")
        return
    
    print(f"  ✅ 加载了 {len(student_attempts)} 个学生")
    print()
    
    # 3. 为每个学生生成session
    print("🎯 生成Student Sessions...")
    print()
    
    sessions = {}
    skipped_students = []
    
    for uid in tqdm(student_attempts.keys(), desc="生成Sessions", ncols=100):
        # 选择中位数concept (格式: concept_X)
        median_concept_key = select_median_concept(student_attempts[uid])
        
        if not median_concept_key:
            skipped_students.append(uid)
            continue
        
        # 从concept_X中提取concept_id数字
        try:
            concept_id = int(median_concept_key.split('_')[1])
        except:
            skipped_students.append(uid)
            continue
        
        # 将concept_id转换为实际文本
        concept_text = id_to_text_map.get(concept_id, median_concept_key)
        
        # 加载persona (使用实际文本)
        persona = load_persona(dataset, uid, concept_text)
        
        # 加载memory (使用实际文本)
        memory = load_memory(dataset, uid, concept_text)
        
        # 加载forgetting信息 (使用原始concept_X格式)
        forgetting = load_forgetting(dataset, uid, median_concept_key)
        
        if not forgetting:
            skipped_students.append(uid)
            continue
        
        # 构建session数据
        session_data = {
            'student_id': uid,
            'concept_id': concept_id,  # 使用数字ID
            'concept_text': concept_text,
            'persona': persona,
            'memory': memory,
            'delta_t_days': forgetting['delta_t_days'],
            'delta_t_minutes': forgetting['delta_t_minutes'],
            'tau_minutes': forgetting['tau_minutes'],
            'last_response': forgetting['last_response'],
            'num_attempts': forgetting['num_attempts'],
            'methods': forgetting['methods']
        }
        
        sessions[uid] = session_data
    
    print()
    print(f"✅ 成功生成 {len(sessions)} 个sessions")
    if skipped_students:
        print(f"⚠️  跳过 {len(skipped_students)} 个学生 (缺少数据)")
    print()
    
    # 3. 保存sessions
    output_dir = f'/mnt/localssd/bank/session/{dataset}'
    os.makedirs(output_dir, exist_ok=True)
    
    print("💾 保存Sessions...")
    
    for uid, session_data in tqdm(sessions.items(), desc="保存文件", ncols=100):
        output_file = os.path.join(output_dir, f'{uid}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    print()
    
    # 4. 统计信息
    print("📊 统计信息:")
    print(f"  学生总数: {len(sessions)}")
    
    # 统计delta_t分布
    delta_t_days = [s['delta_t_days'] for s in sessions.values() if s['delta_t_days'] is not None]
    if delta_t_days:
        print(f"  Delta_t (天):")
        print(f"    中位数: {np.median(delta_t_days):.2f}")
        print(f"    平均值: {np.mean(delta_t_days):.2f}")
        print(f"    范围: {np.min(delta_t_days):.2f} - {np.max(delta_t_days):.2f}")
    
    # 统计num_attempts分布
    num_attempts = [s['num_attempts'] for s in sessions.values() if s['num_attempts'] is not None]
    if num_attempts:
        print(f"  Attempts (次数):")
        print(f"    中位数: {np.median(num_attempts):.0f}")
        print(f"    平均值: {np.mean(num_attempts):.1f}")
        print(f"    范围: {int(np.min(num_attempts))} - {int(np.max(num_attempts))}")
    
    print()
    
    # 5. 显示示例
    if sessions:
        sample_uid = list(sessions.keys())[0]
        sample_data = sessions[sample_uid]
        
        print("📋 示例Session:")
        print(f"  学生ID: {sample_data['student_id']}")
        print(f"  Concept ID: {sample_data['concept_id']}")
        print(f"  Concept Text: {sample_data['concept_text']}")
        
        if sample_data['persona']:
            print(f"  Persona:")
            print(f"    Description: {sample_data['persona'].get('description', 'N/A')[:100]}...")
            print(f"    Stats: {sample_data['persona'].get('stats', 'N/A')}")
        else:
            print(f"  Persona: N/A")
        
        if sample_data['memory']:
            print(f"  Memory ({len(sample_data['memory'])} 条记录):")
            for i, mem in enumerate(sample_data['memory'][:3], 1):
                print(f"    {i}. {mem['description'][:60]}...")
            if len(sample_data['memory']) > 3:
                print(f"    ... (还有 {len(sample_data['memory']) - 3} 条记录)")
        else:
            print(f"  Memory: N/A")
        
        print(f"  Delta_t: {sample_data['delta_t_days']:.2f} 天")
        print(f"  Attempts: {sample_data['num_attempts']}")
        print(f"  Last Response: {sample_data['last_response']}")
        print(f"  Methods:")
        for method, values in sample_data['methods'].items():
            print(f"    {method:10} - s_tc={values['s_tc']:.4f}, fs={values['fs']:.4f}, level={values.get('level', 'N/A')}")
    
    print()
    print(f"💾 保存位置: {output_dir}/")
    
    # 统计文件大小
    total_size = sum(os.path.getsize(os.path.join(output_dir, f'{uid}.json')) 
                     for uid in sessions.keys())
    print(f"📊 总大小: {total_size / 1024 / 1024:.2f}MB")

def main():
    parser = argparse.ArgumentParser(description='为每个学生生成Session数据')
    parser.add_argument('--dataset', type=str, 
                       choices=['assist2017', 'nips_task34', 'algebra2005', 'bridge2006', 'all'],
                       default='all',
                       help='数据集名称 (默认: all)')
    
    args = parser.parse_args()
    
    if args.dataset == 'all':
        datasets = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']
    else:
        datasets = [args.dataset]
    
    for dataset in datasets:
        generate_session_for_dataset(dataset)
        print()
    
    print("="*100)
    print("✅ 所有Session生成完成！")
    print("="*100)
    print()
    print("查看生成的文件:")
    print("  ls -lh /mnt/localssd/bank/session/*/")
    print()
    print("示例:")
    print("  cat /mnt/localssd/bank/session/assist2017/0.json")

if __name__ == '__main__':
    main()

