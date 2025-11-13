#!/usr/bin/env python
"""
修复 nips_task34 数据集的 concept 映射
将数字 ID (如 "204") 映射到实际的 subject 名称 (如 "Algebra")
"""

import json
import pandas as pd
import os
from pathlib import Path

def load_subject_metadata():
    """加载 subject metadata 并创建 SubjectId -> Name 的映射"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    # 创建 SubjectId -> Name 的映射
    subject_mapping = {}
    for _, row in df.iterrows():
        subject_id = int(row['SubjectId'])
        name = str(row['Name']).strip()
        subject_mapping[subject_id] = name
    
    print(f"📚 加载了 {len(subject_mapping)} 个 subject 映射")
    print(f"  示例: {list(subject_mapping.items())[:5]}")
    return subject_mapping

def create_new_keyid2idx():
    """创建新的 keyid2idx.json，将数字 ID 映射到实际的 subject 名称"""
    # 1. 加载原始的 keyid2idx.json
    original_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/keyid2idx.json'
    with open(original_file, 'r') as f:
        original = json.load(f)
    
    # 2. 加载 subject metadata
    subject_mapping = load_subject_metadata()
    
    # 3. 创建新的 concepts 映射
    print("\n🔄 创建新的 concept 映射...")
    new_concepts = {}
    missing_subjects = []
    
    for concept_id_str, idx in original['concepts'].items():
        concept_id = int(concept_id_str)
        
        if concept_id in subject_mapping:
            subject_name = subject_mapping[concept_id]
            new_concepts[subject_name] = idx
        else:
            # 如果找不到对应的 subject，使用原始的数字 ID
            new_concepts[f"Subject_{concept_id}"] = idx
            missing_subjects.append(concept_id)
    
    if missing_subjects:
        print(f"  ⚠️  有 {len(missing_subjects)} 个 concept ID 在 subject_metadata 中找不到:")
        print(f"    {missing_subjects[:10]}")
    
    # 4. 创建新的 keyid2idx
    new_keyid2idx = {
        'questions': original['questions'],
        'concepts': new_concepts,
        'uid': original['uid'],
        'max_concepts': original['max_concepts']
    }
    
    # 5. 备份原始文件
    backup_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/keyid2idx.json.backup'
    if not os.path.exists(backup_file):
        with open(backup_file, 'w') as f:
            json.dump(original, f, indent=2)
        print(f"  ✅ 备份原始文件到: {backup_file}")
    
    # 6. 保存新的 keyid2idx
    with open(original_file, 'w') as f:
        json.dump(new_keyid2idx, f, indent=2)
    
    print(f"  ✅ 更新了 {len(new_concepts)} 个 concept 映射")
    print(f"  示例新映射:")
    for i, (name, idx) in enumerate(list(new_concepts.items())[:10]):
        print(f"    {idx}: {name}")
    
    return new_keyid2idx

def update_persona_files(subject_mapping):
    """更新 nips_task34 的所有 persona 文件，将 concept_text 从数字 ID 改为实际名称"""
    persona_dir = '/mnt/localssd/bank/persona/nips_task34/data'
    
    print(f"\n🔄 更新 persona 文件...")
    
    updated_count = 0
    error_count = 0
    
    persona_files = list(Path(persona_dir).glob('*.json'))
    print(f"  找到 {len(persona_files)} 个 persona 文件")
    
    for persona_file in persona_files:
        try:
            with open(persona_file, 'r') as f:
                personas = json.load(f)
            
            updated = False
            for persona in personas:
                old_text = persona['concept_text']
                
                # 如果是数字，则转换为实际的 subject 名称
                try:
                    concept_id = int(old_text)
                    if concept_id in subject_mapping:
                        persona['concept_text'] = subject_mapping[concept_id]
                        persona['keywords'] = subject_mapping[concept_id]
                        
                        # 更新 description 中的引用
                        old_desc = persona['description']
                        persona['description'] = old_desc.replace(f"'{old_text}'", f"'{subject_mapping[concept_id]}'")
                        
                        updated = True
                except (ValueError, TypeError):
                    # 如果不是数字，跳过
                    pass
            
            if updated:
                with open(persona_file, 'w') as f:
                    json.dump(personas, f, indent=2)
                updated_count += 1
        
        except Exception as e:
            print(f"  ❌ 处理文件 {persona_file.name} 时出错: {e}")
            error_count += 1
    
    print(f"  ✅ 更新了 {updated_count} 个 persona 文件")
    if error_count > 0:
        print(f"  ⚠️  {error_count} 个文件处理失败")

def update_memory_files(subject_mapping):
    """更新 nips_task34 的所有 memory 文件，将 concept_text 从数字 ID 改为实际名称"""
    memory_dir = '/mnt/localssd/bank/memory/nips_task34/data'
    
    print(f"\n🔄 更新 memory 文件...")
    
    updated_count = 0
    error_count = 0
    
    memory_files = list(Path(memory_dir).glob('*.json'))
    print(f"  找到 {len(memory_files)} 个 memory 文件")
    
    for memory_file in memory_files:
        try:
            with open(memory_file, 'r') as f:
                memories = json.load(f)
            
            updated = False
            for memory in memories:
                old_text = memory['concept_text']
                
                # 如果是数字，则转换为实际的 subject 名称
                try:
                    concept_id = int(old_text)
                    if concept_id in subject_mapping:
                        memory['concept_text'] = subject_mapping[concept_id]
                        
                        # 更新 description 中的引用
                        old_desc = memory['description']
                        memory['description'] = old_desc.replace(f"'{old_text}'", f"'{subject_mapping[concept_id]}'")
                        
                        updated = True
                except (ValueError, TypeError):
                    # 如果不是数字，跳过
                    pass
            
            if updated:
                with open(memory_file, 'w') as f:
                    json.dump(memories, f, indent=2)
                updated_count += 1
        
        except Exception as e:
            print(f"  ❌ 处理文件 {memory_file.name} 时出错: {e}")
            error_count += 1
    
    print(f"  ✅ 更新了 {updated_count} 个 memory 文件")
    if error_count > 0:
        print(f"  ⚠️  {error_count} 个文件处理失败")

def verify_fix(num_students=5):
    """验证修复效果"""
    print(f"\n✅ 验证修复效果 (前{num_students}个学生)...")
    
    for student_id in range(num_students):
        persona_file = f'/mnt/localssd/bank/persona/nips_task34/data/{student_id}.json'
        memory_file = f'/mnt/localssd/bank/memory/nips_task34/data/{student_id}.json'
        
        if not os.path.exists(persona_file):
            continue
        
        with open(persona_file, 'r') as f:
            personas = json.load(f)
        
        print(f"\n  学生 {student_id}:")
        print(f"    Persona concepts: {len(personas)} 个")
        
        # 检查是否还有数字 concept_text
        numeric_concepts = [p['concept_text'] for p in personas if p['concept_text'].isdigit()]
        if numeric_concepts:
            print(f"    ⚠️  仍有数字 concept: {numeric_concepts[:3]}")
        else:
            print(f"    ✅ 所有 concept 都已转换为文本")
        
        # 显示前几个 concept
        sample_concepts = [(p['concept_id'], p['concept_text']) for p in personas[:3]]
        for cid, ctext in sample_concepts:
            print(f"      - {cid}: {ctext}")
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memories = json.load(f)
            print(f"    Memory records: {len(memories)} 条")

if __name__ == '__main__':
    print("=" * 80)
    print("修复 NIPS_TASK34 数据集的 Concept 映射")
    print("=" * 80)
    
    # 1. 创建新的 keyid2idx.json
    new_keyid2idx = create_new_keyid2idx()
    
    # 2. 加载 subject mapping
    subject_mapping = load_subject_metadata()
    
    # 3. 更新 persona 文件
    update_persona_files(subject_mapping)
    
    # 4. 更新 memory 文件
    update_memory_files(subject_mapping)
    
    # 5. 验证修复效果
    verify_fix(num_students=5)
    
    print("\n" + "=" * 80)
    print("✅ 修复完成！")
    print("=" * 80)

