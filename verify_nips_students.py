#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 nips_task34 前6个学生的 persona 和 memory 匹配程度
"""

import json
import os
from collections import Counter

def check_student(student_id, dataset='nips_task34'):
    """检查单个学生的 persona 和 memory"""
    base_dir = '/mnt/localssd/bank'
    
    # 读取 persona
    persona_file = f"{base_dir}/persona/{dataset}/data/{student_id}.json"
    if not os.path.exists(persona_file):
        return None, None, f"Persona 文件不存在"
    
    with open(persona_file, 'r', encoding='utf-8') as f:
        personas = json.load(f)
    
    # 读取 memory
    memory_file = f"{base_dir}/memory/{dataset}/data/{student_id}.json"
    if not os.path.exists(memory_file):
        return None, None, f"Memory 文件不存在"
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        memories = json.load(f)
    
    # 提取 concepts
    persona_concepts = set()
    persona_concept_texts = {}
    for p in personas:
        cid = p.get('concept_id')
        ctext = p.get('concept_text', '')
        persona_concepts.add(cid)
        persona_concept_texts[cid] = ctext
    
    memory_concepts = set()
    memory_concept_texts = {}
    for m in memories:
        cid = m.get('concept_id')
        ctext = m.get('concept_text', '')
        memory_concepts.add(cid)
        memory_concept_texts[cid] = ctext
    
    # 统计
    only_in_persona = persona_concepts - memory_concepts
    only_in_memory = memory_concepts - persona_concepts
    in_both = persona_concepts & memory_concepts
    
    # 检查 concept_text 是否是数字
    has_numeric_text = False
    numeric_concepts = []
    for cid, ctext in {**persona_concept_texts, **memory_concept_texts}.items():
        if ctext and ctext.strip().isdigit():
            has_numeric_text = True
            numeric_concepts.append((cid, ctext))
    
    return {
        'student_id': student_id,
        'persona_count': len(persona_concepts),
        'memory_count': len(memory_concepts),
        'both_count': len(in_both),
        'only_persona': len(only_in_persona),
        'only_memory': len(only_in_memory),
        'match_rate': len(in_both) / len(persona_concepts) if persona_concepts else 0,
        'persona_concepts': sorted(list(persona_concepts)),
        'memory_concepts': sorted(list(memory_concepts)),
        'only_in_persona': sorted(list(only_in_persona)),
        'only_in_memory': sorted(list(only_in_memory)),
        'persona_texts': persona_concept_texts,
        'memory_texts': memory_concept_texts,
        'has_numeric_text': has_numeric_text,
        'numeric_concepts': numeric_concepts,
        'persona_records': len(personas),
        'memory_records': len(memories)
    }, personas, memories

def main():
    print("=" * 100)
    print("验证 NIPS_TASK34 学生 0-5 的 Persona 和 Memory 匹配程度")
    print("=" * 100)
    print()
    
    for student_id in range(6):
        print(f"\n{'=' * 100}")
        print(f"学生 {student_id}")
        print(f"{'=' * 100}")
        
        result, personas, memories = check_student(student_id)
        
        if result is None:
            print(f"  ⚠️  {memories}")
            continue
        
        # 基本统计
        print(f"\n📊 基本统计:")
        print(f"  Persona: {result['persona_count']} 个 concepts, {result['persona_records']} 条记录")
        print(f"  Memory:  {result['memory_count']} 个 concepts, {result['memory_records']} 条记录")
        print(f"  匹配:    {result['both_count']} 个 concepts")
        print(f"  匹配率:  {result['match_rate']:.1%}")
        
        # 不匹配的 concepts
        if result['only_persona']:
            print(f"\n  ⚠️  只在 Persona 中: {result['only_persona']}")
            for cid in result['only_persona'][:3]:
                print(f"      Concept {cid}: '{result['persona_texts'].get(cid, 'N/A')}'")
        
        if result['only_memory']:
            print(f"\n  ⚠️  只在 Memory 中: {result['only_memory']}")
            for cid in result['only_memory'][:3]:
                print(f"      Concept {cid}: '{result['memory_texts'].get(cid, 'N/A')}'")
        
        # 检查是否有数字格式的 concept_text
        if result['has_numeric_text']:
            print(f"\n  ⚠️  发现数字格式的 concept_text:")
            for cid, ctext in result['numeric_concepts'][:5]:
                print(f"      Concept {cid}: '{ctext}'")
        
        # 显示一些样例数据
        print(f"\n📝 样例数据:")
        if personas:
            p = personas[0]
            print(f"  Persona 示例:")
            print(f"    concept_id: {p.get('concept_id')}")
            print(f"    concept_text: {p.get('concept_text', '')[:60]}...")
            print(f"    description: {p.get('description', '')[:80]}...")
        
        if memories:
            m = memories[0]
            print(f"  Memory 示例:")
            print(f"    concept_id: {m.get('concept_id')}")
            print(f"    concept_text: {m.get('concept_text', '')[:60]}...")
            print(f"    description: {m.get('description', '')[:80]}...")
        
        # 总结
        if result['match_rate'] == 1.0:
            print(f"\n  ✅ 完全匹配！")
        elif result['match_rate'] >= 0.9:
            print(f"\n  ⚠️  基本匹配，有少量差异")
        else:
            print(f"\n  ❌ 匹配度较低，需要检查")
    
    print(f"\n{'=' * 100}")
    print("✅ 检查完成")
    print(f"{'=' * 100}")

if __name__ == '__main__':
    main()

