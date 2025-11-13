#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 nips_task34 的 persona
将数字 ID 替换为 Subject 名称，重新计算 embeddings
"""

import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import re

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel


def load_subject_mapping():
    """加载 SubjectId -> Name 的映射"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    subject_map = {}
    for _, row in df.iterrows():
        subject_id = str(row['SubjectId'])
        name = row['Name']
        subject_map[subject_id] = name
    
    print(f"✅ 加载了 {len(subject_map)} 个 Subject 映射")
    return subject_map


def replace_in_text(text, subject_map):
    """在文本中替换所有数字 ID 为 Subject 名称"""
    result = text
    # 按 ID 长度从长到短排序，避免替换冲突
    for subject_id in sorted(subject_map.keys(), key=lambda x: len(x), reverse=True):
        subject_name = subject_map[subject_id]
        # 只替换独立的数字（用单引号包围的或作为独立词）
        patterns = [
            f"'{subject_id}'",  # '204'
            f' {subject_id} ',  # 空格包围
            f'^{subject_id} ',  # 开头
            f' {subject_id}$',  # 结尾
        ]
        for pattern in patterns:
            result = result.replace(pattern.replace('^', '').replace('$', ''), 
                                   pattern.replace(subject_id, subject_name).replace('^', '').replace('$', ''))
    
    return result


def fix_persona_file(filepath, subject_map, bge_model):
    """
    修复单个 persona 文件：
    1. 替换 concept_text、description、keywords 中的数字 ID
    2. 重新计算 embeddings
    3. 保存到 .npz
    4. 保存更新后的 JSON（不含 embedding）
    """
    student_id = os.path.basename(filepath).replace('.json', '')
    
    try:
        # 读取 JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            personas = json.load(f)
        
        if not personas:
            return False
        
        # 替换文本
        updated = False
        for persona in personas:
            old_concept_text = persona.get('concept_text', '')
            old_description = persona.get('description', '')
            old_keywords = persona.get('keywords', '')
            
            # 如果 concept_text 是纯数字，替换为 Subject 名称
            if old_concept_text.strip().isdigit():
                new_concept_text = subject_map.get(old_concept_text.strip(), old_concept_text)
                persona['concept_text'] = new_concept_text
                updated = True
            else:
                new_concept_text = old_concept_text
            
            # 替换 description 中的数字 ID
            new_description = replace_in_text(old_description, subject_map)
            if new_description != old_description:
                persona['description'] = new_description
                updated = True
            
            # 更新 keywords（如果是数字）
            if old_keywords.strip().isdigit():
                persona['keywords'] = subject_map.get(old_keywords.strip(), old_keywords)
                updated = True
            elif old_keywords == old_concept_text and new_concept_text != old_concept_text:
                persona['keywords'] = new_concept_text
                updated = True
            
            # 删除 embedding 字段（如果存在）
            if 'embedding' in persona:
                del persona['embedding']
        
        # 保存更新后的 JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(personas, f, indent=2, ensure_ascii=False)
        
        # 重新计算并保存 embeddings
        descriptions = [p['description'] for p in personas]
        keywords_list = [p['keywords'] for p in personas]
        
        desc_embeddings = bge_model.encode(descriptions, batch_size=min(128, len(descriptions)))
        kw_embeddings = bge_model.encode(keywords_list, batch_size=min(128, len(keywords_list)))
        
        # 保存到 .npz
        emb_dir = '/mnt/localssd/bank/persona/nips_task34/embeddings'
        os.makedirs(emb_dir, exist_ok=True)
        
        np.savez_compressed(
            os.path.join(emb_dir, f'{student_id}_description.npz'),
            embeddings=np.array(desc_embeddings, dtype=np.float16)
        )
        np.savez_compressed(
            os.path.join(emb_dir, f'{student_id}_keywords.npz'),
            embeddings=np.array(kw_embeddings, dtype=np.float16)
        )
        
        return True
        
    except Exception as e:
        print(f"\n  ⚠️  处理失败 {filepath}: {e}")
        return False


def main():
    print("=" * 100)
    print("修复 NIPS_TASK34 Persona - 替换数字 ID 并重新计算 Embeddings")
    print("=" * 100)
    print()
    
    # 1. 加载 Subject 映射
    print("📂 加载 Subject 映射...")
    subject_map = load_subject_mapping()
    print()
    
    # 2. 加载 BGE 模型
    print("🤖 初始化 BGE 模型...")
    bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE 模型加载完成")
    print()
    
    # 3. 处理所有 persona 文件
    data_dir = '/mnt/localssd/bank/persona/nips_task34/data'
    files = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])
    
    print(f"📝 处理 {len(files)} 个 Persona 文件...")
    success_count = 0
    
    for filename in tqdm(files, desc="处理进度"):
        filepath = os.path.join(data_dir, filename)
        if fix_persona_file(filepath, subject_map, bge_model):
            success_count += 1
    
    print(f"\n✅ 成功处理 {success_count}/{len(files)} 个文件")
    print()
    
    # 4. 验证前几个学生
    print("🔍 验证前 5 个学生...")
    for sid in range(5):
        filepath = os.path.join(data_dir, f'{sid}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                personas = json.load(f)
            
            if personas:
                sample = personas[0]
                concept_text = sample.get('concept_text', '')
                is_numeric = concept_text.strip().isdigit()
                has_embedding = 'embedding' in sample
                
                print(f"  学生 {sid}: concept_text='{concept_text[:40]}...' "
                      f"[{'❌数字' if is_numeric else '✅文本'}] "
                      f"[{'❌有embedding' if has_embedding else '✅无embedding'}]")
    
    print()
    print("=" * 100)
    print("✅ 完成！")
    print("=" * 100)


if __name__ == '__main__':
    main()
