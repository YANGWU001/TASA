#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新计算 embeddings
从现有 JSON 读取数据，计算 embeddings，保存到 .npz
"""

import os
import json
import numpy as np
from tqdm import tqdm
import argparse

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel


def load_bge_model():
    """加载 BGE 模型"""
    print("🤖 初始化BGE模型...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE模型加载完成")
    return model


def generate_embeddings_batch(texts, model):
    """批量生成embeddings（与create_student_bank_final.py保持一致）"""
    if not texts:
        return np.zeros((0, 1024), dtype=np.float16)
    
    try:
        # 确保所有文本都是字符串
        texts = [str(t) if t is not None else "" for t in texts]
        # 旧版FlagModel (v1.1.6) 的encode()方法不接受return_dense等参数
        # 直接调用encode会返回dense embeddings
        result = model.encode(texts, batch_size=min(32, len(texts)))
        
        # 确保返回的是numpy数组
        if isinstance(result, dict):
            # 如果返回的是字典，尝试获取'dense' embeddings
            result = result.get('dense', result.get('embeddings', result))
        
        # 转换为numpy数组并确保是float16类型
        result = np.array(result, dtype=np.float16)
        return result
    except Exception as e:
        print(f"  ⚠️  Embedding生成失败: {e}, 返回零向量")
        # 返回零向量作为fallback
        return np.zeros((len(texts), 1024), dtype=np.float16)


def process_file(filepath, data_type, dataset_name, bge_model):
    """
    处理单个文件：
    1. 读取 JSON
    2. 提取 description 和 keywords
    3. 生成 embeddings
    4. 保存到 .npz
    """
    student_id = os.path.basename(filepath).replace('.json', '')
    
    try:
        # 1. 读取 JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return False
        
        # 2. 提取文本（确保是字符串）
        descriptions = []
        keywords_list = []
        
        for item in data:
            desc = item.get('description', '')
            kw = item.get('keywords', item.get('concept_text', ''))
            
            # 确保是字符串
            descriptions.append(str(desc) if desc else '')
            keywords_list.append(str(kw) if kw else '')
        
        # 3. 生成 embeddings
        desc_embeddings = generate_embeddings_batch(descriptions, bge_model)
        kw_embeddings = generate_embeddings_batch(keywords_list, bge_model)
        
        if desc_embeddings is None or kw_embeddings is None:
            return False
        
        # 4. 保存到 .npz
        emb_dir = f'/mnt/localssd/bank/{data_type}/{dataset_name}/embeddings'
        os.makedirs(emb_dir, exist_ok=True)
        
        # 保存description embeddings
        desc_emb_file = os.path.join(emb_dir, f'{student_id}_description.npz')
        np.savez_compressed(desc_emb_file, embeddings=desc_embeddings)
        
        # 保存keywords embeddings  
        key_emb_file = os.path.join(emb_dir, f'{student_id}_keywords.npz')
        np.savez_compressed(key_emb_file, embeddings=kw_embeddings)
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  处理失败 {filepath}: {e}")
        return False


def process_dataset(dataset_name, data_type, bge_model):
    """处理整个数据集"""
    data_dir = f'/mnt/localssd/bank/{data_type}/{dataset_name}/data'
    
    if not os.path.exists(data_dir):
        print(f"  ⚠️  目录不存在: {data_dir}")
        return 0
    
    files = sorted([f for f in os.listdir(data_dir) if f.endswith('.json')])
    
    print(f"  处理 {len(files)} 个文件...")
    success_count = 0
    failed_count = 0
    
    for filename in tqdm(files, desc=f"{dataset_name} {data_type}"):
        filepath = os.path.join(data_dir, filename)
        if process_file(filepath, data_type, dataset_name, bge_model):
            success_count += 1
        else:
            failed_count += 1
    
    if failed_count > 0:
        print(f"  ⚠️  失败: {failed_count} 个文件")
    
    return success_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='nips_task34',
                       help='数据集名称')
    parser.add_argument('--type', type=str, choices=['memory', 'persona', 'both'],
                       default='both', help='处理类型')
    args = parser.parse_args()
    
    print("=" * 100)
    print(f"重新计算 Embeddings - {args.dataset}")
    print("=" * 100)
    print()
    
    # 加载 BGE 模型
    bge_model = load_bge_model()
    print()
    
    total_success = 0
    
    if args.type in ['persona', 'both']:
        print(f"👤 处理 Persona:")
        count = process_dataset(args.dataset, 'persona', bge_model)
        print(f"  ✅ 成功处理 {count} 个文件")
        total_success += count
        print()
    
    if args.type in ['memory', 'both']:
        print(f"📝 处理 Memory:")
        count = process_dataset(args.dataset, 'memory', bge_model)
        print(f"  ✅ 成功处理 {count} 个文件")
        total_success += count
        print()
    
    print("=" * 100)
    print(f"✅ 完成！总共处理了 {total_success} 个文件")
    print("=" * 100)


if __name__ == '__main__':
    main()
