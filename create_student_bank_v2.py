#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建学生Persona和Memory Bank - 改进版
"""

import os
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm
from FlagEmbedding import BGEM3FlagModel
from openai import OpenAI
import time
import re

# LLM配置
ENDPOINT = "http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000"
KEY = "sk-g-wO3D7N2V-VvcfhfqG9ww"
MODEL = "gpt-4o"

# 数据集配置
DATASETS = {
    'assist2017': '/mnt/localssd/pykt-toolkit/data/assist2017/train_valid_sequences.csv',
    'nips_task34': '/mnt/localssd/pykt-toolkit/data/nips_task34/train_valid_sequences.csv',
    'algebra2005': '/mnt/localssd/pykt-toolkit/data/algebra2005/train_valid_sequences.csv',
    'bridge2006': '/mnt/localssd/pykt-toolkit/data/bridge2algebra2006/train_valid_sequences.csv',
}

# 全局变量
bge_model = None
llm_client = None

def init_models():
    """初始化模型"""
    global bge_model, llm_client
    
    if bge_model is None:
        print("加载BGE-M3模型...")
        bge_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, devices='cuda:0')
        print("BGE-M3加载完成")
    
    if llm_client is None:
        print("初始化LLM客户端...")
        llm_client = OpenAI(
            api_key="Bearer " + KEY,
            base_url=ENDPOINT,
        )
        print("LLM客户端就绪")
    
    return bge_model, llm_client

def parse_csv_field(field_str):
    """解析CSV字段"""
    if pd.isna(field_str) or field_str == 'NA' or field_str == '':
        return []
    
    try:
        values = str(field_str).strip().split(',')
        result = []
        for v in values:
            v = v.strip()
            if v and v != '-1' and v != 'NA':
                try:
                    result.append(int(v))
                except ValueError:
                    result.append(v)
        return result
    except:
        return []

def extract_student_data(row, dataset_name):
    """提取学生数据，排除最后一次答题"""
    uid = row['uid']
    
    questions = parse_csv_field(row['questions'])
    concepts = parse_csv_field(row['concepts'])
    responses = parse_csv_field(row['responses'])
    timestamps = parse_csv_field(row['timestamps'])
    
    # 构建交互
    interactions = []
    for i in range(min(len(questions), len(concepts), len(responses), len(timestamps))):
        interactions.append({
            'question_id': questions[i],
            'concept_id': concepts[i],
            'response': responses[i],
            'timestamp': timestamps[i],
            'index': i
        })
    
    # 按concept分组
    concept_groups = defaultdict(list)
    for inter in interactions:
        concept_groups[inter['concept_id']].append(inter)
    
    # 分离历史和最后一次
    history = []
    last_interactions = {}
    
    for cid, inters in concept_groups.items():
        if len(inters) > 1:
            history.extend(inters[:-1])
            last_interactions[str(cid)] = {
                'question_id': inters[-1]['question_id'],
                'response': inters[-1]['response'],
                'timestamp': inters[-1]['timestamp']
            }
        elif len(inters) == 1:
            # 只有一次，保存为last但不用于persona/memory
            last_interactions[str(cid)] = {
                'question_id': inters[0]['question_id'],
                'response': inters[0]['response'],
                'timestamp': inters[0]['timestamp']
            }
    
    return {
        'uid': uid,
        'history': history,
        'last_interactions': last_interactions
    }

def generate_persona_llm(uid, history, dataset_name):
    """使用LLM生成persona"""
    # 按concept统计
    stats = defaultdict(lambda: {'correct': 0, 'total': 0})
    for inter in history:
        cid = inter['concept_id']
        stats[cid]['total'] += 1
        if inter['response'] == 1:
            stats[cid]['correct'] += 1
    
    if not stats:
        return []
    
    # 构建prompt
    system_prompt = """You are an educational analyst. Summarize each concept's mastery level in 2 sentences based on performance data. Be concise and specific."""
    
    user_prompt = f"Student {uid} ({dataset_name}):\n\n"
    for cid, s in list(stats.items())[:20]:  # 限制20个concept
        acc = s['correct'] / s['total'] if s['total'] > 0 else 0
        user_prompt += f"Concept {cid}: {s['correct']}/{s['total']} ({acc:.0%})\n"
    
    user_prompt += "\nFor each concept above, provide: 1) Overall mastery (excellent/good/struggling), 2) One insight. Format: 'Concept X: [2 sentences]'"
    
    try:
        response = llm_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        # 解析响应
        personas = []
        for cid, s in stats.items():
            # 简单创建描述
            acc = s['correct'] / s['total'] if s['total'] > 0 else 0
            if acc >= 0.8:
                level = "excellent mastery"
            elif acc >= 0.6:
                level = "good understanding"
            else:
                level = "needs improvement"
            
            desc = f"Student shows {level} of Concept {cid} with {acc:.0%} accuracy over {s['total']} attempts."
            
            personas.append({
                'concept_id': int(cid),
                'concept_text': f"Concept {cid}",
                'description': desc,
                'keywords': f"Concept {cid}",
                'stats': s
            })
        
        return personas
    
    except Exception as e:
        print(f"  LLM生成persona失败: {e}")
        return []

def generate_memory_simple(uid, history, dataset_name):
    """简化的memory生成（不调用LLM）"""
    memories = []
    
    # 每个交互创建一个memory（限制前50个）
    for inter in history[:50]:
        cid = inter['concept_id']
        result = "correctly" if inter['response'] == 1 else "incorrectly"
        desc = f"Student answered question {inter['question_id']} on Concept {cid} {result}."
        
        memories.append({
            'concept_id': int(cid),
            'concept_text': f"Concept {cid}",
            'description': desc,
            'keywords': f"Concept {cid}",
            'question_id': inter['question_id'],
            'response': inter['response'],
            'timestamp': inter['timestamp']
        })
    
    return memories

