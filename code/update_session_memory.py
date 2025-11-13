#!/usr/bin/env python3
"""
更新Session文件的Memory字段
特别处理nips_task34数据集的concept映射问题
"""

import json
import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import argparse

def load_nips_subject_mapping():
    """加载nips_task34的subject映射 (数字ID -> 名称)"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    
    if not os.path.exists(metadata_file):
        return {}
    
    df = pd.read_csv(metadata_file)
    subject_map = {}
    for _, row in df.iterrows():
        subject_id = str(row['SubjectId'])  # 转为字符串,如"210"
        name = str(row['Name']).strip()
        subject_map[subject_id] = name
    
    return subject_map

def load_memory_for_student(dataset, student_id):
    """加载学生的所有memory记录"""
    memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{student_id}.json'
    
    if not os.path.exists(memory_file):
        return None
    
    with open(memory_file) as f:
        return json.load(f)

def find_memory_records(memory_data, concept_text):
    """从memory中找到匹配concept_text的所有记录"""
    if not memory_data:
        return None
    
    memories = []
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
    return memories

def update_session_file(session_file, dataset, nips_mapping=None):
    """更新单个session文件的memory字段"""
    with open(session_file) as f:
        session = json.load(f)
    
    # 如果已经有memory,跳过
    if session.get('memory') and len(session.get('memory', [])) > 0:
        return False, "already_has_memory"
    
    student_id = session['student_id']
    concept_text_in_session = session['concept_text']
    
    # 加载该学生的memory数据
    memory_data = load_memory_for_student(dataset, student_id)
    
    if not memory_data:
        return False, "no_memory_file"
    
    # 对于nips_task34, concept_text是数字,需要映射到实际名称
    if dataset == 'nips_task34' and nips_mapping:
        # session中的concept_text是数字(如"210")
        # 映射到实际名称
        actual_concept_text = nips_mapping.get(concept_text_in_session, None)
        
        if not actual_concept_text:
            # 如果映射不到,尝试直接用concept_id
            concept_id = session.get('concept_id')
            if concept_id is not None:
                actual_concept_text = nips_mapping.get(str(concept_id), None)
        
        if not actual_concept_text:
            return False, f"no_mapping_for_{concept_text_in_session}"
    else:
        actual_concept_text = concept_text_in_session
    
    # 在memory中找到对应concept的记录
    memories = find_memory_records(memory_data, actual_concept_text)
    
    if memories is None:
        return False, "no_matching_memory"
    
    # 更新session
    session['memory'] = memories
    
    # 保存
    with open(session_file, 'w') as f:
        json.dump(session, f, indent=2)
    
    return True, None

def update_dataset(dataset):
    """更新整个数据集的session"""
    print("="*80)
    print(f"更新 {dataset.upper()} 的Session Memory")
    print("="*80)
    
    session_dir = f'/mnt/localssd/bank/session/{dataset}'
    
    if not os.path.exists(session_dir):
        print(f"  ❌ Session目录不存在: {session_dir}")
        return
    
    # 对于nips_task34,加载subject映射
    nips_mapping = None
    if dataset == 'nips_task34':
        print("  📚 加载NIPS_TASK34的Subject映射...")
        nips_mapping = load_nips_subject_mapping()
        print(f"  ✅ 加载了 {len(nips_mapping)} 个映射")
    
    # 获取所有session文件
    session_files = list(Path(session_dir).glob('*.json'))
    print(f"  📂 找到 {len(session_files)} 个session文件")
    print()
    
    # 统计
    updated = 0
    skipped = 0
    errors = {}
    
    # 更新每个文件
    for session_file in tqdm(session_files, desc=f"更新{dataset}", ncols=100):
        success, error = update_session_file(session_file, dataset, nips_mapping)
        
        if success:
            updated += 1
        else:
            skipped += 1
            if error:
                errors[error] = errors.get(error, 0) + 1
    
    # 报告结果
    print()
    print(f"✅ 成功更新: {updated} 个")
    print(f"⚠️  跳过: {skipped} 个")
    
    if errors:
        print(f"\n跳过原因:")
        for reason, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count} 个")
    print()

def main():
    parser = argparse.ArgumentParser(description='更新Session的Memory字段')
    parser.add_argument('--dataset', type=str,
                       choices=['nips_task34', 'assist2017', 'algebra2005', 'bridge2006', 'all'],
                       default='all',
                       help='数据集名称')
    
    args = parser.parse_args()
    
    if args.dataset == 'all':
        datasets = ['nips_task34', 'assist2017', 'algebra2005', 'bridge2006']
    else:
        datasets = [args.dataset]
    
    for dataset in datasets:
        update_dataset(dataset)
        print()
    
    print("="*80)
    print("✅ 所有Session更新完成！")
    print("="*80)

if __name__ == '__main__':
    main()

