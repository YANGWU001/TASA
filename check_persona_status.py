#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 persona 处理状态"""

import os
import json

data_dir = '/mnt/localssd/bank/persona/nips_task34/data'
emb_dir = '/mnt/localssd/bank/persona/nips_task34/embeddings'

print("=" * 100)
print("检查 NIPS_TASK34 Persona 处理状态")
print("=" * 100)
print()

# 统计
total = 0
correct = 0
has_numbers = 0
has_embedding = 0

# 采样检查
sample_ids = list(range(20)) + [100, 200, 500, 1000, 2000, 4000]

for student_id in sample_ids:
    filepath = os.path.join(data_dir, f'{student_id}.json')
    if not os.path.exists(filepath):
        continue
    
    total += 1
    
    with open(filepath, 'r') as f:
        personas = json.load(f)
    
    if not personas:
        continue
    
    # 检查第一个 persona
    first = personas[0]
    concept_text = first.get('concept_text', '')
    
    # 检查是否是数字
    is_numeric = concept_text.strip().isdigit()
    
    # 检查是否有 embedding 字段
    has_emb = 'embedding' in first
    
    # 检查 embeddings 文件是否存在
    desc_emb_file = os.path.join(emb_dir, f'{student_id}_description.npz')
    kw_emb_file = os.path.join(emb_dir, f'{student_id}_keywords.npz')
    emb_files_exist = os.path.exists(desc_emb_file) and os.path.exists(kw_emb_file)
    
    status = "✅" if not is_numeric and not has_emb and emb_files_exist else "❌"
    
    if not is_numeric:
        correct += 1
    if is_numeric:
        has_numbers += 1
    if has_emb:
        has_embedding += 1
    
    if student_id < 10 or is_numeric or has_emb:
        print(f"学生 {student_id:4d}: {status}")
        print(f"  concept_text: '{concept_text[:50]}...'")
        print(f"  是否数字: {'是' if is_numeric else '否'}")
        print(f"  有embedding字段: {'是' if has_emb else '否'}")
        print(f"  .npz文件存在: {'是' if emb_files_exist else '否'}")
        print()

print("=" * 100)
print(f"统计 (采样 {total} 个学生):")
print(f"  ✅ 已正确处理: {correct} ({correct/total*100:.1f}%)")
print(f"  ❌ 仍是数字ID: {has_numbers} ({has_numbers/total*100:.1f}%)")
print(f"  ⚠️  有embedding字段: {has_embedding} ({has_embedding/total*100:.1f}%)")
print("=" * 100)

if has_numbers > 0:
    print()
    print("⚠️  发现未处理的 persona！")
    print("   运行以下命令来修复所有 persona:")
    print("   bash /mnt/localssd/run_fix_persona.sh")


