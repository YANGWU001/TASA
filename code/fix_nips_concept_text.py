#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 nips_task34 数据集的 concept_text
将数字 ID 替换为实际的 subject 名称，并重新计算 embedding
"""

import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm
import torch
import argparse

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel


def load_subject_mapping():
    """加载 SubjectId -> Name 的映射"""
    metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
    df = pd.read_csv(metadata_file)
    
    # 创建 SubjectId -> Name 的映射
    subject_map = {}
    for _, row in df.iterrows():
        subject_id = str(row['SubjectId'])
        name = row['Name']
        subject_map[subject_id] = name
    
    print(f"✅ 加载了 {len(subject_map)} 个 Subject 映射")
    print(f"   示例: SubjectId 191 -> '{subject_map.get('191', 'NOT_FOUND')}'")
    
    return subject_map


def replace_concept_text_in_string(text, subject_map):
    """
    在字符串中替换 concept_text
    例如: "The student mastered the 191 task." -> "The student mastered the Percentages task."
    """
    result = text
    # 按照 SubjectId 从长到短排序，避免替换冲突（如先替换1，再替换191会有问题）
    for subject_id in sorted(subject_map.keys(), key=lambda x: len(x), reverse=True):
        subject_name = subject_map[subject_id]
        # 只替换独立的数字（前后是空格、标点或字符串边界）
        import re
        # 匹配独立的数字
        pattern = r'\b' + re.escape(subject_id) + r'\b'
        result = re.sub(pattern, subject_name, result)
    
    return result


def process_memory_file(student_file, subject_map, bge_model):
    """处理单个 memory 文件"""
    student_id = os.path.basename(student_file).replace('.json', '')
    
    with open(student_file, 'r', encoding='utf-8') as f:
        memories = json.load(f)
    
    if not memories:
        return 0
    
    json_updated = False
    need_recompute_embeddings = False
    
    for idx, memory in enumerate(memories):
        old_concept_text = memory['concept_text']
        old_description = memory['description']
        
        # 替换 concept_text（如果是纯数字）
        if old_concept_text.isdigit():
            new_concept_text = subject_map.get(old_concept_text, old_concept_text)
            if new_concept_text != old_concept_text:
                memory['concept_text'] = new_concept_text
                json_updated = True
                need_recompute_embeddings = True
        
        # 替换 description 中的数字
        new_description = replace_concept_text_in_string(old_description, subject_map)
        if new_description != old_description:
            memory['description'] = new_description
            json_updated = True
            need_recompute_embeddings = True
    
    # 保存更新后的 JSON 文件
    if json_updated:
        with open(student_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
    
    # 重新计算并保存 embeddings
    if need_recompute_embeddings:
        # 提取所有 descriptions 和 keywords
        descriptions = [m['description'] for m in memories]
        keywords = [m.get('keywords', m['concept_text']) for m in memories]
        
        # 生成 embeddings
        desc_embeddings = generate_embeddings_batch(descriptions, bge_model)
        kw_embeddings = generate_embeddings_batch(keywords, bge_model)
        
        # 保存到 embeddings/ 目录
        embeddings_dir = os.path.join(os.path.dirname(os.path.dirname(student_file)), 'embeddings')
        os.makedirs(embeddings_dir, exist_ok=True)
        
        # 保存为 npz 文件（使用 float16 格式节省空间）
        np.savez_compressed(
            os.path.join(embeddings_dir, f'{student_id}_description.npz'),
            embeddings=np.array(desc_embeddings, dtype=np.float16)
        )
        np.savez_compressed(
            os.path.join(embeddings_dir, f'{student_id}_keywords.npz'),
            embeddings=np.array(kw_embeddings, dtype=np.float16)
        )
        
        return len(memories)
    
    return 0


def process_persona_file(student_file, subject_map, bge_model):
    """处理单个 persona 文件"""
    student_id = os.path.basename(student_file).replace('.json', '')
    
    with open(student_file, 'r', encoding='utf-8') as f:
        personas = json.load(f)
    
    if not personas:
        return 0
    
    json_updated = False
    need_recompute_embeddings = False
    
    for idx, persona in enumerate(personas):
        old_concept_text = persona['concept_text']
        old_description = persona['description']
        
        # 替换 concept_text（如果是纯数字）
        if old_concept_text.isdigit():
            new_concept_text = subject_map.get(old_concept_text, old_concept_text)
            if new_concept_text != old_concept_text:
                persona['concept_text'] = new_concept_text
                # 也更新 keywords
                if persona.get('keywords') == old_concept_text:
                    persona['keywords'] = new_concept_text
                json_updated = True
                need_recompute_embeddings = True
        
        # 替换 description 中的数字
        new_description = replace_concept_text_in_string(old_description, subject_map)
        if new_description != old_description:
            persona['description'] = new_description
            json_updated = True
            need_recompute_embeddings = True
    
    # 保存更新后的 JSON 文件
    if json_updated:
        with open(student_file, 'w', encoding='utf-8') as f:
            json.dump(personas, f, indent=2, ensure_ascii=False)
    
    # 重新计算并保存 embeddings
    if need_recompute_embeddings:
        # 提取所有 descriptions 和 keywords
        descriptions = [p['description'] for p in personas]
        keywords = [p.get('keywords', p['concept_text']) for p in personas]
        
        # 生成 embeddings
        desc_embeddings = generate_embeddings_batch(descriptions, bge_model)
        kw_embeddings = generate_embeddings_batch(keywords, bge_model)
        
        # 保存到 embeddings/ 目录
        embeddings_dir = os.path.join(os.path.dirname(os.path.dirname(student_file)), 'embeddings')
        os.makedirs(embeddings_dir, exist_ok=True)
        
        # 保存为 npz 文件（使用 float16 格式节省空间）
        np.savez_compressed(
            os.path.join(embeddings_dir, f'{student_id}_description.npz'),
            embeddings=np.array(desc_embeddings, dtype=np.float16)
        )
        np.savez_compressed(
            os.path.join(embeddings_dir, f'{student_id}_keywords.npz'),
            embeddings=np.array(kw_embeddings, dtype=np.float16)
        )
        
        return len(personas)
    
    return 0


def generate_embeddings_batch(texts, model):
    """批量生成 embeddings"""
    if not texts:
        return []
    
    # 使用 BGE-M3 模型的 encode 方法
    embeddings = model.encode(texts, batch_size=min(128, len(texts)))
    return embeddings


def load_bge_model():
    """加载 BGE 模型"""
    print("🤖 初始化BGE模型...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE模型加载完成")
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, choices=['memory', 'persona', 'both'], default='both',
                       help='处理类型: memory, persona, 或 both')
    parser.add_argument('--test', action='store_true', help='测试模式（只处理前5个学生）')
    args = parser.parse_args()
    
    print("=" * 100)
    print("修复 NIPS_TASK34 Concept Text")
    print(f"处理类型: {args.type}")
    if args.test:
        print("⚠️  测试模式: 只处理前5个学生")
    print("=" * 100)
    print()
    
    # 1. 加载 Subject 映射
    subject_map = load_subject_mapping()
    print()
    
    # 2. 加载 BGE 模型
    bge_model = load_bge_model()
    print()
    
    # 3. 处理 Memory 文件
    if args.type in ['memory', 'both']:
        memory_dir = '/mnt/localssd/bank/memory/nips_task34/data'
        memory_files = sorted([f for f in os.listdir(memory_dir) if f.endswith('.json')])
        
        if args.test:
            memory_files = memory_files[:5]
        
        print(f"📝 处理 Memory 文件 (共{len(memory_files)}个)...")
        total_updated = 0
        for filename in tqdm(memory_files, desc="Memory"):
            filepath = os.path.join(memory_dir, filename)
            updated_count = process_memory_file(filepath, subject_map, bge_model)
            total_updated += updated_count
        
        print(f"  ✅ Memory 处理完成: 更新了 {total_updated} 条记录的 embedding")
        print()
    
    # 4. 处理 Persona 文件
    if args.type in ['persona', 'both']:
        persona_dir = '/mnt/localssd/bank/persona/nips_task34/data'
        persona_files = sorted([f for f in os.listdir(persona_dir) if f.endswith('.json')])
        
        if args.test:
            persona_files = persona_files[:5]
        
        print(f"👤 处理 Persona 文件 (共{len(persona_files)}个)...")
        total_updated = 0
        for filename in tqdm(persona_files, desc="Persona"):
            filepath = os.path.join(persona_dir, filename)
            updated_count = process_persona_file(filepath, subject_map, bge_model)
            total_updated += updated_count
        
        print(f"  ✅ Persona 处理完成: 更新了 {total_updated} 条记录的 embedding")
        print()
    
    print("=" * 100)
    print("✅ 完成！")
    print("=" * 100)


if __name__ == '__main__':
    main()