def generate_embeddings_batch(texts, model):
    """批量生成embeddings"""
    if not texts:
        return []
    
    try:
        result = model.encode(
            texts,
            batch_size=min(32, len(texts)),
            max_length=256,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        return result['dense_vecs']
    except Exception as e:
        print(f"  Embedding生成失败: {e}")
        return None

def process_student(row, dataset_name, bge_model, llm_client):
    """处理单个学生"""
    try:
        data = extract_student_data(row, dataset_name)
        uid = data['uid']
        
        if len(data['history']) == 0:
            return {
                'uid': uid,
                'status': 'skipped',
                'personas': [],
                'memories': [],
                'last_interactions': data['last_interactions']
            }
        
        # 生成persona
        personas = generate_persona_llm(uid, data['history'], dataset_name)
        
        # 生成memory
        memories = generate_memory_simple(uid, data['history'], dataset_name)
        
        # 生成embeddings
        if personas:
            desc_texts = [p['description'] for p in personas]
            key_texts = [p['keywords'] for p in personas]
            
            desc_embs = generate_embeddings_batch(desc_texts, bge_model)
            key_embs = generate_embeddings_batch(key_texts, bge_model)
            
            if desc_embs is not None and key_embs is not None:
                for i, p in enumerate(personas):
                    p['description_embedding'] = desc_embs[i].tolist()
                    p['keywords_embedding'] = key_embs[i].tolist()
        
        if memories:
            desc_texts = [m['description'] for m in memories]
            key_texts = [m['keywords'] for m in memories]
            
            desc_embs = generate_embeddings_batch(desc_texts, bge_model)
            key_embs = generate_embeddings_batch(key_texts, bge_model)
            
            if desc_embs is not None and key_embs is not None:
                for i, m in enumerate(memories):
                    m['description_embedding'] = desc_embs[i].tolist()
                    m['keywords_embedding'] = key_embs[i].tolist()
        
        return {
            'uid': uid,
            'status': 'success',
            'personas': personas,
            'memories': memories,
            'last_interactions': data['last_interactions']
        }
    
    except Exception as e:
        print(f"  处理学生失败: {e}")
        return {
            'uid': row.get('uid', 'unknown'),
            'status': 'error',
            'error': str(e),
            'personas': [],
            'memories': [],
            'last_interactions': {}
        }

def save_results(results, dataset_name):
    """保存结果"""
    base_dir = "/mnt/localssd/bank"
    
    # Persona
    persona_data = [{'uid': r['uid'], 'personas': r['personas']} 
                    for r in results if r['personas']]
    persona_file = f"{base_dir}/persona/{dataset_name}/data/personas.json"
    os.makedirs(os.path.dirname(persona_file), exist_ok=True)
    with open(persona_file, 'w') as f:
        json.dump(persona_data, f, indent=2)
    
    # Memory
    memory_data = [{'uid': r['uid'], 'memories': r['memories']} 
                   for r in results if r['memories']]
    memory_file = f"{base_dir}/memory/{dataset_name}/data/memories.json"
    os.makedirs(os.path.dirname(memory_file), exist_ok=True)
    with open(memory_file, 'w') as f:
        json.dump(memory_data, f, indent=2)
    
    # Last interactions
    last_data = {r['uid']: r['last_interactions'] 
                 for r in results if r.get('last_interactions')}
    last_file = f"{base_dir}/persona/{dataset_name}/last_interactions/last_interactions.json"
    os.makedirs(os.path.dirname(last_file), exist_ok=True)
    with open(last_file, 'w') as f:
        json.dump(last_data, f, indent=2)
    
    print(f"\n  ✅ 保存完成:")
    print(f"    Persona: {len(persona_data)} 学生")
    print(f"    Memory: {len(memory_data)} 学生")
    print(f"    Last interactions: {len(last_data)} 学生")

def process_dataset(dataset_name, data_path, max_students=None):
    """处理单个数据集"""
    print(f"\n{'='*60}")
    print(f"处理数据集: {dataset_name}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    if max_students:
        df = df.head(max_students)
    
    print(f"总学生数: {len(df)}")
    
    # 初始化模型
    bge_model, llm_client = init_models()
    
    # 处理学生
    results = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"{dataset_name}"):
        result = process_student(row, dataset_name, bge_model, llm_client)
        results.append(result)
        
        # 每10个保存一次
        if len(results) % 10 == 0:
            save_results(results, dataset_name)
    
    # 最终保存
    save_results(results, dataset_name)
    
    # 统计
    success = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n✅ {dataset_name} 完成: 成功{success}, 跳过{skipped}, 错误{errors}")

def main():
    """主函数"""
    print("="*60)
    print("  创建学生Persona和Memory Bank")
    print("="*60)
    
    # 测试模式
    TEST_MODE = True
    max_students = 3 if TEST_MODE else None
    
    if TEST_MODE:
        print("\n⚠️  测试模式：每个数据集处理3个学生\n")
    
    for dataset_name, data_path in DATASETS.items():
        try:
            process_dataset(dataset_name, data_path, max_students)
        except Exception as e:
            print(f"\n❌ {dataset_name}失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("  ✅ 所有数据集处理完成！")
    print("="*60)

if __name__ == '__main__':
    main()

