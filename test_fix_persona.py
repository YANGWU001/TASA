#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 persona 修复脚本（只处理学生 2-5）"""

import os
import json
import numpy as np
import pandas as pd
import re

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel


def load_subject_mapping():
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    subject_map = {}
    for _, row in df.iterrows():
        subject_map[str(row['SubjectId'])] = row['Name']
    print(f"✅ 加载了 {len(subject_map)} 个 Subject 映射")
    print(f"   示例: 204 -> {subject_map.get('204', 'N/A')}")
    print(f"   示例: 209 -> {subject_map.get('209', 'N/A')}")
    return subject_map


def replace_text(text, subject_map):
    result = text
    for subject_id in sorted(subject_map.keys(), key=lambda x: len(x), reverse=True):
        subject_name = subject_map[subject_id]
        pattern = r"'" + re.escape(subject_id) + r"'"
        result = re.sub(pattern, f"'{subject_name}'", result)
    return result


print("=" * 80)
print("测试 Persona 修复（学生 2-5）")
print("=" * 80)
print()

subject_map = load_subject_mapping()
print()

print("🤖 加载 BGE 模型...")
bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
print("  ✅ BGE 模型就绪")
print()

for student_id in [2, 3, 4, 5]:
    print(f"\n{'='*80}")
    print(f"学生 {student_id}")
    print(f"{'='*80}")
    
    persona_file = f'/mnt/localssd/bank/persona/nips_task34/data/{student_id}.json'
    
    with open(persona_file, 'r') as f:
        personas = json.load(f)
    
    print(f"  原始 personas: {len(personas)} 条")
    
    # 显示前2条的原始数据
    for i, p in enumerate(personas[:2]):
        print(f"\n  原始 Persona {i}:")
        print(f"    concept_text: '{p['concept_text']}'")
        print(f"    description: {p['description'][:60]}...")
    
    # 替换
    updated = 0
    for persona in personas:
        old_text = persona['concept_text']
        if old_text.strip().isdigit():
            new_text = subject_map.get(old_text.strip(), old_text)
            persona['concept_text'] = new_text
            persona['keywords'] = new_text
            updated += 1
        
        old_desc = persona['description']
        new_desc = replace_text(old_desc, subject_map)
        persona['description'] = new_desc
        
        if 'embedding' in persona:
            del persona['embedding']
    
    print(f"\n  更新了 {updated} 个 concept_text")
    
    # 显示更新后的数据
    for i, p in enumerate(personas[:2]):
        print(f"\n  更新后 Persona {i}:")
        print(f"    concept_text: '{p['concept_text']}'")
        print(f"    description: {p['description'][:60]}...")
    
    # 保存 JSON
    with open(persona_file, 'w') as f:
        json.dump(personas, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ JSON 已保存")
    
    # 计算并保存 embeddings
    descriptions = [p['description'] for p in personas]
    keywords = [p['keywords'] for p in personas]
    
    desc_emb = bge_model.encode(descriptions, batch_size=128)
    kw_emb = bge_model.encode(keywords, batch_size=128)
    
    emb_dir = '/mnt/localssd/bank/persona/nips_task34/embeddings'
    np.savez_compressed(f'{emb_dir}/{student_id}_description.npz',
                       embeddings=np.array(desc_emb, dtype=np.float16))
    np.savez_compressed(f'{emb_dir}/{student_id}_keywords.npz',
                       embeddings=np.array(kw_emb, dtype=np.float16))
    
    print(f"  ✅ Embeddings 已保存到 .npz")

print(f"\n{'='*80}")
print("✅ 测试完成！")
print(f"{'='*80}")
