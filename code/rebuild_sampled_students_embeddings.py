#!/usr/bin/env python3
"""
只为采样的10个学生重建memory embeddings
"""
import os
import json
import numpy as np
from tqdm import tqdm

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    from FlagEmbedding import FlagModel as BGEM3FlagModel


DATASETS = ['assist2017', 'algebra2005', 'bridge2006', 'nips_task34']


def load_bge_model():
    """加载 BGE 模型"""
    print("🤖 初始化BGE模型...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE模型加载完成")
    return model


def load_sampled_students(dataset):
    """加载采样的学生ID列表"""
    sample_file = f'/mnt/localssd/qualified_students_{dataset}_sampled10.json'
    
    try:
        with open(sample_file, 'r') as f:
            data = json.load(f)
            return data.get('sampled_students', [])
    except Exception as e:
        print(f"  ⚠️  加载采样学生失败 ({dataset}): {e}")
        return []


def generate_embeddings_batch(texts, model):
    """批量生成embeddings（与create_student_bank_final.py保持一致）"""
    if not texts:
        return []
    
    try:
        # 确保所有文本都是字符串
        texts = [str(t) if t is not None else "" for t in texts]
        # 旧版FlagModel (v1.1.6) 的encode()方法不接受return_dense等参数
        # 直接调用encode会返回dense embeddings
        result = model.encode(texts, batch_size=min(32, len(texts)))
        return result
    except Exception as e:
        print(f"  ⚠️  Embedding生成失败: {e}")
        return None


def process_student(student_id, dataset_name, bge_model):
    """处理单个学生的memory embeddings"""
    # 读取memory JSON文件
    memory_file = f'/mnt/localssd/bank/memory/{dataset_name}/data/{student_id}.json'
    
    if not os.path.exists(memory_file):
        return False, f"文件不存在"
    
    try:
        # 1. 读取 JSON
        with open(memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return False, "空数据"
        
        # 2. 提取文本（确保是字符串）
        descriptions = []
        keywords_list = []
        
        for item in data:
            desc = item.get('description', '')
            kw = item.get('keywords', item.get('concept_text', ''))
            
            # 确保是字符串
            descriptions.append(str(desc) if desc else '')
            keywords_list.append(str(kw) if kw else '')
        
        # 3. 生成 embeddings（已经返回float16的numpy数组）
        desc_embeddings = generate_embeddings_batch(descriptions, bge_model)
        kw_embeddings = generate_embeddings_batch(keywords_list, bge_model)
        
        if desc_embeddings is None or kw_embeddings is None:
            return False, "Embedding生成失败"
        
        # 4. 保存到 .npz
        emb_dir = f'/mnt/localssd/bank/memory/{dataset_name}/embeddings'
        os.makedirs(emb_dir, exist_ok=True)
        
        # 保存description embeddings
        desc_emb_file = os.path.join(emb_dir, f'{student_id}_description.npz')
        np.savez_compressed(desc_emb_file, embeddings=desc_embeddings)
        
        # 保存keywords embeddings  
        key_emb_file = os.path.join(emb_dir, f'{student_id}_keywords.npz')
        np.savez_compressed(key_emb_file, embeddings=kw_embeddings)
        
        return True, "成功"
        
    except Exception as e:
        return False, str(e)


def process_dataset(dataset_name, sampled_students, bge_model):
    """处理单个数据集的采样学生"""
    print(f"\n📊 {dataset_name}:")
    print(f"  采样学生数: {len(sampled_students)}")
    
    success_count = 0
    failed_list = []
    
    for student_id in tqdm(sampled_students, desc=f"  处理"):
        success, msg = process_student(student_id, dataset_name, bge_model)
        if success:
            success_count += 1
        else:
            failed_list.append((student_id, msg))
    
    print(f"  ✅ 成功: {success_count}/{len(sampled_students)}")
    
    if failed_list:
        print(f"  ⚠️  失败: {len(failed_list)}")
        for sid, msg in failed_list[:5]:  # 只显示前5个
            print(f"     - Student {sid}: {msg}")
    
    return success_count


def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║          🔄 为采样学生重建Memory Embeddings (BGE-M3)                       ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 加载 BGE 模型
    bge_model = load_bge_model()
    print()
    
    total_students = 0
    total_success = 0
    
    for dataset in DATASETS:
        # 加载采样学生列表
        sampled_students = load_sampled_students(dataset)
        
        if not sampled_students:
            print(f"\n⚠️  {dataset}: 未找到采样学生")
            continue
        
        total_students += len(sampled_students)
        
        # 处理该数据集
        success_count = process_dataset(dataset, sampled_students, bge_model)
        total_success += success_count
    
    print("\n" + "="*100)
    print("📊 最终统计")
    print("="*100)
    print(f"✅ 成功: {total_success}/{total_students}")
    print(f"📦 4个数据集，每个10个学生")
    print("="*100)


if __name__ == '__main__':
    main()

