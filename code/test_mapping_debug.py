#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 subject 映射加载"""

import pandas as pd
import json

# 1. 加载映射
metadata_file = '/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv'
df = pd.read_csv(metadata_file)

subject_map = {}
for _, row in df.iterrows():
    subject_id = str(row['SubjectId'])
    name = row['Name']
    subject_map[subject_id] = name

print(f"加载了 {len(subject_map)} 个映射")
print(f"\n测试几个 ID:")
test_ids = ['211', '219', '220', '204', '67']
for test_id in test_ids:
    print(f"  {test_id} -> {subject_map.get(test_id, 'NOT FOUND')}")

# 2. 读取一个 persona 文件测试
print(f"\n\n读取 540.json:")
with open('/mnt/localssd/bank/persona/nips_task34/data/540.json', 'r') as f:
    personas = json.load(f)

print(f"学生 540 有 {len(personas)} 个 concept")
for i, p in enumerate(personas[:3]):
    concept_text = p.get('concept_text', '')
    print(f"\n  Concept {i+1}:")
    print(f"    concept_text = '{concept_text}'")
    print(f"    type = {type(concept_text)}")
    print(f"    isdigit() = {concept_text.strip().isdigit()}")
    print(f"    映射结果 = {subject_map.get(concept_text.strip(), 'NOT FOUND')}")


