#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 nips_task34 persona 的 concept_text
将数字 ID 替换为实际的 Subject 名称，重新计算 embeddings
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


def replace_text(text, subject_map):
    """在文本中替换数字 ID 为名称"""
    result = text
    # 按照 ID 从长到短排序，避免替换冲突
    for subject_id in sorted(subject_map.keys(), key=lambda x: len(x), reverse=True):
        subject_name = subject_map[subject_id]
        # 匹配独立的数字（用引号包围或作为独立单词）
        pattern = r"'" + re.escape(subject_id) + r"'"
        result = re.sub(pattern, f"'{subject_name}'", result)
    
    return result


def process_student(student_id, subject_map, bge_model):
    """处理单个学生的 persona"""
    persona_file = f'/mnt/localssd/bank/persona/nips_task34/data/{student_id}.json'
    
    if not os.path.exists(persona_file):
        return False
    
    try:
        # 1. 读取 JSON
        with open(persona_file, 'r', encoding='utf-8') as f:
            personas = json.load(f)
        
        if not personas:
            return False
        
        # 2. 替换 concept_text, description, keywords
        updated = False
        for persona in personas:
            old_concept_text = persona.get('concept_text', '')
            
            # 如果是纯数字，替换为名称
            if old_concept_text.strip().isdigit():
                new_concept_text = subject_map.get(old_concept_text.strip(), old_concept_text)
                if new_concept_text != old_concept_text:
                    persona['concept_text'] = new_concept_text
                    persona['keywords'] = new_concept_text
                    updated = True
            
            # 替换 description 中的数字
            old_description = persona.get('description', '')
            new_description = replace_text(old_description, subject_map)
            if new_description != old_description:
                persona['description'] = new_description
                updated = True
            
            # 删除 embedding 字段（如果存在）
            if 'embedding' in persona:
                del persona['embedding']
                updated = True
        
        # 3. 保存更新后的 JSON
        if updated:
            with open(persona_file, 'w', encoding='utf-8') as f:
                json.dump(personas, f, indent=2, ensure_ascii=False)
        
        # 4. 重新计算 embeddings
        descriptions = [p['description'] for p in personas]
        keywords_list = [p['keywords'] for p in personas]
        
        desc_result = bge_model.encode(descriptions, batch_size=min(128, len(descriptions)))
        kw_result = bge_model.encode(keywords_list, batch_size=min(128, len(keywords_list)))
        
        # BGE-M3 返回字典，提取 dense_vecs
        if isinstance(desc_result, dict):
            desc_embeddings = desc_result['dense_vecs']
            kw_embeddings = kw_result['dense_vecs']
        else:
            desc_embeddings = desc_result
            kw_embeddings = kw_result
        
        # 5. 保存到 .npz
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
        print(f"  ⚠️  学生 {student_id} 处理失败: {e}")
        return False


def main():
    print("=" * 100)
    print("修复 NIPS_TASK34 Persona Concept Text 并重新计算 Embeddings")
    print("=" * 100)
    print()
    
    # 1. 加载 Subject 映射
    print("📋 加载 Subject 映射...")
    subject_map = load_subject_mapping()
    print()
    
    # 2. 加载 BGE 模型
    print("🤖 初始化 BGE 模型...")
    bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE 模型加载完成")
    print()
    
    # 3. 获取所有学生文件
    data_dir = '/mnt/localssd/bank/persona/nips_task34/data'
    files = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])
    student_ids = [f.replace('.json', '') for f in files]
    
    print(f"📝 处理 {len(student_ids)} 个学生的 Persona...")
    print()
    
    # 4. 处理所有学生
    success_count = 0
    for student_id in tqdm(student_ids, desc="处理进度"):
        if process_student(student_id, subject_map, bge_model):
            success_count += 1
    
    print()
    print("=" * 100)
    print(f"✅ 完成！成功处理 {success_count}/{len(student_ids)} 个学生")
    print("=" * 100)
    print()
    print("📊 处理结果:")
    print("  - concept_text: 数字 ID → Subject 名称")
    print("  - description: 替换其中的数字 ID")
    print("  - keywords: 更新为新的 concept_text")
    print("  - embeddings: 保存到 .npz 文件")
    print("  - JSON: 不包含 embedding 字段")


if __name__ == '__main__':
    main()
