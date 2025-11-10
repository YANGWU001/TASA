#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 JSON 文件中删除 embedding 字段
保持其他数据不变，只删除 embedding
"""

import os
import json
from tqdm import tqdm
import argparse


def clean_file(filepath):
    """从单个 JSON 文件中删除 embedding 字段"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return False
        
        cleaned = False
        for item in data:
            if 'embedding' in item:
                del item['embedding']
                cleaned = True
        
        if cleaned:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        
        return False
    except Exception as e:
        print(f"  ⚠️  错误处理 {filepath}: {e}")
        return False


def clean_dataset(dataset_name, data_type):
    """清理一个数据集的 persona 或 memory"""
    data_dir = f'/mnt/localssd/bank/{data_type}/{dataset_name}/data'
    
    if not os.path.exists(data_dir):
        print(f"  ⚠️  目录不存在: {data_dir}")
        return 0
    
    files = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])
    
    print(f"  处理 {len(files)} 个文件...")
    cleaned_count = 0
    
    for filename in tqdm(files, desc=f"{dataset_name} {data_type}"):
        filepath = os.path.join(data_dir, filename)
        if clean_file(filepath):
            cleaned_count += 1
    
    return cleaned_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='nips_task34',
                       help='数据集名称')
    parser.add_argument('--type', type=str, choices=['memory', 'persona', 'both'], 
                       default='both', help='清理类型')
    args = parser.parse_args()
    
    print("=" * 100)
    print(f"清理 JSON 文件中的 embedding 字段 - {args.dataset}")
    print("=" * 100)
    print()
    
    total_cleaned = 0
    
    if args.type in ['memory', 'both']:
        print(f"📝 清理 Memory 文件:")
        count = clean_dataset(args.dataset, 'memory')
        print(f"  ✅ 清理了 {count} 个文件")
        total_cleaned += count
        print()
    
    if args.type in ['persona', 'both']:
        print(f"👤 清理 Persona 文件:")
        count = clean_dataset(args.dataset, 'persona')
        print(f"  ✅ 清理了 {count} 个文件")
        total_cleaned += count
        print()
    
    print("=" * 100)
    print(f"✅ 完成！总共清理了 {total_cleaned} 个文件")
    print("=" * 100)


if __name__ == '__main__':
    main()

