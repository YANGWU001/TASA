#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取和展示数据集中的Concept描述信息
"""

import pandas as pd
import json
import os
from collections import Counter

def analyze_ednet_concepts(data_dir):
    """
    分析EdNet的concept信息
    """
    print(f"\n{'='*80}")
    print(f"📊 EdNet 数据集 - Concept分析")
    print(f"{'='*80}\n")
    
    # 读取keyid2idx.json
    keyid_path = os.path.join(data_dir, "keyid2idx.json")
    with open(keyid_path, 'r') as f:
        keyid2idx = json.load(f)
    
    concepts_map = keyid2idx.get('concepts', {})
    
    print(f"📋 Concept ID 映射:")
    print(f"  - 总Concept数: {len(concepts_map)}")
    
    # EdNet的concept是数字ID（表示知识点tag）
    # 原始EdNet数据没有提供concept的文字描述
    print(f"\n⚠️  **EdNet数据集的局限性**:")
    print(f"  - Concepts只是数字ID (如: 1, 2, 3...188)")
    print(f"  - 原始数据集**没有提供**concept的文字描述")
    print(f"  - 这些ID对应EdNet平台内部的知识点标签")
    print(f"  - 无法知道每个concept的具体含义（如 \"代数\"、\"几何\" 等）")
    
    # 展示部分concept ID
    sorted_concepts = sorted([(k, v) for k, v in concepts_map.items()], key=lambda x: x[1])
    print(f"\n  Concept ID 示例（原始标签 -> 索引）:")
    for orig_tag, idx in sorted_concepts[:20]:
        print(f"    - Tag {orig_tag} -> Index {idx}")
    
    print(f"\n💡 建议:")
    print(f"  - 可以联系EdNet数据集提供方获取标签描述")
    print(f"  - 或根据相关问题内容推断concept含义")
    print(f"  - 在研究中可以用\"Concept X\"来指代")
    
    return concepts_map


def analyze_assistments_concepts(data_dir):
    """
    分析ASSISTments2017的concept (skill) 信息
    """
    print(f"\n{'='*80}")
    print(f"📊 ASSISTments2017 数据集 - Concept (Skill) 分析")
    print(f"{'='*80}\n")
    
    # 读取原始数据
    raw_data_path = os.path.join(data_dir, "anonymized_full_release_competition_dataset.csv")
    print(f"📂 读取原始数据: {raw_data_path}")
    print(f"⏳ 正在加载（可能需要一些时间）...")
    
    df = pd.read_csv(raw_data_path)
    
    # 提取skill信息
    skills = df['skill'].dropna().unique()
    skill_counts = df['skill'].value_counts()
    
    print(f"\n✅ ASSISTments2017 **有完整的Skill文字描述**！")
    print(f"\n📋 Skill统计:")
    print(f"  - 总Skill数: {len(skills)}")
    print(f"  - 总交互数: {len(df):,}")
    
    # 读取keyid2idx.json查看映射
    keyid_path = os.path.join(data_dir, "keyid2idx.json")
    with open(keyid_path, 'r') as f:
        keyid2idx = json.load(f)
    
    concepts_map = keyid2idx.get('concepts', {})
    
    # 创建反向映射：索引 -> skill名称
    idx_to_skill = {v: k for k, v in concepts_map.items()}
    
    print(f"\n🔝 最常见的20个Skills（有文字描述）:")
    print(f"{'='*80}")
    for i, (skill, count) in enumerate(skill_counts.head(20).items(), 1):
        # 找到对应的索引
        idx = concepts_map.get(skill, '?')
        print(f"{i:2d}. [{idx:3}] {skill}")
        print(f"     出现次数: {count:,} ({count/len(df)*100:.2f}%)")
    
    print(f"\n📄 所有Skills列表（按索引排序）:")
    print(f"{'='*80}")
    sorted_skills = sorted([(idx, skill) for skill, idx in concepts_map.items()])
    for idx, skill in sorted_skills:
        count = skill_counts.get(skill, 0)
        print(f"  [{idx:3d}] {skill:50s} ({count:,} 次)")
    
    # 保存到文件
    output_path = "/tmp/assistments2017_skill_descriptions.txt"
    with open(output_path, 'w') as f:
        f.write("ASSISTments2017 Skills 描述列表\n")
        f.write("="*80 + "\n\n")
        for idx, skill in sorted_skills:
            count = skill_counts.get(skill, 0)
            f.write(f"[{idx:3d}] {skill:50s} ({count:,} 次)\n")
    
    print(f"\n✅ Skills描述已保存到: {output_path}")
    
    return concepts_map, idx_to_skill, skill_counts


def create_concept_mapping_summary(assistments_skills):
    """
    创建concept ID到描述的映射摘要
    """
    print(f"\n{'='*80}")
    print(f"📊 Concept描述可用性总结")
    print(f"{'='*80}\n")
    
    print("| 数据集 | Concept数量 | 有文字描述 | 描述类型 |")
    print("|--------|-------------|-----------|----------|")
    print("| EdNet | 188 | ❌ 否 | 仅数字ID (1-188) |")
    print(f"| ASSISTments2017 | {len(assistments_skills)} | ✅ 是 | 英文skill名称 |")
    
    print(f"\n💡 使用建议:")
    print(f"\n  **对于EdNet:**")
    print(f"  - Concept以数字ID表示，如 \"Concept 7\"、\"Concept 24\"")
    print(f"  - 可以通过分析高频concept对应的题目内容来推断含义")
    print(f"  - 在论文/报告中直接使用\"Concept X\"即可")
    
    print(f"\n  **对于ASSISTments2017:**")
    print(f"  - Concept有完整英文描述，如:")
    print(f"    • \"properties-of-geometric-figures\" (几何图形性质)")
    print(f"    • \"sum-of-interior-angles-more-than-3-sides\" (多边形内角和)")
    print(f"    • \"transformations-rotations\" (变换-旋转)")
    print(f"  - 预处理时会转换为数字索引")
    print(f"  - 可以通过keyid2idx.json查看映射关系")


if __name__ == "__main__":
    print("🔍 Concept描述信息提取")
    print("=" * 80)
    
    # 分析EdNet
    ednet_dir = "/mnt/localssd/pykt-toolkit/data/ednet"
    ednet_concepts = analyze_ednet_concepts(ednet_dir)
    
    # 分析ASSISTments2017
    assistments_dir = "/mnt/localssd/pykt-toolkit/data/assist2017"
    assistments_concepts, idx_to_skill, skill_counts = analyze_assistments_concepts(assistments_dir)
    
    # 创建总结
    create_concept_mapping_summary(assistments_concepts)
    
    print(f"\n{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}")

