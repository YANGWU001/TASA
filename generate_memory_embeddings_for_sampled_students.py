#!/usr/bin/env python3
"""
按照persona的方式为采样的10个学生生成memory embeddings
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

# 从评估结果中提取的学生列表
SAMPLED_STUDENTS = {
    'algebra2005': [48, 52, 109, 120, 300, 309, 370, 457, 504, 565],
    'assist2017': [119, 170, 183, 304, 307, 491, 570, 774, 1093, 1098],
    'bridge2006': [73, 360, 519, 613, 799, 834, 842, 843, 871, 1053],
    'nips_task34': [109, 137, 598, 1293, 1420, 2010, 2114, 2173, 2641, 2642]
}


def load_bge_model():
    """加载 BGE 模型"""
    print("🤖 初始化BGE模型...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("  ✅ BGE模型加载完成")
    return model


def process_student(student_id, dataset_name, bge_model):
    """处理单个学生的memory embeddings（参考persona的方式）"""
    # 读取memory JSON文件
    memory_file = f'/mnt/localssd/bank/memory/{dataset_name}/data/{student_id}.json'
    
    if not os.path.exists(memory_file):
        return False, f"文件不存在"
    
    try:
        # 1. 读取 JSON
        with open(memory_file, 'r', encoding='utf-8') as f:
            memories = json.load(f)
        
        if not memories:
            return False, "空数据"
        
        # 2. 提取文本（确保是字符串）
        descriptions = []
        keywords_list = []
        
        for item in memories:
            desc = item.get('description', '')
            kw = item.get('keywords', item.get('concept_text', ''))
            
            descriptions.append(str(desc) if desc else '')
            keywords_list.append(str(kw) if kw else '')
        
        # 3. 生成 embeddings（完全按照persona的方式）
        desc_result = bge_model.encode(descriptions, batch_size=min(128, len(descriptions)))
        kw_result = bge_model.encode(keywords_list, batch_size=min(128, len(keywords_list)))
        
        # BGE-M3返回字典，需要提取dense embeddings
        if isinstance(desc_result, dict):
            desc_embeddings = desc_result['dense_vecs']
            kw_embeddings = kw_result['dense_vecs']
        else:
            desc_embeddings = desc_result
            kw_embeddings = kw_result
        
        # 4. 保存到 .npz（完全按照persona的方式，使用 np.array + dtype=np.float16）
        emb_dir = f'/mnt/localssd/bank/memory/{dataset_name}/embeddings'
        os.makedirs(emb_dir, exist_ok=True)
        
        # 保存description embeddings
        np.savez_compressed(
            os.path.join(emb_dir, f'{student_id}_description.npz'),
            embeddings=np.array(desc_embeddings, dtype=np.float16)
        )
        
        # 保存keywords embeddings  
        np.savez_compressed(
            os.path.join(emb_dir, f'{student_id}_keywords.npz'),
            embeddings=np.array(kw_embeddings, dtype=np.float16)
        )
        
        return True, f"成功 (shape: {desc_embeddings.shape})"
        
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
    print("║        🔄 为采样学生生成Memory Embeddings (参考Persona方式)                ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 加载 BGE 模型
    bge_model = load_bge_model()
    print()
    
    total_students = 0
    total_success = 0
    
    for dataset in DATASETS:
        sampled_students = SAMPLED_STUDENTS.get(dataset, [])
        
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
    print(f"📦 4个数据集，每个约10个学生")
    print("="*100)


if __name__ == '__main__':
    main()

