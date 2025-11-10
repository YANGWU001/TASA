#!/usr/bin/env python3
"""
修复nips_task34 session文件中的concept_text和persona
将数字ID更新为实际的subject描述
"""

import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def load_subject_mapping():
    """加载subject映射"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    subject_map = {}
    for _, row in df.iterrows():
        subject_id = str(row['SubjectId'])
        name = str(row['Name']).strip()
        subject_map[subject_id] = name
    
    return subject_map

def main():
    print("="*80)
    print("修复NIPS_TASK34 Session的Concept Text")
    print("="*80)
    
    # 加载映射
    print("📚 加载Subject映射...")
    subject_map = load_subject_mapping()
    print(f"  ✅ 加载了 {len(subject_map)} 个映射\n")
    
    # 获取所有session文件
    session_dir = Path('/mnt/localssd/bank/session/nips_task34')
    session_files = list(session_dir.glob('*.json'))
    print(f"📂 找到 {len(session_files)} 个session文件\n")
    
    updated_count = 0
    already_text = 0
    no_mapping = 0
    
    for session_file in tqdm(session_files, desc="更新文件", ncols=100):
        with open(session_file) as f:
            session = json.load(f)
        
        concept_text = session['concept_text']
        
        # 如果已经是文本，跳过
        if not concept_text.isdigit():
            already_text += 1
            continue
        
        # 查找映射
        actual_text = subject_map.get(concept_text)
        
        if not actual_text:
            no_mapping += 1
            continue
        
        # 更新concept_text
        session['concept_text'] = actual_text
        
        # 更新persona中的concept_text和keywords (如果存在)
        if session.get('persona'):
            if session['persona'].get('description'):
                # 更新description中的引用
                old_desc = session['persona']['description']
                session['persona']['description'] = old_desc.replace(f"'{concept_text}'", f"'{actual_text}'")
            
            if session['persona'].get('keywords'):
                session['persona']['keywords'] = actual_text
        
        # 保存
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
        
        updated_count += 1
    
    print(f"\n{'='*80}")
    print("✅ 更新完成！")
    print(f"{'='*80}")
    print(f"  成功更新: {updated_count} 个")
    print(f"  已是文本: {already_text} 个")
    if no_mapping > 0:
        print(f"  无映射: {no_mapping} 个")
    print()
    
    # 显示示例
    print("验证示例 (前5个):")
    for session_file in list(session_files)[:5]:
        with open(session_file) as f:
            session = json.load(f)
        
        student_id = session['student_id']
        concept_text = session['concept_text']
        is_digit = "❌ 数字" if concept_text.isdigit() else "✅ 文本"
        
        print(f"  学生 {student_id:5s}: {concept_text:40s} {is_digit}")

if __name__ == '__main__':
    main()

