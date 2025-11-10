#!/usr/bin/env python
"""
验证Memory和Persona的concept一致性
检查每个数据集的前N个学生
"""

import os
import json
from collections import defaultdict

DATASETS = ['assist2017', 'nips_task34', 'algebra2005', 'bridge2006']

def check_student(dataset, uid):
    """检查单个学生的Memory和Persona是否一致"""
    persona_file = f'/mnt/localssd/bank/persona/{dataset}/data/{uid}.json'
    memory_file = f'/mnt/localssd/bank/memory/{dataset}/data/{uid}.json'
    
    # 检查文件是否存在
    if not os.path.exists(persona_file):
        return {'status': 'persona_missing', 'persona_concepts': 0, 'memory_concepts': 0}
    
    if not os.path.exists(memory_file):
        return {'status': 'memory_missing', 'persona_concepts': 0, 'memory_concepts': 0}
    
    # 读取Persona
    try:
        with open(persona_file) as f:
            persona = json.load(f)
        persona_concepts = set(p['concept_id'] for p in persona)
    except Exception as e:
        return {'status': 'persona_error', 'error': str(e), 'persona_concepts': 0, 'memory_concepts': 0}
    
    # 读取Memory
    try:
        with open(memory_file) as f:
            memory = json.load(f)
        memory_concepts = set(m['concept_id'] for m in memory)
    except Exception as e:
        return {'status': 'memory_error', 'error': str(e), 'persona_concepts': len(persona_concepts), 'memory_concepts': 0}
    
    # 对比
    match = persona_concepts == memory_concepts
    
    return {
        'status': 'match' if match else 'mismatch',
        'persona_concepts': len(persona_concepts),
        'memory_concepts': len(memory_concepts),
        'memory_records': len(memory),
        'match': match,
        'only_in_persona': len(persona_concepts - memory_concepts),
        'only_in_memory': len(memory_concepts - persona_concepts)
    }

def verify_dataset(dataset, max_students=100):
    """验证数据集的前N个学生"""
    print(f"\n{'='*80}")
    print(f"验证 {dataset.upper()}")
    print(f"{'='*80}\n")
    
    # 获取所有学生ID
    persona_dir = f'/mnt/localssd/bank/persona/{dataset}/data'
    if not os.path.exists(persona_dir):
        print(f"❌ Persona目录不存在: {persona_dir}")
        return
    
    # 获取前N个学生（按文件名排序）
    all_files = sorted([f.replace('.json', '') for f in os.listdir(persona_dir) if f.endswith('.json')])
    student_ids = all_files[:max_students]
    
    if len(student_ids) == 0:
        print(f"❌ 没有找到学生数据")
        return
    
    print(f"检查前 {len(student_ids)} 个学生...")
    print()
    
    # 统计
    stats = {
        'match': 0,
        'mismatch': 0,
        'persona_missing': 0,
        'memory_missing': 0,
        'persona_error': 0,
        'memory_error': 0
    }
    
    mismatch_details = []
    
    # 检查每个学生
    for uid in student_ids:
        result = check_student(dataset, uid)
        stats[result['status']] += 1
        
        if result['status'] == 'mismatch':
            mismatch_details.append({
                'uid': uid,
                'persona_concepts': result['persona_concepts'],
                'memory_concepts': result['memory_concepts'],
                'only_in_persona': result['only_in_persona'],
                'only_in_memory': result['only_in_memory']
            })
    
    # 输出结果
    print("📊 验证结果:")
    print(f"  ✅ 完全匹配: {stats['match']}/{len(student_ids)} ({stats['match']/len(student_ids)*100:.1f}%)")
    
    if stats['mismatch'] > 0:
        print(f"  ❌ 不匹配: {stats['mismatch']}")
    
    if stats['memory_missing'] > 0:
        print(f"  ⚠️  Memory文件缺失: {stats['memory_missing']}")
    
    if stats['persona_missing'] > 0:
        print(f"  ⚠️  Persona文件缺失: {stats['persona_missing']}")
    
    if stats['persona_error'] > 0 or stats['memory_error'] > 0:
        print(f"  ⚠️  读取错误: Persona={stats['persona_error']}, Memory={stats['memory_error']}")
    
    # 显示不匹配的详情（前5个）
    if mismatch_details:
        print(f"\n  不匹配详情（前5个）:")
        for detail in mismatch_details[:5]:
            print(f"    学生{detail['uid']}: Persona={detail['persona_concepts']}个concept, "
                  f"Memory={detail['memory_concepts']}个concept "
                  f"(只在Persona: {detail['only_in_persona']}, 只在Memory: {detail['only_in_memory']})")
    
    print()
    return stats

def main():
    print("="*80)
    print("验证Memory和Persona的Concept一致性")
    print("检查每个数据集的前100个学生")
    print("="*80)
    
    all_stats = {}
    
    for dataset in DATASETS:
        stats = verify_dataset(dataset, max_students=100)
        if stats:
            all_stats[dataset] = stats
    
    # 总结
    print("\n" + "="*80)
    print("📊 总体统计")
    print("="*80)
    print()
    
    for dataset, stats in all_stats.items():
        total = sum(stats.values())
        match_rate = stats['match'] / total * 100 if total > 0 else 0
        print(f"  {dataset:15} : {stats['match']}/{total} 匹配 ({match_rate:.1f}%)")
    
    print()
    print("="*80)
    print("✅ 验证完成！")
    print("="*80)

if __name__ == '__main__':
    main()

