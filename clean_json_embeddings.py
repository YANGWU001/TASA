#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理 JSON 文件中错误添加的 embedding 字段
"""

import os
import json
from tqdm import tqdm

def clean_embeddings_from_json(file_path):
    """从 JSON 文件中删除 embedding 字段"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned = False
    for item in data:
        if 'embedding' in item:
            del item['embedding']
            cleaned = True
    
    if cleaned:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False

def main():
    print("=" * 100)
    print("清理 NIPS_TASK34 JSON 文件中的 embedding 字段")
    print("=" * 100)
    print()
    
    # 清理 Memory 文件
    memory_dir = '/mnt/localssd/bank/memory/nips_task34/data'
    memory_files = sorted([f for f in os.listdir(memory_dir) if f.endswith('.json')])
    
    print(f"📝 清理 Memory 文件 (共{len(memory_files)}个)...")
    cleaned_count = 0
    for filename in tqdm(memory_files, desc="Memory"):
        filepath = os.path.join(memory_dir, filename)
        if clean_embeddings_from_json(filepath):
            cleaned_count += 1
    print(f"  ✅ 清理了 {cleaned_count} 个 Memory 文件")
    print()
    
    # 清理 Persona 文件
    persona_dir = '/mnt/localssd/bank/persona/nips_task34/data'
    persona_files = sorted([f for f in os.listdir(persona_dir) if f.endswith('.json')])
    
    print(f"👤 清理 Persona 文件 (共{len(persona_files)}个)...")
    cleaned_count = 0
    for filename in tqdm(persona_files, desc="Persona"):
        filepath = os.path.join(persona_dir, filename)
        if clean_embeddings_from_json(filepath):
            cleaned_count += 1
    print(f"  ✅ 清理了 {cleaned_count} 个 Persona 文件")
    print()
    
    print("=" * 100)
    print("✅ 完成！")
    print("=" * 100)

if __name__ == '__main__':
    main()

