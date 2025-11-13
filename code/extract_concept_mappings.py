#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提取每个数据集的concept到文本的映射
"""

import pandas as pd
import json
import os

def extract_assist2017_mapping():
    """提取ASSISTments2017的skill映射"""
    print("提取ASSISTments2017 concept映射...")
    
    try:
        # 读取原始数据
        df = pd.read_csv('/mnt/localssd/pykt-toolkit/data/assist2017/anonymized_full_release_competition_dataset.csv')
        
        # 创建skill映射
        if 'skill' in df.columns:
            # skill列包含skill名称
            unique_skills = df['skill'].dropna().unique()
            # 创建一个临时映射（skill名称就是描述）
            mapping = {skill: skill for skill in unique_skills}
            print(f"  找到 {len(mapping)} 个skills")
            return mapping
        else:
            print(f"  列名: {df.columns.tolist()}")
            return {}
    except Exception as e:
        print(f"  失败: {e}")
        return {}

def extract_nips_mapping():
    """提取NIPS Task 3&4的subject映射"""
    print("提取NIPS Task 3&4 concept映射...")
    
    try:
        # 读取subject metadata
        df = pd.read_csv('/mnt/localssd/pykt-toolkit/data/nips_task34/metadata/subject_metadata.csv')
        
        # 只保留Level 3的subjects（这是数据集使用的）
        df_level3 = df[df['Level'] == 3]
        
        mapping = {}
        for _, row in df_level3.iterrows():
            if pd.notna(row['SubjectId']) and pd.notna(row['Name']):
                mapping[str(row['SubjectId'])] = row['Name']
        
        print(f"  找到 {len(mapping)} 个Level 3 subjects")
        return mapping
    except Exception as e:
        print(f"  失败: {e}")
        return {}

def extract_algebra2005_mapping():
    """提取Algebra2005的KC映射"""
    print("提取Algebra2005 concept映射...")
    
    try:
        # 读取原始数据
        df = pd.read_table('/mnt/localssd/pykt-toolkit/data/algebra2005/algebra_2005_2006_train.txt', 
                          low_memory=False, nrows=10000)
        
        # 检查KC列
        kc_cols = [col for col in df.columns if 'KC' in col or 'Skill' in col]
        print(f"  KC列: {kc_cols}")
        
        if 'KC(Default)' in df.columns:
            # 提取unique KCs
            unique_kcs = set()
            for val in df['KC(Default)'].dropna():
                # KC可能用~~分隔
                kcs = str(val).split('~~')
                unique_kcs.update(kcs)
            
            # 创建映射（KC文本就是描述）
            mapping = {kc.strip(): kc.strip() for kc in unique_kcs if kc.strip()}
            print(f"  找到 {len(mapping)} 个KCs")
            return mapping
        else:
            print(f"  未找到KC列")
            return {}
    except Exception as e:
        print(f"  失败: {e}")
        return {}

def extract_bridge2006_mapping():
    """提取Bridge2Algebra2006的KC映射"""
    print("提取Bridge2Algebra2006 concept映射...")
    
    try:
        df = pd.read_table('/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/bridge_to_algebra_2006_2007_train.txt',
                          low_memory=False, nrows=10000)
        
        kc_cols = [col for col in df.columns if 'KC' in col or 'Skill' in col]
        print(f"  KC列: {kc_cols}")
        
        if 'KC(SubSkills)' in df.columns:
            unique_kcs = set()
            for val in df['KC(SubSkills)'].dropna():
                kcs = str(val).split('~~')
                unique_kcs.update(kcs)
            
            mapping = {kc.strip(): kc.strip() for kc in unique_kcs if kc.strip()}
            print(f"  找到 {len(mapping)} 个KCs")
            return mapping
        else:
            print(f"  未找到KC列")
            return {}
    except Exception as e:
        print(f"  失败: {e}")
        return {}

def main():
    """主函数"""
    print("="*60)
    print("  提取Concept映射")
    print("="*60 + "\n")
    
    mappings = {
        'assist2017': extract_assist2017_mapping(),
        'nips_task34': extract_nips_mapping(),
        'algebra2005': extract_algebra2005_mapping(),
        'bridge2006': extract_bridge2006_mapping()
    }
    
    # 保存映射
    output_dir = '/mnt/localssd/bank/concept_mappings'
    os.makedirs(output_dir, exist_ok=True)
    
    for dataset, mapping in mappings.items():
        if mapping:
            output_file = f"{output_dir}/{dataset}_concept_mapping.json"
            with open(output_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            print(f"\n✅ {dataset}: {len(mapping)} concepts saved to {output_file}")
        else:
            print(f"\n❌ {dataset}: No mapping extracted")
    
    print("\n" + "="*60)
    print("  完成")
    print("="*60)

if __name__ == '__main__':
    main()

