#!/usr/bin/env python3
"""
修复Session中Memory的description
将数字ID替换为实际的concept描述文本
"""

import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import re

def load_subject_mapping():
    """加载nips_task34的subject映射"""
    # 1. 加载concept_id -> SubjectId映射
    keyid_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/keyid2idx.json'
    with open(keyid_file) as f:
        keyid_data = json.load(f)
    
    # 反向映射: {concept_id: SubjectId}
    idx2subject = {v: k for k, v in keyid_data['concepts'].items()}
    
    # 2. 加载SubjectId -> Name映射
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    subject_id_to_name = {}
    for _, row in df.iterrows():
        subject_id = str(row['SubjectId'])
        name = str(row['Name']).strip()
        subject_id_to_name[subject_id] = name
    
    return idx2subject, subject_id_to_name

def update_memory_description(description, old_text, new_text):
    """更新description中的concept引用"""
    # 替换各种形式的数字引用
    # 例如: "understanding 209", "a 209 problem", "the 209 task"
    
    # 使用正则表达式找到所有数字引用并替换
    # 匹配模式: 单词边界 + 数字 + 单词边界
    pattern = r'\b' + re.escape(old_text) + r'\b'
    updated = re.sub(pattern, new_text, description)
    
    return updated

def fix_session_memory(session_file, idx2subject, subject_id_to_name):
    """修复单个session文件的memory descriptions"""
    with open(session_file) as f:
        session = json.load(f)
    
    # 获取该session的concept信息
    concept_id = session.get('concept_id')
    concept_text = session.get('concept_text')
    
    if concept_id is None:
        return False, "no_concept_id"
    
    # 第一步: concept_id -> SubjectId
    subject_id = idx2subject.get(concept_id)
    if not subject_id:
        return False, f"no_subject_for_concept_{concept_id}"
    
    # 第二步: SubjectId -> Name
    actual_name = subject_id_to_name.get(subject_id)
    if not actual_name:
        return False, f"no_name_for_subject_{subject_id}"
    
    # 检查memory是否存在且需要更新
    memory = session.get('memory')
    if not memory:
        return False, "no_memory"
    
    updated = False
    
    # 更新每条memory的description
    for mem in memory:
        old_desc = mem.get('description', '')
        
        # 检查是否包含SubjectId (数字)
        if re.search(r'\b' + re.escape(subject_id) + r'\b', old_desc):
            # 替换SubjectId为实际名称
            new_desc = update_memory_description(old_desc, subject_id, actual_name)
            mem['description'] = new_desc
            updated = True
    
    if not updated:
        return False, "no_update_needed"
    
    # 保存更新后的session
    with open(session_file, 'w') as f:
        json.dump(session, f, indent=2)
    
    return True, None

def main():
    print("="*80)
    print("修复NIPS_TASK34 Session Memory的Descriptions")
    print("="*80)
    
    # 加载映射
    print("📚 加载映射...")
    idx2subject, subject_id_to_name = load_subject_mapping()
    print(f"  ✅ 加载了 {len(idx2subject)} 个concept_id映射")
    print(f"  ✅ 加载了 {len(subject_id_to_name)} 个subject名称\n")
    
    # 获取所有session文件
    session_dir = Path('/mnt/localssd/bank/session/nips_task34')
    session_files = list(session_dir.glob('*.json'))
    print(f"📂 找到 {len(session_files)} 个session文件\n")
    
    # 统计
    updated = 0
    skipped = 0
    errors = {}
    
    # 处理每个文件
    for session_file in tqdm(session_files, desc="修复Memory", ncols=100):
        success, error = fix_session_memory(session_file, idx2subject, subject_id_to_name)
        
        if success:
            updated += 1
        else:
            skipped += 1
            if error:
                errors[error] = errors.get(error, 0) + 1
    
    # 报告结果
    print(f"\n{'='*80}")
    print("✅ 修复完成！")
    print(f"{'='*80}")
    print(f"  成功更新: {updated} 个")
    print(f"  跳过: {skipped} 个")
    
    if errors:
        print(f"\n跳过原因:")
        for reason, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count} 个")
    
    print()
    
    # 验证示例
    print("验证示例:")
    sample_files = [session_files[13], session_files[126], session_files[0]]  # 学生14, 127, 0
    
    for session_file in sample_files:
        if not session_file.exists():
            continue
            
        with open(session_file) as f:
            session = json.load(f)
        
        student_id = session['student_id']
        concept_text = session['concept_text']
        memory = session.get('memory', [])
        
        print(f"\n  学生 {student_id:5s} (concept: {concept_text})")
        if memory:
            print(f"    前2条memory:")
            for i, mem in enumerate(memory[:2]):
                desc = mem['description'][:60] + '...' if len(mem['description']) > 60 else mem['description']
                print(f"      {i+1}. {desc}")

if __name__ == '__main__':
    main()

